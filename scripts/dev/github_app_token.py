#!/usr/bin/env python3
"""GitHub App Installation tokenをローカル設定とmacOS Keychainから発行する。"""

from __future__ import annotations

import argparse
import base64
import binascii
import getpass
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    import jwt
except ImportError:  # pragma: no cover - 依存未導入時のCLIメッセージ用
    jwt = None  # type: ignore[assignment]


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config" / "github_app.json"
API_VERSION = "2022-11-28"
USER_AGENT = "B-Stats-Site-GitHub-App-Token"


@dataclass(frozen=True)
class GitHubAppConfig:
    """秘密値を含まないGitHub Appローカル設定。"""

    issuer: str
    installation_id: int | None
    repository_owner: str
    repository_name: str
    keychain_service: str
    keychain_account: str | None
    permissions: dict[str, str] | None
    api_url: str


@dataclass(frozen=True)
class IssuedToken:
    """Installation token本体と、表示してよい有効期限。"""

    token: str
    expires_at: str
    installation_id: int
    permissions: dict[str, str]


class GitHubAppConfigurationError(RuntimeError):
    """ローカル設定に不備がある場合の例外。"""


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="macOS Keychainの秘密鍵からGitHub App Installation tokenを発行する"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"ローカル設定JSON（default: {DEFAULT_CONFIG}）",
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument(
        "--check-config",
        action="store_true",
        help="JSON設定の形式だけを確認する。秘密鍵・ネットワークは使わない。",
    )
    action.add_argument(
        "--check-keychain",
        action="store_true",
        help="Keychain項目の存在とPEM形式を確認する。tokenは発行しない。",
    )
    action.add_argument(
        "--verify",
        action="store_true",
        help="tokenを発行して対象リポジトリへのreadアクセスを確認する。tokenは表示しない。",
    )
    action.add_argument(
        "--print-token",
        action="store_true",
        help="Installation tokenだけを標準出力へ出す。コマンド置換専用。",
    )
    return parser.parse_args()


def _text(value: Any, field_name: str) -> str:
    if isinstance(value, bool):
        raise GitHubAppConfigurationError(f"{field_name}は文字列または数値で指定してください")
    normalized = str(value).strip() if value is not None else ""
    if not normalized:
        raise GitHubAppConfigurationError(f"{field_name}が空です")
    if normalized.startswith("REPLACE_WITH_"):
        raise GitHubAppConfigurationError(
            f"{field_name}がテンプレート値のままです: config/github_app.jsonを編集してください"
        )
    return normalized


def _positive_int(value: Any, field_name: str) -> int:
    text = _text(value, field_name)
    try:
        number = int(text)
    except ValueError as error:
        raise GitHubAppConfigurationError(f"{field_name}は正の整数で指定してください") from error
    if number <= 0:
        raise GitHubAppConfigurationError(f"{field_name}は正の整数で指定してください")
    return number


def _optional_positive_int(value: Any, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return _positive_int(value, field_name)


def _load_config(path: Path) -> GitHubAppConfig:
    if not path.is_file():
        raise GitHubAppConfigurationError(
            f"設定がありません: {path}。config/github_app.example.jsonを複製してください"
        )
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GitHubAppConfigurationError(f"設定JSONを読めません: {path}") from error
    if not isinstance(raw, dict):
        raise GitHubAppConfigurationError("設定JSONのトップレベルはobjectにしてください")

    client_id = raw.get("client_id")
    app_id = raw.get("app_id")
    if app_id is not None:
        _positive_int(app_id, "app_id")
    if client_id is not None:
        issuer = _text(client_id, "client_id")
    elif app_id is not None:
        issuer = str(_positive_int(app_id, "app_id"))
    else:
        raise GitHubAppConfigurationError("client_idまたはapp_idを指定してください")

    repository = _text(raw.get("repository"), "repository")
    owner, separator, name = repository.partition("/")
    if not separator or not owner or not name or "/" in name:
        raise GitHubAppConfigurationError("repositoryはowner/repository形式で指定してください")

    keychain = raw.get("keychain")
    if isinstance(keychain, dict):
        keychain_service = _text(keychain.get("service"), "keychain.service")
        keychain_account: str | None = _text(
            keychain.get("account"), "keychain.account"
        )
    elif isinstance(keychain, str):
        keychain_service = _text(keychain, "keychain")
        account_value = raw.get("keychain_account")
        keychain_account = (
            _text(account_value, "keychain_account")
            if account_value is not None
            else None
        )
    elif raw.get("keychain_service") is not None:
        keychain_service = _text(raw.get("keychain_service"), "keychain_service")
        account_value = raw.get("keychain_account")
        keychain_account = (
            _text(account_value, "keychain_account")
            if account_value is not None
            else None
        )
    else:
        raise GitHubAppConfigurationError(
            "keychainはservice/accountを持つobject、service名の文字列、"
            "またはkeychain_serviceにしてください"
        )

    raw_permissions = raw.get("permissions")
    permissions: dict[str, str] | None = None
    if raw_permissions is not None:
        if not isinstance(raw_permissions, dict) or not raw_permissions:
            raise GitHubAppConfigurationError(
                "permissionsは1件以上の権限を持つobjectにしてください"
            )
        permissions = {}
        for name_key, level in raw_permissions.items():
            permission_name = _text(name_key, "permissionsのキー")
            permission_level = _text(level, f"permissions.{permission_name}")
            if permission_level not in {"read", "write"}:
                raise GitHubAppConfigurationError(
                    f"permissions.{permission_name}はreadまたはwriteにしてください"
                )
            permissions[permission_name] = permission_level

    api_url = _text(raw.get("api_url", "https://api.github.com"), "api_url").rstrip("/")
    if not api_url.startswith("https://"):
        raise GitHubAppConfigurationError("api_urlはhttps://で始まるURLにしてください")

    return GitHubAppConfig(
        issuer=issuer,
        installation_id=_optional_positive_int(
            raw.get("installation_id"), "installation_id"
        ),
        repository_owner=owner,
        repository_name=name,
        keychain_service=keychain_service,
        keychain_account=keychain_account,
        permissions=permissions,
        api_url=api_url,
    )


def _read_private_key(config: GitHubAppConfig) -> str:
    account = config.keychain_account or getpass.getuser()
    command = [
        "security",
        "find-generic-password",
        "-a",
        account,
        "-s",
        config.keychain_service,
    ]
    command.append("-w")
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise RuntimeError("macOSのsecurityコマンドが見つかりません") from error
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            "KeychainのGitHub App秘密鍵を取得できません。"
            "configのkeychain_service/accountとKeychain項目を確認してください"
        ) from error

    private_key = completed.stdout.strip()
    if not private_key.startswith("-----BEGIN"):
        try:
            private_key = base64.b64decode(private_key, validate=True).decode(
                "utf-8"
            ).strip()
        except (binascii.Error, UnicodeDecodeError) as error:
            raise RuntimeError("Keychain項目にPEM形式のGitHub App秘密鍵がありません") from error
    if not private_key.startswith("-----BEGIN") or "PRIVATE KEY-----" not in private_key:
        raise RuntimeError("Keychain項目にPEM形式のGitHub App秘密鍵がありません")
    return private_key


def _require_jwt() -> Any:
    if jwt is None:
        raise RuntimeError(
            "PyJWTがありません。python -m pip install -r scraper/requirements.txt を実行してください"
        )
    return jwt


def _create_jwt(config: GitHubAppConfig, private_key: str) -> str:
    jwt_module = _require_jwt()
    now = int(time.time())
    encoded = jwt_module.encode(
        {
            "iat": now - 60,
            "exp": now + 540,
            "iss": config.issuer,
        },
        private_key,
        algorithm="RS256",
    )
    return encoded.decode("utf-8") if isinstance(encoded, bytes) else encoded


def _request_json(
    *,
    url: str,
    bearer_token: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {bearer_token}",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": API_VERSION,
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            result = json.load(response)
    except HTTPError as error:
        message = "GitHub API request failed"
        try:
            detail = json.load(error)
            if isinstance(detail, dict) and isinstance(detail.get("message"), str):
                message = detail["message"]
        except (json.JSONDecodeError, OSError):
            pass
        raise RuntimeError(f"GitHub API {error.code}: {message}") from error
    except URLError as error:
        raise RuntimeError(f"GitHub APIへ接続できません: {error.reason}") from error
    if not isinstance(result, dict):
        raise RuntimeError("GitHub APIのレスポンス形式が不正です")
    return result


def _issue_token(config: GitHubAppConfig, private_key: str) -> IssuedToken:
    app_jwt = _create_jwt(config, private_key)
    installation_id = config.installation_id or _resolve_installation_id(config, app_jwt)
    payload: dict[str, Any] = {"repositories": [config.repository_name]}
    if config.permissions is not None:
        payload["permissions"] = config.permissions
    response = _request_json(
        url=(
            f"{config.api_url}/app/installations/{installation_id}/access_tokens"
        ),
        bearer_token=app_jwt,
        method="POST",
        payload=payload,
    )
    token = response.get("token")
    expires_at = response.get("expires_at")
    if not isinstance(token, str) or not token:
        raise RuntimeError("GitHub APIのInstallation tokenが空です")
    if not isinstance(expires_at, str) or not expires_at:
        raise RuntimeError("GitHub APIのInstallation token有効期限がありません")
    permissions = response.get("permissions")
    return IssuedToken(
        token=token,
        expires_at=expires_at,
        installation_id=installation_id,
        permissions=permissions if isinstance(permissions, dict) else {},
    )


def _resolve_installation_id(config: GitHubAppConfig, app_jwt: str) -> int:
    response = _request_json(
        url=(
            f"{config.api_url}/repos/"
            f"{config.repository_owner}/{config.repository_name}/installation"
        ),
        bearer_token=app_jwt,
    )
    return _positive_int(response.get("id"), "GitHub APIのinstallation_id")


def _verify_repository(config: GitHubAppConfig, issued: IssuedToken) -> dict[str, Any]:
    repository = _request_json(
        url=f"{config.api_url}/repos/{config.repository_owner}/{config.repository_name}",
        bearer_token=issued.token,
    )
    return {
        "repository": repository.get("full_name"),
        "private": repository.get("private"),
        "installation_id": issued.installation_id,
        "token_expires_at": issued.expires_at,
        "token_permissions": issued.permissions,
    }


def main() -> None:
    args = _parse_args()
    try:
        config = _load_config(args.config)
        if args.check_config:
            print("GitHub App設定の形式は有効です")
            return

        private_key = _read_private_key(config)
        if args.check_keychain:
            print("GitHub App秘密鍵のKeychain項目を確認しました")
            return

        issued = _issue_token(config, private_key)
        if args.print_token:
            print(issued.token)
            return
        print(json.dumps(_verify_repository(config, issued), ensure_ascii=False, indent=2))
    except (GitHubAppConfigurationError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()

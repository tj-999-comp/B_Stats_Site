-- players.nationality を削除し、暫定ルールで player_slot_category を補完する
-- 作成日: 2026-05-27
-- 実行日: 2026-05-27
-- 種別: 一回限りのスキーマ変更・データパッチ（現行スキーマの正本ではない）

BEGIN;

-- 1) nationality を削除
ALTER TABLE public.players
    DROP COLUMN IF EXISTS nationality;

-- 2) player_slot_category を暫定補完
-- ルール: player_name_j が「漢字のみ」の場合は「日本人選手」
-- 既存で player_slot_category が入っている行は上書きしない
UPDATE public.players
SET player_slot_category = '日本人選手',
    updated_at = NOW()
WHERE (player_slot_category IS NULL OR BTRIM(player_slot_category) = '')
  AND player_name_j IS NOT NULL
  AND REGEXP_REPLACE(player_name_j, '[[:space:]　・･]', '', 'g') <> ''
  AND REGEXP_REPLACE(player_name_j, '[[:space:]　・･]', '', 'g') ~ '^[一-龥々〆ヵヶ]+$';

COMMIT;

-- 3) 確認用クエリ
SELECT
    player_slot_category,
    COUNT(*) AS cnt
FROM public.players
GROUP BY player_slot_category
ORDER BY cnt DESC, player_slot_category;

SELECT
    COUNT(*) AS japanese_filled_rows
FROM public.players
WHERE player_slot_category = '日本人選手';

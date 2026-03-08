-- games テーブルに game_type カラムを追加する
-- RS: Regular Season (setu <= 100)
-- CS: Championship Series (setu >= 101)

ALTER TABLE games
  ADD COLUMN IF NOT EXISTS game_type text;

-- 全シーズン一括更新
UPDATE games
SET game_type = CASE
  WHEN setu::integer <= 100 THEN 'RS'
  ELSE 'CS'
END
WHERE setu IS NOT NULL;

-- シーズン指定で更新する場合は下記のWHEREを使用
-- WHERE year = 2022 AND setu IS NOT NULL;

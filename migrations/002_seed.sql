-- Moonshot: visa_data.json seed
-- migrations/002_seed.sql
-- 재실행 가능 (TRUNCATE → INSERT)

BEGIN;

TRUNCATE visa_sub_codes, visas RESTART IDENTITY CASCADE;

INSERT INTO visas
  (code, name, cat, period, new_req, ext_req, faq, data_badge, data_date, aliases, sort_order)
VALUES

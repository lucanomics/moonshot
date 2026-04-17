-- Moonshot: visas schema
-- migrations/001_schema.sql

CREATE TABLE IF NOT EXISTS visas (
    id          SERIAL PRIMARY KEY,
    code        TEXT        NOT NULL UNIQUE,
    name        TEXT        NOT NULL,
    cat         TEXT,
    period      TEXT,
    new_req     TEXT,
    ext_req     TEXT,
    faq         TEXT,
    data_badge  TEXT,
    data_date   TEXT,
    aliases     JSONB,
    sort_order  INT         NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS visa_sub_codes (
    id          SERIAL PRIMARY KEY,
    code        TEXT        NOT NULL UNIQUE,
    parent_code TEXT        NOT NULL REFERENCES visas(code) ON DELETE CASCADE,
    name        TEXT        NOT NULL,
    add_req     TEXT,
    note        TEXT,
    aliases     JSONB,
    sort_order  INT         NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_visa_sub_codes_parent ON visa_sub_codes(parent_code);

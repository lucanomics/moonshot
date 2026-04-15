-- moonshot_schema.sql
DROP TABLE IF EXISTS visa_data CASCADE;

CREATE TABLE visa_data (
    code VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    cat VARCHAR(50) NOT NULL,
    period VARCHAR(255),
    data_badge VARCHAR(255),
    data_date VARCHAR(255),
    new_req TEXT,
    ext_req TEXT,
    faq TEXT,
    aliases JSONB,
    sub_codes JSONB
);

CREATE INDEX idx_visa_cat ON visa_data(cat);

CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
CREATE TABLE IF NOT EXISTS "user" (
    email VARCHAR NOT NULL,
    id SERIAL NOT NULL,
    name VARCHAR NOT NULL,
    age INTEGER,
    phone VARCHAR,
    face_id VARCHAR,
    trained BOOLEAN NOT NULL,
    face_data BYTEA,
    password VARCHAR NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (face_id),
    UNIQUE (face_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_user_email ON "user" (email);
CREATE INDEX IF NOT EXISTS ix_user_name ON "user" (name);
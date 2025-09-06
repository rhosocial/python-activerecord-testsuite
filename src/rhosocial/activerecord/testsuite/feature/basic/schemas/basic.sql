-- src/rhosocial/activerecord/testsuite/feature/basic/schemas/basic.sql
-- Schema for basic feature tests

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    age INTEGER,
    balance REAL NOT NULL DEFAULT 0.00,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE type_cases (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    tiny_int INTEGER,
    small_int INTEGER,
    big_int INTEGER,
    float_val REAL,
    double_val REAL,
    decimal_val TEXT,
    char_val TEXT,
    varchar_val TEXT,
    text_val TEXT,
    date_val TEXT,
    time_val TEXT,
    timestamp_val TEXT,
    blob_val BLOB,
    json_val TEXT,
    array_val TEXT,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE validated_field_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    age INTEGER,
    balance REAL NOT NULL DEFAULT 0.00,
    credit_score INTEGER NOT NULL DEFAULT 300,
    status TEXT NOT NULL DEFAULT 'active',
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE type_tests (
    id TEXT PRIMARY KEY,
    string_field TEXT,
    int_field INTEGER,
    float_field REAL,
    decimal_field TEXT,
    bool_field INTEGER,
    datetime_field TEXT,
    json_field TEXT,
    nullable_field TEXT
);

CREATE TABLE validated_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    age INTEGER
);

-- Create Database
CREATE DATABASE fqc_part_checker;

-- NOTE: If you're using psql CLI, switch to the new database using:
-- \c fqc_part_checker

-- ------------------------
-- Create User Table
-- ------------------------
CREATE TABLE user_table (
    employee_id VARCHAR(50) PRIMARY KEY,
    user_type VARCHAR(20) NOT NULL CHECK (user_type IN ('IT_ADMIN', 'ADMIN', 'OPERATOR')),
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    created_by VARCHAR(50) NOT NULL,
    created_date TIMESTAMP NOT NULL,
    modified_date TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- ------------------------
-- Create Add Part Table
-- ------------------------
CREATE TABLE add_part_table (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL REFERENCES user_table(employee_id),
    user_type VARCHAR(20) NOT NULL,
    username VARCHAR(50) NOT NULL,
    id_no VARCHAR(50) UNIQUE NOT NULL,
    ed VARCHAR(50) NOT NULL,
    status VARCHAR(20) CHECK (status IN ('ACTIVE', 'NOT_ACTIVE')),
    created_date TIMESTAMP NOT NULL,
    modified_date TIMESTAMP NOT NULL
);

-- ------------------------
-- Create FQC Part Table
-- ------------------------
CREATE TABLE fqc_part_table (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL REFERENCES user_table(employee_id),
    user_type VARCHAR(20) NOT NULL,
    username VARCHAR(50) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    location VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    shift VARCHAR(1) NOT NULL,
    crown_scan VARCHAR(100) NOT NULL,
    pinion_scan VARCHAR(100) NOT NULL,
    crown_id_no VARCHAR(50) NOT NULL,
    pinion_id_no VARCHAR(50) NOT NULL,
    crown_set_no VARCHAR(50) NOT NULL,
    pinion_set_no VARCHAR(50) NOT NULL,
    ed_no VARCHAR(50) NOT NULL,
    set_match VARCHAR(3) NOT NULL CHECK (set_match IN ('YES', 'NO')),
    part_match VARCHAR(3) NOT NULL CHECK (part_match IN ('YES', 'NO')),
    overall_status VARCHAR(10) NOT NULL CHECK (overall_status IN ('OK', 'NOT_OK')),
    repeat_no VARCHAR(10) DEFAULT ''
);

-- ------------------------
-- Create Login Log Table
-- ------------------------
CREATE TABLE login_table (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL REFERENCES user_table(employee_id),
    user_type VARCHAR(20) NOT NULL,
    username VARCHAR(50) NOT NULL,
    last_login TIMESTAMP NOT NULL
);

-- ------------------------
-- Insert Sample Users
-- ------------------------
INSERT INTO user_table (
    employee_id, user_type, username, password, first_name, last_name, email, phone_number,
    created_by, created_date, modified_date, is_active, is_deleted
)
VALUES 
    ('1234', 'IT_ADMIN', 'VVERMAG', '12345678', 'VISHAL', 'VERMA', 'VVERMAG@VECV.IN', '8851857434',
     'EMPID', '2025-06-26 20:34:07', '2025-06-26 21:12:07', TRUE, FALSE),

    ('567', 'ADMIN', 'RAVI', '12345', 'RAVI', 'CHAWADA', 'ZZRCHAWADA@VECV.IN', '123457890',
     'EMPID', '2025-06-26 18:27:03', '2025-06-26 18:48:06', TRUE, FALSE),

    ('2345', 'OPERATOR', 'ABC', '123', 'HANS', 'RAJ', 'amitravat@vecv.in', '+91 9328971172',
     'EMPID', '2025-06-26 22:43:01', '2025-06-26 23:06:07', TRUE, FALSE);

-- ------------------------
-- Insert Sample Parts
-- ------------------------
INSERT INTO add_part_table (
    employee_id, user_type, username, id_no, ed, status, created_date, modified_date
)
VALUES 
    ('1234', 'IT_ADMIN', 'VVERMAG', 'D10190240', '6148/51', 'ACTIVE', '2025-06-26 00:00:00', '2025-06-26 00:00:00'),
    ('1234', 'IT_ADMIN', 'VVERMAG', '006504487B91', '6338/6361', 'NOT_ACTIVE', '2025-06-26 00:00:00', '2025-06-26 00:00:00'),
    ('1234', 'IT_ADMIN', 'VVERMAG', '1310A01101', '6750/51', 'ACTIVE', '2025-06-26 00:00:00', '2025-06-26 00:00:00');

-- ------------------------
-- Insert Sample FQC Part Check
-- ------------------------
INSERT INTO fqc_part_table (
    employee_id, user_type, username, unit, location, timestamp, shift,
    crown_scan, pinion_scan, crown_id_no, pinion_id_no,
    crown_set_no, pinion_set_no, ed_no,
    set_match, part_match, overall_status, repeat_no
)
VALUES (
    '2345', 'OPERATOR', 'ABC', 'UNIT-1', 'CWPFQC', '2025-06-26 06:28:00', 'C',
    'PID313626A#TFD-87#', 'PID313626A#TFD-87#',
    'ID313626', 'ID313626', 'FD-87', 'FD-87', '5680/81',
    'YES', 'YES', 'OK', ''
);

-- ------------------------
-- Insert Sample Login Log
-- ------------------------
INSERT INTO login_table (
    employee_id, user_type, username, last_login
)
VALUES (
    '2345', 'OPERATOR', 'ABC', '2025-06-27 00:00:00'
);





ALTER TABLE user_table DROP CONSTRAINT IF EXISTS user_table_email_key;
ALTER TABLE user_table DROP CONSTRAINT IF EXISTS user_table_phone_number_key;

-- 2. Make both columns NULLABLE
ALTER TABLE user_table
    ALTER COLUMN email DROP NOT NULL,
    ALTER COLUMN phone_number DROP NOT NULL;

-- 3. Recreate partial UNIQUE indexes (ignore NULLs)
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_email ON user_table(email)
WHERE email IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_user_phone ON user_table(phone_number)
WHERE phone_number IS NOT NULL;






CREATE TABLE qr2_parts (
    id SERIAL PRIMARY KEY,
    
    crown_id VARCHAR(50) NOT NULL,
    crown_ed_no VARCHAR(50) NOT NULL,

    pinion_id VARCHAR(50) NOT NULL,
    pinion_ed_no VARCHAR(50) NOT NULL,

    ed_no VARCHAR(100), -- Combined ED no, e.g., 5790/5790

    employee_id VARCHAR(50),
    user_type VARCHAR(20),
    username VARCHAR(100),

    unit VARCHAR(50),
    location VARCHAR(100),

    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



CREATE TABLE qr2_scan_logs (
    id SERIAL PRIMARY KEY,

    employee_id VARCHAR(50),
    user_type VARCHAR(20),
    username VARCHAR(100),

    unit VARCHAR(50),
    location VARCHAR(100),

    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    shift VARCHAR(10),

    crown_scan TEXT,
    pinion_scan TEXT,

    crown_id VARCHAR(50),
    pinion_id VARCHAR(50),

    crown_set VARCHAR(50),
    pinion_set VARCHAR(50),

    ed_no TEXT,               -- Combined, e.g., 5790/5790

    set_match VARCHAR(10),    -- YES / NO
    ed_match VARCHAR(10),     -- YES / NO
    overall_status VARCHAR(10), -- OK / NOT_OK

    repeat_no INT DEFAULT 1
);

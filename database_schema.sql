CREATE DATABASE raospool;

-- DROP TABLES IF THEY EXIST TO PREVENT ERRORS
DROP TABLE IF EXISTS emp CASCADE;
DROP TABLE IF EXISTS membership CASCADE;
DROP TABLE IF EXISTS "user" CASCADE;


-- WAIT TO ADD TABLES UNTIL AFTER THE DATABASE IS CREATED
CREATE TABLE membership (
    membership_id INTEGER NOT NULL,
    email VARCHAR(80) NOT NULL,
    password VARCHAR(80),
    phone VARCHAR(10),
    street VARCHAR(80),
    city VARCHAR(80),
    state VARCHAR(2),
    zip_code VARCHAR(5),
    billing_type VARCHAR(80),
    membership_type VARCHAR(80),
    last_date_paid DATE,
    size_of_family INTEGER,
    active BOOLEAN NOT NULL,
    PRIMARY KEY (membership_id)
);

CREATE TABLE member (
    member_id INTEGER NOT NULL,
    membership_id INTEGER NOT NULL,

    first_name VARCHAR(80),
    last_name VARCHAR(80),
    birthday DATE,
    -- picture paths (aws)
    profile_image_location VARCHAR(255),

    PRIMARY KEY (member_id),
    FOREIGN KEY (membership_id) REFERENCES membership(membership_id)
);

CREATE TABLE emp (
    emp_id INTEGER NOT NULL,
    first_name VARCHAR(80),
    last_name VARCHAR(80),
    email VARCHAR(80) NOT NULL,
    password VARCHAR(80),
    PRIMARY KEY (emp_id),

    -- admin stuff
    admin BOOLEAN NOT NULL
);

INSERT INTO emp VALUES (1, 'Colin', 'Brown', 'colin8297@gmail.com', 'admin', TRUE);
INSERT INTO membership VALUES (6184, 'lori8297@gmail.com', 'test', '9517606370', '1234 Main St', 'Riverside', 'CA', '92507', 'Yearly', 'Family', '2024-06-01', 6);
INSERT INTO member VALUES (1, 6184, 'Lori', 'Brown', '2000-06-01', '');
INSERT INTO member VALUES (2, 6184, 'Phi;', 'Brown', '1971-02-24', '');
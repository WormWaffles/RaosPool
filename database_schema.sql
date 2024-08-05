CREATE DATABASE raospool;

-- DROP TABLES IF THEY EXIST TO PREVENT ERRORS
DROP TABLE IF EXISTS emp CASCADE;
DROP TABLE IF EXISTS membership CASCADE;
DROP TABLE IF EXISTS "user" CASCADE;


CREATE SEQUENCE member_id_seq
    START 1000
    INCREMENT BY 1
    MINVALUE 1000
    MAXVALUE 9999
    CACHE 1;

-- WAIT TO ADD TABLES UNTIL AFTER THE DATABASE IS CREATED
CREATE TABLE membership (
    membership_id INT NOT NULL DEFAULT nextval('member_id_seq'),
    email VARCHAR(80) NOT NULL,
    password VARCHAR(80),
    phone VARCHAR(10),
    street VARCHAR(80),
    city VARCHAR(80),
    state VARCHAR(2),
    zip_code VARCHAR(5),
    membership_type VARCHAR(80),
    size_of_family INTEGER,
    referred_by VARCHAR(80),
    emergency_contact_name VARCHAR(80),
    emergency_contact_phone VARCHAR(10),
    billing_type VARCHAR(80),
    last_date_paid DATE,
    active BOOLEAN NOT NULL,
    PRIMARY KEY (membership_id)
);

CREATE TABLE member (
    member_id INTEGER NOT NULL,
    membership_id INTEGER NOT NULL,

    first_name VARCHAR(80),
    last_name VARCHAR(80),
    birthday DATE,
    membership_owner BOOLEAN NOT NULL,
    -- picture paths (aws)
    profile_image_location VARCHAR(255),

    PRIMARY KEY (member_id),
    FOREIGN KEY (membership_id) REFERENCES membership(membership_id)
);

CREATE TABLE emp (
    emp_id INTEGER NOT NULL,
    position VARCHAR(80),
    first_name VARCHAR(80),
    middle_name VARCHAR(80),
    last_name VARCHAR(80),
    email VARCHAR(80) NOT NULL,
    password VARCHAR(80),
    phone VARCHAR(10),
    birthday DATE,
    us_eligable BOOLEAN NOT NULL,
    license BOOLEAN NOT NULL,
    street VARCHAR(80),
    city VARCHAR(80),
    state VARCHAR(2),
    zip_code VARCHAR(5),
    felony VARCHAR(5),
    active BOOLEAN NOT NULL,
    PRIMARY KEY (emp_id),

    -- admin stuff
    admin BOOLEAN NOT NULL
);

CREATE TABLE code (
    code_id INTEGER NOT NULL,
    email VARCHAR(80) NOT NULL,
    PRIMARY KEY (code_id)
);

CREATE TABLE checkin (
    checkin_id INTEGER NOT NULL,
    member_id VARCHAR(80) NOT NULL,
    checkin_date TIMESTAMP NOT NULL,
    PRIMARY KEY (checkin_id)
);

CREATE TABLE reservation (
    reservation_id INTEGER NOT NULL,
    member_id VARCHAR(80) NOT NULL,
    reservation_date DATE NOT NULL,
    reservation_time TIMESTAMP NOT NULL,
    guest_count INTEGER NOT NULL,
    court_number INTEGER NOT NULL,
    order_id INTEGER DEFAULT NULL,
    PRIMARY KEY (reservation_id)
);
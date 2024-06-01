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
    PRIMARY KEY (membership_id)
);

CREATE TABLE member (
    member_id INTEGER NOT NULL,
    membership_id INTEGER NOT NULL,

    first_name VARCHAR(80),
    last_name VARCHAR(80),
    -- picture paths (aws)
    profile_image_location VARCHAR(255)

    PRIMARY KEY (member_id),
    FOREIGN KEY (membership_id) REFERENCES membership(membership_id)
);

CREATE TABLE emp (
    emp_id INTEGER NOT NULL,
    first_name VARCHAR(80),
    last_name VARCHAR(80),
    email VARCHAR(80) NOT NULL,
    password VARCHAR(80),
    PRIMARY KEY (user_id),

    -- admin stuff
    admin BOOLEAN NOT NULL,
);
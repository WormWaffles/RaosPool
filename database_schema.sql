CREATE DATABASE raospool;

-- DROP TABLES IF THEY EXIST TO PREVENT ERRORS
DROP TABLE IF EXISTS emp CASCADE;
DROP TABLE IF EXISTS "user" CASCADE;


-- WAIT TO ADD TABLES UNTIL AFTER THE DATABASE IS CREATED
CREATE TABLE "user" (
    user_id INTEGER NOT NULL,
    first_name VARCHAR(80),
    last_name VARCHAR(80),
    email VARCHAR(80) NOT NULL,
    password VARCHAR(80),
    PRIMARY KEY (user_id),
    -- picture paths (aws)
    profile_image_location VARCHAR(255)
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
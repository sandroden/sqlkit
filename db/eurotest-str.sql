CREATE TABLE city (
    city_id serial NOT NULL,
    city_name character varying(30) NOT NULL,
    city_pv char(2) NOT NULL,
    PRIMARY KEY (city_id)
);
CREATE TABLE euro_user (
    user_id serial NOT NULL,
    user_name character varying(30) NOT NULL UNIQUE,
    user_last_name character varying(30) NOT NULL,
    user_birth_date date, 
    user_address character varying(20),
--    city_id character varying(20),
    city_id int,
    user_age int,
    user_sex char(1),
    user_active bool,
    user_timestamp  timestamp without time zone,
    CONSTRAINT euro_user_pkey PRIMARY KEY (user_id),
    FOREIGN KEY (city_id) REFERENCES city(city_id)
);

CREATE TABLE euro_mail (
    mail_id serial NOT NULL,
    mail_address character varying(30) NOT NULL,
    mail_user_id integer,
    mail_info varchar(50),
    PRIMARY KEY (mail_id),
    FOREIGN KEY (mail_user_id) REFERENCES euro_user(user_id)
);

-- CREATE TABLE user_city (
--     city character varying(30) NOT NULL,
--     user_name varchar(30),
--     PRIMARY KEY (city, user_name),
--     FOREIGN KEY (user_name) REFERENCES euro_user(user_name),
--     FOREIGN KEY (city) REFERENCES city(city_name)
-- );

--ALTER TABLE euro_user ADD CONSTRAINT euro_user_city FOREIGN KEY (city) REFERENCES city (city) MATCH FULL;

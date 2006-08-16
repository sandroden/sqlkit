CREATE TABLE test_user (
    user_id serial NOT NULL,
    user_name character varying(30) NOT NULL,
    user_last_name character varying(30) NOT NULL,
    user_birth_date timestamp, 
    user_address character varying(20),
    user_city character varying(20),
    user_pv  character(2),
    user_age int,
    user_sex char(1),
    user_active bool,
    user_timestamp timestamp without time zone,
    user_fee numeric(8,2),
    user_float double precision,

    CONSTRAINT test_user_pkey PRIMARY KEY (user_id)
);
CREATE TABLE test_mail (
    mail_id serial NOT NULL,
    mail_address character varying(30) NOT NULL,
    mail_user_id integer,
    PRIMARY KEY (mail_address),
    FOREIGN KEY (mail_user_id) REFERENCES test_user(user_id)
);

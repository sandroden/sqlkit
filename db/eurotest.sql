SET client_encoding = 'LATIN9';
SET check_function_bodies = false;

SET SESSION AUTHORIZATION 'postgres';

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


SET SESSION AUTHORIZATION 'test';

SET search_path = public, pg_catalog;

CREATE TABLE euro_user (
    user_id serial NOT NULL,
    user_name character varying(30) NOT NULL,
    user_last_name character varying(30) NOT NULL,
    user_birth_date date, 
    user_address character varying(20),
    user_city character varying(20),
    user_pv  character(2),
    user_age int,
    user_sex char(1),
    user_active bool,

    CONSTRAINT euro_user_pkey PRIMARY KEY (user_id)
);
CREATE TABLE euro_mail (
    mail_address character varying(30) NOT NULL,
    mail_user_id integer,
    PRIMARY KEY (mail_address),
    FOREIGN KEY (mail_user_id) REFERENCES euro_user(user_id)
);


COPY euro_user (user_id, user_name, user_last_name, user_birth_date, user_address, user_city, user_pv, user_age, user_sex, user_active) FROM stdin;
1	Sam	Patts	1963-04-07	C.na vega 1	Usmate	mi	42	m	t
2	Sid	Watts	1972-04-07	manzoni	Merate	vr	30	m	t
3	Axe	Smith	2005-01-01	verdi	Monza	mz	1	m	f
4	Ted	Will	2000-12-25	mozart	milano	mi	33	m	t
5	Fat	Joe	1990-08-01	foscolo	mantova	mn	20	m	f
6	Jim	Big	1995-09-23	grimm	sondrio	so	50	m	t
7	Suzan	White	1970-10-23	boh	lecco	lc	40	f	t
8	Anna	Pearl	1972-09-09	mah	nova	mi	32	f	t
\.


--
-- Data for TOC entry 11 (OID 815932)
-- Name: euro_mail; Type: TABLE DATA; Schema: public; Owner: test
--

COPY euro_mail (mail_address, mail_user_id) FROM stdin;
sam@example.com	1
sid@example.com	2
sid2@example.com	2
ted@example.com	4
ted_will@example.com	4
fjoe@example.com	5
jbig@example.com	6
\.


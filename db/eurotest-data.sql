COPY city (city_id, city_name, city_pv) FROM stdin;
1	Monza	MI
2	Milano	MI
3	Usmate	MI
4	Lecco	LC
5	Como	CO
6	Sondrio	SO
7	Nova	MI
8	Merate	BG
9	Selvino	BG
\.
SELECT setval('city_city_id_seq',(select max(city_id) from city));




--
-- Data for TOC entry 11 (OID 815932)
-- Name: euro_mail; Type: TABLE DATA; Schema: public; Owner: test
--

COPY euro_user (user_id, user_name, user_last_name, user_birth_date, user_address, city_id, user_age, user_sex, user_active) FROM stdin;
1	Sam	Patts	1963-04-07	vega 1	1	42	m	t
2	Sid	Watts	1972-04-07	manzoni	2	30	m	t
3	Axe	Smith	2005-01-01	verdi	3	1	m	f
4	Ted	Will	2000-12-25	mozart	4	33	m	t
5	Fat	Joe	1990-08-01	foscolo	5	20	m	f
6	Jim	Big	1995-09-23	grimm	6	50	m	t
7	Suzan	White	1970-10-23	boh	7	40	f	t
8	Ann	Pearl	1972-09-09	mah	8	32	f	t
\.
SELECT setval('euro_user_user_id_seq',(select max(user_id) from euro_user));
COPY euro_mail (mail_address, mail_user_id) FROM stdin;
sam@example.com	1
sid@example.com	2
asid2@example.com	2
ated@example.com	4
ted_will@example.com	4
fjoe@example.com	5
jbig@example.com	6
\.

-- COPY user_city (user_name, city) FROM stdin;
-- Sam	Monza
-- Sid	Lecco
-- Axe	Nova
-- Ted	Como
-- Ted	Lecco
-- Ted	Usmate
-- Fat	Milano
-- Jim	Selvino
-- Suzan	Selvino
-- Anna	Nova
-- \.


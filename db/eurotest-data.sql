COPY city (city, pv) FROM stdin;
Monza	MI
Milano	MI
Usmate	MI
Lecco	LC
Como	CO
Sondrio	SO
Nova	MI
Merate	BG
Selvino	BG
\.





--
-- Data for TOC entry 11 (OID 815932)
-- Name: euro_mail; Type: TABLE DATA; Schema: public; Owner: test
--

COPY euro_user (user_id, user_name, user_last_name, user_birth_date, user_address, user_city, user_pv, user_age, user_sex, user_active) FROM stdin;
1	Sam	Patts	1963-04-07	C.na vega 1	Usmate	mi	42	m	t
2	Sid	Watts	1972-04-07	manzoni	Merate	vr	30	m	t
3	Axe	Smith	2005-01-01	verdi	Monza	mz	1	m	f
4	Ted	Will	2000-12-25	mozart	Milano	mi	33	m	t
5	Fat	Joe	1990-08-01	foscolo	Como	mn	20	m	f
6	Jim	Big	1995-09-23	grimm	Sondrio	so	50	m	t
7	Suzan	White	1970-10-23	boh	Lecco	lc	40	f	t
8	Anna	Pearl	1972-09-09	mah	Nova	mi	32	f	t
\.

COPY euro_mail (mail_address, mail_user_id) FROM stdin;
sam@example.com	1
sid@example.com	2
asid2@example.com	2
ated@example.com	4
ted_will@example.com	4
fjoe@example.com	5
jbig@example.com	6
\.

COPY user_city (user_name, city) FROM stdin;
Sam	Monza
Sid	Lecco
Axe	Nova
Ted	Como
Ted	Lecco
Ted	Usmate
Fat	Milano
Jim	Selvino
Suzan	Selvino
Anna	Nova
\.


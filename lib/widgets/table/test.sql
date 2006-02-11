--
-- PostgreSQL database dump
--

SET client_encoding = 'UTF8';
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: test; Type: DATABASE; Schema: -; Owner: test
--

CREATE DATABASE test WITH TEMPLATE = template0 ENCODING = 'UTF8';


ALTER DATABASE test OWNER TO test;

\connect test

SET client_encoding = 'UTF8';
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS 'Standard public schema';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: table1; Type: TABLE; Schema: public; Owner: test; Tablespace: 
--

CREATE TABLE table1 (
    id integer NOT NULL,
    nome character varying(30),
    cognome character varying(30)
);


ALTER TABLE public.table1 OWNER TO test;

--
-- Name: table2; Type: TABLE; Schema: public; Owner: test; Tablespace: 
--

CREATE TABLE table2 (
    uid character varying(16) NOT NULL,
    id integer
);


ALTER TABLE public.table2 OWNER TO test;

--
-- Data for Name: table1; Type: TABLE DATA; Schema: public; Owner: test
--

COPY table1 (id, nome, cognome) FROM stdin;
1	mario	rossi
2	gianni	verdi
3	felice	natale
\.


--
-- Data for Name: table2; Type: TABLE DATA; Schema: public; Owner: test
--

COPY table2 (uid, id) FROM stdin;
m1	1
g1	2
f1	3
\.


--
-- Name: table1_pkey; Type: CONSTRAINT; Schema: public; Owner: test; Tablespace: 
--

ALTER TABLE ONLY table1
    ADD CONSTRAINT table1_pkey PRIMARY KEY (id);


--
-- Name: table2_pkey; Type: CONSTRAINT; Schema: public; Owner: test; Tablespace: 
--

ALTER TABLE ONLY table2
    ADD CONSTRAINT table2_pkey PRIMARY KEY (uid);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--


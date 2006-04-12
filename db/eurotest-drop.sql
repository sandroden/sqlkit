SET client_encoding = 'LATIN1';
SET check_function_bodies = false;

SET SESSION AUTHORIZATION 'postgres';

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


SET SESSION AUTHORIZATION 'test';

SET search_path = public, pg_catalog;
DROP TABLE euro_user CASCADE;
DROP TABLE euro_mail CASCADE;
DROP TABLE city CASCADE;
DROP TABLE user_city CASCADE;









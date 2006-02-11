
CREATE TABLE test1 (
  id SERIAL PRIMARY KEY,
  active BOOL
);

CREATE TABLE test2 (
  id SERIAL PRIMARY KEY,
  fk_id INT REFERENCES test1(id) ON DELETE CASCADE,
  name VARCHAR (40),
  surname VARCHAR (40),
  age INT
);

INSERT INTO test1 (active) VALUES ('True');
INSERT INTO test2 (id, fk_id, name, surname, age) VALUES (1, 1, 'Nicholas', 'Wieland', 27);


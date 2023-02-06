-- Postgres database.
CREATE DATABASE clansptbr;

CREATE TABLE clans (
    id SERIAL PRIMARY KEY,
    nome VARCHAR
);

CREATE TABLE dxp (
    id SERIAL PRIMARY KEY,
    data_comeco DATE,
    data_fim DATE
);

CREATE TABLE exp (
    id SERIAL PRIMARY KEY,
    id_clan INTEGER REFERENCES clans (id),
    data_hora TIMESTAMP,
    exp BIGINT 
);
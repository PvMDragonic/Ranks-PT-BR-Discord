-- Postgres database.
CREATE DATABASE clansptbr;

CREATE TABLE clans (
    id INT PRIMARY KEY, -- clanId da Jagex.
    arquivado BOOLEAN
);

CREATE TABLE nomes (
    id SERIAL PRIMARY KEY,
    id_clan INT REFERENCES clans (id),
    nome VARCHAR,
    data_alterado DATE
);

CREATE TABLE dxp (
    id SERIAL PRIMARY KEY,
    data_comeco TIMESTAMP,
    data_fim TIMESTAMP
);

CREATE TABLE estatisticas (
    id SERIAL PRIMARY KEY,
    id_clan INT REFERENCES clans (id),
    data_hora TIMESTAMP,
    membros INT,
    nv_fort INT,
    nv_total INT,
    nv_cb_total INT,
    exp_total BIGINT 
);

CREATE TABLE admins (
    id SERIAL PRIMARY KEY,
    id_discord BIGINT,
    nv_acesso INT
);
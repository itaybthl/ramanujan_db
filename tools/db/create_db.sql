-- Creating DB
CREATE DATABASE ramanujanv3
    WITH
    OWNER = postgres
;

-- Use DB
\c ramanujanv3

-- Add module for uuid
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Creating tables
CREATE TABLE constant (
	const_id UUID NOT NULL DEFAULT uuid_generate_v1() PRIMARY KEY,
	value NUMERIC,
	precision INT,
	time_added timestamp DEFAULT current_timestamp
);

CREATE TABLE named_constant (
    const_id UUID NOT NULL PRIMARY KEY REFERENCES constant (const_id),
	name VARCHAR NOT NULL UNIQUE,
	description VARCHAR,
	artificial INT NOT NULL DEFAULT 0
);

CREATE TABLE pcf_canonical_constant (
    const_id UUID NOT NULL PRIMARY KEY REFERENCES constant (const_id),
	p INT[] NOT NULL,
	q INT[] NOT NULL,
	last_matrix INT[],
	depth INT,
	convergence INT,
	
	UNIQUE(p, q)
);

CREATE TABLE scan_history (
    const_id UUID NOT NULL PRIMARY KEY REFERENCES constant (const_id),
	algorithm VARCHAR NOT NULL,
	time_scanned timestamp DEFAULT current_timestamp,
	details VARCHAR
);

CREATE TABLE relation (
	relation_id UUID NOT NULL DEFAULT uuid_generate_v1() PRIMARY KEY,
	relation_type VARCHAR NOT NULL,
	details INT[] NOT NULL,
	time_added timestamp DEFAULT current_timestamp
);

CREATE TABLE constant_in_relation (
	const_id UUID NOT NULL REFERENCES constant (const_id) ON UPDATE CASCADE ON DELETE CASCADE,
	relation_id UUID NOT NULL REFERENCES relation (relation_id) ON UPDATE CASCADE,
	CONSTRAINT const_relation_pkey PRIMARY KEY (const_id, relation_id)
);

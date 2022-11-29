USE `againstall`;

CREATE TABLE IF NOT EXISTS Player (alias varchar(30) PRIMARY KEY,
                passwd varchar(30) NOT NULL,
                nivel integer DEFAULT 0,
                EF integer DEFAULT 0,
                EC integer DEFAULT 0,
                posicion varchar(30));

COMMIT;


ALTER DATABASE againstall CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

USE againstall;

CREATE TABLE IF NOT EXISTS Player (alias VARCHAR(30) PRIMARY KEY,
                passwd VARCHAR(64) NOT NULL,
                salt VARCHAR(64) NOT NULL,
                nivel TINYINT DEFAULT 0,
                niveltotal TINYINT DEFAULT 0,
                EF TINYINT DEFAULT 0,
                EC TINYINT DEFAULT 0,
                posicion VARCHAR(30)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Game (id INTEGER PRIMARY KEY AUTO_INCREMENT,
                map VARCHAR(5000) NOT NULL,
                stamp DATETIME NOT NULL,
                players VARCHAR(150) NOT NULL,
                npcs VARCHAR(150),
                cities VARCHAR(150),
                quadrants VARCHAR(150),
                mines VARCHAR(1000),
                food VARCHAR(1000)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

COMMIT;
CREATE DATABASE IF NOT EXISTS reverbapp;

USE reverbapp;

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS entries;

CREATE TABLE users
(
    userid       int not null AUTO_INCREMENT,
    username     varchar(64) not null,
    pwdhash      varchar(256) not null,
    PRIMARY KEY  (userid),
    UNIQUE       (username)
);

ALTER TABLE users AUTO_INCREMENT = 20001;  -- starting value

CREATE TABLE entries
(
    entryid           int not null AUTO_INCREMENT,
    userid            int not null,
    entrydate         date not null, -- YYYY-MM-DD
    songname          varchar(256) not null,
    artist            varchar(256) not null,
    blurb             text not null,
    encryptionkey     varchar(256) not null,
    PRIMARY KEY (entryid),
    FOREIGN KEY (userid) REFERENCES users(userid),
    UNIQUE      (encryptionkey)
);

ALTER TABLE entries AUTO_INCREMENT = 10001;  -- starting value

--
-- Insert some users to start with:
-- 
-- PWD hashing: https://phppasswordhash.com/
--
INSERT INTO users(username, pwdhash)  -- pwd = abc123!!
            values('p_sarkar', '$2y$10$/8B5evVyaHF.hxVx0i6dUe2JpW89EZno/VISnsiD1xSh6ZQsNMtXK');

INSERT INTO users(username, pwdhash)  -- pwd = abc456!!
            values('e_ricci', '$2y$10$F.FBSF4zlas/RpHAxqsuF.YbryKNr53AcKBR3CbP2KsgZyMxOI2z2');

INSERT INTO users(username, pwdhash)  -- pwd = abc789!!
            values('l_chen', '$2y$10$GmIzRsGKP7bd9MqH.mErmuKvZQ013kPfkKbeUAHxar5bn1vu9.sdK');

--
-- creating user accounts for database access:
--
-- ref: https://dev.mysql.com/doc/refman/8.0/en/create-user.html
--

DROP USER IF EXISTS 'reverbapp-read-only';
DROP USER IF EXISTS 'reverbapp-read-write';

CREATE USER 'reverbapp-read-only' IDENTIFIED BY 'abc123!!';
CREATE USER 'reverbapp-read-write' IDENTIFIED BY 'def456!!';

GRANT SELECT, SHOW VIEW ON reverbapp.* 
      TO 'reverbapp-read-only';
GRANT SELECT, SHOW VIEW, INSERT, UPDATE, DELETE, DROP, CREATE, ALTER ON reverbapp.* 
      TO 'reverbapp-read-write';
      
FLUSH PRIVILEGES;

--
-- done
--


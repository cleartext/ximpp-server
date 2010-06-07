CREATE TABLE subscribers(
    user VARCHAR(250) NOT NULL,
    subscriber VARCHAR(250) NOT NULL,
    PRIMARY KEY (user, subscriber)
) ENGINE=InnoDB, CHARSET=utf8;

-- add jid and presence fields
ALTER TABLE users ADD jid VARCHAR(255) DEFAULT '', ADD presence BOOLEAN DEFAULT FALSE;
UPDATE users SET jid = concat(username, '@coolbananas.com.au');
CREATE UNIQUE INDEX by_jid ON users (jid);

-- Table to store realtime searches
CREATE TABLE search_terms (
    term VARCHAR(255) NOT NULL,
    username VARCHAR(250) NOT NULL,
    PRIMARY KEY (term, username)
) ENGINE=InnoDB, CHARSET=utf8;

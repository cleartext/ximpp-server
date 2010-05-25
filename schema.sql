CREATE TABLE subscribers(
    user VARCHAR(250) NOT NULL,
    subscriber VARCHAR(250) NOT NULL,
    PRIMARY KEY (user, subscriber)
);

-- add jid and presence fields
ALTER TABLE users ADD jid VARCHAR(255) DEFAULT '', ADD presence BOOLEAN DEFAULT FALSE;
UPDATE users SET jid = concat(username, '@coolbananas.com.au');
CREATE UNIQUE INDEX by_jid ON users (jid);

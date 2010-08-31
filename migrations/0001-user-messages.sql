CREATE TABLE tweets(
    id INTEGER NOT NULL AUTO_INCREMENT,
    username VARCHAR(250) NOT NULL,
    text TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id)
) ENGINE = InnoDB, CHARSET=utf8;

CREATE INDEX by_user ON tweets (username);

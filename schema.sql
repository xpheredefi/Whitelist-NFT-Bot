CREATE TABLE IF NOT EXISTS discord_server (
    id INTEGER PRIMARY KEY,
    whitelist_channel INTEGER UNIQUE,
    whitelist_role INTEGER UNIQUE,
    blockchain TEXT
);

CREATE TABLE IF NOT EXISTS user (
    id INTEGER NOT NULL,
    discord_server NOT NULL,
    wallet TEXT,
    PRIMARY KEY (id, discord_server),
    FOREIGN KEY (discord_server) REFERENCES discord_server (id) 
        ON DELETE CASCADE ON UPDATE NO ACTION
);
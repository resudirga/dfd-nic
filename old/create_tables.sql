.open NICA.db

PRAGMA encoding=utf8;

CREATE TABLE IF NOT EXISTS Places
(   placeid     INTEGER     PRIMARY KEY,        -- This is an autogenerating key
    name        TEXT,
    lat         REAL     NOT NULL,
    lng         REAL     NOT NULL,
    source      TEXT     NOT NULL,
    date_retrieved TEXT  NOT NULL,
    address     TEXT,
    streetnumber   TEXT,
    streetname  TEXT,
    citytown    TEXT,
    province    TEXT,
    postalcode  TEXT,
    phonenum    TEXT,
    website     TEXT,
    permanently_closed INTEGER,
    vicinity    TEXT,
    owner       TEXT,
    google_rating INTEGER
);

CREATE TABLE IF NOT EXISTS Reviews
(   placeid     INTEGER   NOT NULL,
    author_name TEXT,
    user_rating INTEGER,
    text        TEXT,
    review_time TEXT,
    lang      TEXT,
    PRIMARY KEY (placeid, author_name),
    FOREIGN KEY(placeid) REFERENCES Places(placeid) 
      ON DELETE CASCADE
      ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS AmenityTypes
(   placeid     INTEGER     NOT NULL,
    amtype      TEXT     NOT NULL,
    source      TEXT     NOT NULL,
    PRIMARY KEY(placeid, amtype),
    FOREIGN KEY(placeid) REFERENCES Places(placeid)
      ON DELETE CASCADE
      ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS GoogleMetadata
(   id      INTEGER  UNIQUE,
    google_id TEXT PRIMARY KEY,
    url     TEXT,
    idscope TEXT, 
    FOREIGN KEY(id) REFERENCES Places(placeid) 
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS OSMMetadata
(   id           INTEGER  NOT NULL  UNIQUE,
    nodeid       TEXT  PRIMARY KEY,
    datatime     TEXT,
    author       TEXT,
    authorid     TEXT,
    version      TEXT,
    changeset    TEXT,
    FOREIGN KEY(id) REFERENCES Places(placeid) 
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

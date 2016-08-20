CREATE TABLE IF NOT EXISTS servers
(
  serverid INTEGER PRIMARY KEY,
  ipaddr TEXT NOT NULL,
  port INTEGER NOT NULL,
  gs_steamid INTEGER DEFAULT NULL UNIQUE,
  master_update INTEGER DEFAULT (strftime('%s', 'now'))
);

CREATE TABLE IF NOT EXISTS server_info
(
  serverid INTEGER PRIMARY KEY,
  info_update INTEGER DEFAULT (strftime('%s', 'now')),
  server_info BLOB
);
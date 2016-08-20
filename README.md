Team Fortress 2 Community Quickplay Browser
-------------------------------------------

This is the open-source project for the Community Quickplay project (*Project Silkworm*).


## Setting up

The project is designed to be relatively simple to run.  Maybe.  The setup is hacky, but
it should be doable.

1. Install the external software libraries:
  * Required:
    * `flup3`, a FastCGI server library that supports Python3.
      * `pip install flup==1.0.3.dev20151210`
	* `sqlite3`, for the database.
    * `python-valve`, a library to perform master server queries.
    * `SourceLib`, a library to deal with receiving data from `A2S_INFO` requests.
      We use this for server queries in place of `python-valve` because the latter doesn't
      support extra data flags.  (TODO test if [kradalby's fork][sl-fork] works)
    * `geoip2` (Python), library that can loop up IP addresses and get approximate location.
      (This is used to get approximate distance from server.)
    * `libmaxminddb`, a C extension for optimal speed in `geoip2` lookups.
    * `GeoLite2-City.mmdb`, the database used for the geoip lookups.
    * `nginx`, serves web content.  I use it for front-line FastCGI caching, but if you know
      your way around dealing with FastCGI on other software, go for it.
2.  Dive into `bin/CommunityQuickplay/Database.py` and change the URI for the database as
	needed.  It's a bit of a pain, but I'd like to push this out today and I'm too tired to
	figure out how to change it.
3.  Create the SQLite database in the appropriate directory with `db/database.sql`.
4.  `cd` into the `bin` directory and run `./master_query.py` to populate the database with
	valid servers.
5.	Run `./server_service.py` to start the FastCGI service.
6.	Configure `nginx` to fastcgi_pass `/get_servers`, and `/server` to the socket.

[sl-fork]: https://github.com/kradalby/SourceLib
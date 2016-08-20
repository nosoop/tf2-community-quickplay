#!/usr/bin/python3

import sqlite3, time, sys

# conn = sqlite3.connect(':memory:')
conn = sqlite3.connect('database_production.sq3')
conn.row_factory = sqlite3.Row

cursor = conn.cursor()

for row in cursor.execute('SELECT * FROM servers'):
	print(dict(row))

conn.commit()
conn.close()
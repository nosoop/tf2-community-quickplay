import sqlite3, time
from CommunityQuickplay.Config import Config

SERVER_UPDATE_OLDEST = 60 * 60 * 8

class Database:
	def __init__(self):
		# self.connection = sqlite3.connect('/srv/quickplay.www/db/database_production.sq3')
		self.connection = sqlite3.connect(Config()['databases']['sqlite'], uri=True)
		self.connection.row_factory = sqlite3.Row
		self.cursor = self.connection.cursor()
	
	def get_ip_port_for_server(self, serverid):
		self.cursor.execute('SELECT ipaddr, port FROM servers WHERE serverid = ?;', (serverid,))
		result = self.cursor.fetchone()
		return (result['ipaddr'], result['port']) if result is not None else (None, None)
	
	def server_master_entry_update(self, ipaddr, port, gs_steamid):
		if gs_steamid is not None:
			# server with gs_steamid already has row, update based on that
			self.cursor.execute('UPDATE servers SET ipaddr = ?, port = ?, master_update = ? WHERE gs_steamid = ?;', (ipaddr, port, int(time.time()), gs_steamid))
		else:
			# try to update anonymous server row based on ipaddr, port
			self.cursor.execute('UPDATE servers SET master_update = ? WHERE ipaddr = ? AND port = ? AND gs_steamid IS NULL;', (int(time.time()), ipaddr, port))
		
		# there doesn't seem to be any entries that got updated, so let's put a new one in
		if (self.cursor.rowcount == 0):
			self.cursor.execute('INSERT INTO servers(ipaddr, port, gs_steamid) SELECT ?, ?, ?;', (ipaddr, port, gs_steamid))
	
	def get_current_server_list(self, access_time = -1):
		if access_time == -1:
			access_time = int(time.time())
		
		oldest_entry_time = access_time - SERVER_UPDATE_OLDEST
		self.cursor.execute('SELECT serverid FROM servers WHERE master_update >= ?', (oldest_entry_time,))
		
		while True:
			row = self.cursor.fetchone()
			
			if row is None:
				break
			
			yield row['serverid']

	def get_ip_port_server_list(self, offset=0, limit=50, access_time=-1):
		if access_time == -1:
			access_time = int(time.time())
		oldest_entry_time = access_time - SERVER_UPDATE_OLDEST

		self.cursor.execute(
			'SELECT ipaddr, port FROM servers WHERE master_update >= ? ORDER BY serverid LIMIT ? OFFSET ?',
			(oldest_entry_time, limit, offset)
		)

		return self.cursor.fetchall()
	
	def get_server_info_by_id(self, serverid):
		pass
	
	def commit(self):
		self.connection.commit()
	
	def close(self):
		self.connection.close()

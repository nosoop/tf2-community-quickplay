#!/usr/bin/python3

"""
A script that pokes the master server list and stores active servers in a database.
Preferably run via crontab.
"""

import sys, socket

# python-valve project
import valve.source.a2s
import valve.source.master_server
import valve.source.util

'''
SourceLib's A2S_INFO implementation supports EDF for game tags, so we'll use that.
We have our own port of SourceLib.SourceQuery, as the main branch is only 2.x and kradalby's
build doesn't seem to do A2S_RULES for some strange reason
'''
# from SourceLib.SourceQuery import SourceQuery

from CommunityQuickplay.Database import Database
from CommunityQuickplay.GameServerInfo import GameServerInfo

servers = set()

msq = valve.source.master_server.MasterServerQuerier()

try:
	addr_hundred = 0
	for address in msq.find(gamedir=u"tf", secure=True,
			type=valve.source.util.ServerType.DEDICATED):
		servers.add(address)
except valve.source.a2s.NoResponseError:
	print("Master server request timed out!", file=sys.stderr)

print('{} servers to query, hoo boy'.format(len(servers)))

db = Database()

server_count = 0

for connect_info in servers:
	# TODO if last server query was less than {time} then just set the master query time to that?
	
	try:
		server = GameServerInfo(*connect_info)
		# TODO use SourceLib/SourceQuery 
		# server = valve.source.a2s.ServerQuerier(connect_info)
		
		response = server.get()
		
		if response['eligible']:
			server = response['server']
			# TODO update server list with time
			print('{} {}/{} {}'.format(connect_info, server['human_players'],
					server['max_players'], server['hostname'].encode('utf8')))
			
			serverid = response.get('gs_steamid', None)
			
			address, port = connect_info
			db.server_master_entry_update(address, port, serverid)
			
			server_count += 1
			
			# safety saves
			if server_count % 20 == 0:
				db.commit()
	except (valve.source.a2s.NoResponseError, NotImplementedError, socket.timeout,
			ConnectionRefusedError, socket.error) as e:
		# print('server at {} failed to respond'.format(address))
		pass
	except (UnicodeDecodeError) as e:
		# for some reason there's at least one server in asia ('182.211.115.149', 27015) that
		# PHP-Source-Server-Query, python-valve, and SourceLib are unable to read
		pass

db.commit()
db.close()
print('{} servers successfully queried'.format(server_count))
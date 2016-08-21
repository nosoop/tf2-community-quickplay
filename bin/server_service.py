#!/usr/bin/env python3

# standalone web-available server query script
# just fastcgi_pass the socket and you're good to go, none of that install 5 bigass frameworks nonsense

"""
location = /server {
	include fastcgi_params;
	fastcgi_pass unix:/tmp/quickplay.sock;
}
"""

# python3, so we need flup3: https://github.com/chxanders/flup3
# pip3 install flup==1.0.3.dev20151210
from flup.server.fcgi import WSGIServer

from cgi import escape

import json, urllib, time, queue, threading
# import database_funcs

from CommunityQuickplay.Database import Database
from CommunityQuickplay.Config import Config
from CommunityQuickplay.GameServerInfo import GameServerInfo

def app(environ, start_response):
	
	# yield 'Hello World\n'
	# yield environ.get('QUERY_STRING', '')
	
	# server = ("pika.nom-nom-nom.us", 27015)
	# yield json.dumps(server_query.server_query(*server), indent=4)
	
	#for k, v in sorted(environ.items()):
	#	yield '{} -- {}\n'.format(escape(k), escape(v))
	
	script = environ['SCRIPT_NAME']
	query = urllib.parse.parse_qs(environ['QUERY_STRING'])
	
	#for k, v in query.items():
	#	yield '{} -- {}\n'.format(escape(k), escape(str(v)))
	
	if script == '/server':
		# cache results for two minutes
		start_response('200 OK', [('Content-Type', 'text/json'), ('Cache-Control', 'max-age=120')])
		
		serverid = query['serverid'][0] if 'serverid' in query and len(query['serverid']) > 0 else None
		
		host = query['host'][0] if 'host' in query and len(query['host']) > 0 else None
		port = int(query['port'][0]) if 'port' in query and len(query['port']) > 0 else None
		
		extdata = True if 'extdata' in query else False
		
		response = None
		
		if serverid is not None:
			# response = GameServerEntry(serverid).query()
			db = Database()
			connect_info = db.get_ip_port_for_server(serverid)
			db.close()
			
			response = GameServerInfo(*connect_info, extdata=extdata).get()
		else:
			response = GameServerInfo(host, port, extdata=extdata).get()
		
		yield json.dumps(response, indent = 4)
	elif script == '/server_list':
		start_response('200 OK', [('Content-Type', 'text/json'), ('Cache-Control', 'max-age=60')])

		limit = 50
		offset = 0
		extdata = True if 'extdata' in query else False
		response = { 'success': False, 'servers': [] }

		if 'limit' in query:
			limit = query['limit'][0]
		if 'offset' in query:
			offset = query['offset'][0]

		db = Database()

		# Here, we get an array of IP:Port tuples.
		server_list = db.get_ip_port_server_list(offset, limit)

		threads = Config()['query_threads']

		query_q = queue.Queue()
		result_q = queue.Queue()

		# This is the function that will be the worker threads
		def query_thread(i, q):
			while True: # Loop until forever (until killed)
				job = None
				try:
					job = q.get(timeout=3) # Get some work from the queue
				except queue.Empty: # Make sure threads exit if no work is left.
					break
				server_info = GameServerInfo(*job, extdata=extdata).get()
				result_q.put(server_info)
				q.task_done()

		# Launch our worker therads.
		for i in range(threads):
			q_thread = threading.Thread(target=query_thread, args=(i, query_q))
			q_thread.setDaemon(True)
			q_thread.start()

		# Place all servers in the query queue
		for server in server_list:
			query_q.put(server)

		# Wait for all therads to finish
		query_q.join()

		# Fetch everything from the result queue and make a pretty list
		while True:
			try:
				s = result_q.get_nowait()
				response['servers'].append(s)
			except queue.Empty:
				break
		
		#response['servers'] = server_list
		response['count'] = len(server_list)
		response['success'] = True

		yield json.dumps(response, indent = 4)

	elif script == '/get_servers':
		start_response('200 OK', [('Content-Type', 'text/json'), ('Cache-Control', 'max-age=10')])
		
		response = { 'success': False, 'ids': [] }
		
		db = Database()
		for serverid in db.get_current_server_list():
			response['ids'].append(serverid)
		db.close()
		
		response['num_servers'] = len(response['ids'])
		response['success'] = True
		
		yield json.dumps(response)

socket = Config()['socket']

print('Created FastCGI socket at {}'.format(socket))
#WSGIServer(app, bindAddress=socket, umask=0o011).run()
WSGIServer(app, bindAddress=('0.0.0.0', 9000), umask=0o011).run()

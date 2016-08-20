from .Config import Config
from SourceLib.SourceQuery import SourceQuery

from .GeoIPReader import GeoIPReader

import socket, time

filter = Config()['filters']
reader = GeoIPReader()

def valid_ipaddr(addr):
	try:
		socket.inet_aton(addr)
		return True
	except socket.error:
		return False

def valid_hostname(dn):
	try:
		# add period to hostname https://secure.php.net/manual/en/function.gethostbyname.php#111684
		socket.gethostbyname(dn + '.' if not dn.endswith('.') else dn)
		return True
	except socket.error:
		return False

def valid_host(host):
	return valid_ipaddr(host) or valid_hostname(host)

def info_filtered(info):
	'''
	Here's how we do the filtering:
	1.  Drop password-protected servers
	2.  Drop non-TF2 servers (server might've changed games after a successful master query)
	3.  Drop gamemodes listed in description
	4.  Drop servers containing specific map prefixes
	5.  Drop servers containing any of the restricted tags
	'''
	if info is None:
		return True
	
	map = info['map'].lower()
	if 'workshop/' in info["map"]:
		map = info['map'][9: info['map'].find('.')]
	
	if not map.startswith(filter['allowed_map_prefixes']):
		return True
	
	return (info['passworded'] == True
			or info['appid'] != 440
			or info['gamedesc'].lower().startswith(filter['gamedesc'])
			or map.lower().startswith(filter['map_prefixes'])
			or ('tag' in info and contains_filtered_tag(info['tag']))
			or info['hostname'].startswith(filter['hosts'])
			)

def contains_filtered_tag(tag_string):
	return len(filter['tags'].intersection(tag_string.lower().split(','))) > 0

server_tags_allowed = frozenset(Config()['passthrough']['tags'])

class GameServerInfo:
	'''
	An object that returns data based on host / port.
	Basically spits out the same dict that is returned in JSON form on server query.
	'''
	def __init__(self, host, port, extdata = False):
		self.__host = host
		self.__port = port if port is not None else 27015
		self.__extdata = extdata
	
	def get(self):
		'''
		Retrieves the server info.
		My head hurts.  This code is a mess.
		
		TODO streamline code
		'''
		server = (self.__host, self.__port)
		
		output = {
			'success': False,
		}

		if self.__host is None or not valid_host(self.__host):
			output['message'] = "Host does not resolve to a valid IP address."
		else:
			try:
				query = SourceQuery(*server)
				query.connect()
				
				output['eligible'] = False
				
				info = query.info()
				
				rules = []
				
				if not self.__extdata:
					if info_filtered(info):
						query.disconnect()
						return output
					
					rules = query.rules()
					
					# todo filter servers based on rules
					
					# filter out servers that are in the matchmaking system
					# in case one of the existing listings turned into a Valve-hosted MM server
					if rules is None or int(float(rules.get('tf_mm_servermode', 0))) == 1:
						query.disconnect()
						return output
					
					if len(filter['convars'].intersection(rules.keys())) > 0:
						query.disconnect()
						return output
					
					if 'tag' not in info:
						query.disconnect()
						return output
					
					output['eligible'] = True
				else:
					rules = query.rules()
				
				tags = info['tag'].lower().split(',')
				
				result = {
					"hostname": info['hostname'].replace("\x01", '').strip(),
					"connect": '{}:{}'.format(*server),
					"tags": [],
					"map": info["map"],
					
					"human_players": info["numplayers"] - info["numbots"],
					"max_players": info["maxplayers"],
					"bots": info["numbots"]
				}
				
				# quick hack to clean up display names
				if 'workshop/' in info["map"]:
					result['map'] = info['map'][9: info['map'].find('.')]
				
				result['tags'] = set(server_tags_allowed.intersection(tags))
				
				if ('HLstatsX:CE'.lower() in tags
						or 'gameme_plugin_version' in rules):
					result['tags'].add('stats')
				
				if ('sm_motdgd_version' in rules or 'sm_pinion_adverts_version' in rules):
					result["tags"].add('advertisements');
				
				if ('sourcemod_version' not in rules and 'metamod_version' not in rules):
					result["tags"].add('vanilla');
				
				if (int(rules.get('tv_enable', 0)) != 0 and int(rules.get('tv_password', 1)) == 0):
					result['tags'].add('sourcetv')
				
				if (int(rules.get('tfh_halloween', 0)) == 1 or int(rules.get('tfh_fullmoon', 0)) == 1):
					result['tags'].add('halloween')
				
				nextmap = rules.get('sm_nextmap', rules.get('nextlevel', None))
				if (nextmap is not None and nextmap == info['map']):
					result['tags'].add('24/7')
				
				if 'sm_classrestrict_version' in rules:
					result['tags'].add('class limits')
				
				# _registered means eligible for quickplay?
				
				# get steamid for server
				if ('steamid' in info):
					if (info['steamid'] & 0x0130000000000000 == 0x0130000000000000):
						# the server has a registered GSLT
						result['gs_steamid'] = info['steamid'] & 0xFFFFFFFF
					if (info['steamid'] & 0x0140000000000000 == 0x0140000000000000):
						# instance is shared between many servers?
						# result['anon_instance'] = (info['steamid'] >> 4 * 8) & 0xFFFF
						
						# anonymous servers don't keep steamids between restarts
						# can't use it as an identifier
						# result['anon_serverid'] = info['steamid'] & 0xFFFFFFFF
						# formatted as '[A:1:{}:{}]'.format(anon_serverid, anon_instance)
						pass
				
				result['tags'] = list(result['tags'])
				result['query_time'] = int(time.time())
				
				if self.__extdata:
					result['info'] = info
					result['rules'] = rules
				
				response = reader.city(self.__host)
												
				result['geoip'] = {
					"coords": [ response.location.latitude, response.location.longitude ],
					"region": response.continent.code 
				}
				
				location_region = response.subdivisions.most_specific.name
				location_country = response.country.name
				
				if location_region is not None:
					result['geoip']['location'] = '{}, {}'.format(location_region, location_country)
				else:
					result['geoip']['location'] = '{}'.format(location_country)

				
				output["server"] = result
				output["success"] = True
				
			except (socket.error) as e:
				pass
			finally:
				query.disconnect()
		
		return output

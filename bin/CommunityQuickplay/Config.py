import json, os

# location relative to 'bin/'
json_location = '../config.json'

class Config(dict):
	'''
	Creates a shared read-only dict that loads its data from a configuration file.
	'''
	
	info = None
	
	def __init__(self):
		if not Config.info:
			json_realpath = os.path.realpath(json_location)
			
			if not os.path.exists(json_realpath):
				print('could not find configuration file (in {})'.format(json_realpath),
						file=sys.stderr)
			
			with open(json_realpath, 'r') as f:
				Config.info = json.load(f)
				self.__mutate()
	
	def __mutate(self):
		'''
		Converts certain dict entries to the preferred types
		'''
		self['filters']['tags'] = frozenset(self['filters']['tags'])
		self['filters']['map_prefixes'] = tuple(self['filters']['map_prefixes'])
		self['filters']['allowed_map_prefixes'] = tuple(self['filters']['allowed_map_prefixes'])
		self['filters']['gamedesc'] = tuple(self['filters']['gamedesc'])
		self['filters']['convars'] = frozenset(self['filters']['convars'])
		self['filters']['hosts'] = tuple(self['filters']['hosts'])
	
	def __getitem__(self, key):
		return Config.info[key]
	
	def get(self, key, default=None):
		return Config.info.get(key, default)
import geoip2.database, socket

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


class GeoIPReader:
	'''
	Creates a shared GeoIP2 Reader instance.
	'''
	
	reader = geoip2.database.Reader('/srv/quickplay.www/db/GeoLite2-City.mmdb')
	
	def __init__(self):
		pass
	
	def city(self, host):
		ipaddr = None
		if valid_ipaddr(host):
			ipaddr = host
		elif valid_hostname(host):
			ipaddr = socket.gethostbyname(host + '.' if not host.endswith('.') else host)
		else:
			return None
		return GeoIPReader.reader.city(ipaddr)
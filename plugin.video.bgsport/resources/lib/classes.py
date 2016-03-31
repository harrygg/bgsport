# -*- coding: utf-8 -*-
import sys, os, re, sqlite3, requests, gzip, urllib2
from xbmcswift2 import xbmc

reload(sys)
sys.setdefaultencoding('utf8')

### Class Categories
class Category:

	def __init__(self, attr):
		self.id = attr[0]
		self.name = attr[1]
		self.parent_id = attr[2]

### Class Helper
class Helper:
	
	db_file_name = 'assets.db'

	def __init__(self, plugin):
		self.plugin = plugin
		self.local_db = os.path.join(plugin.storage_path, self.db_file_name)

	def check_assets(self):
		#Check whether the assets file is old
		try:
			from datetime import datetime, timedelta
			if os.path.exists(self.local_db):
				treshold = datetime.now() - timedelta(hours=6)
				fileModified = datetime.fromtimestamp(os.path.getmtime(self.local_db))
				if fileModified < treshold: #file is more than a day old
					self.download_assets()
			else: #file does not exist, perhaps first run
					self.download_assets()
		except Exception, er:
			self.plugin.log.error(er)
			xbmc.executebuiltin('Notification(%s,%s,10000,%s)' % (self.plugin.name,'Неуспешно сваляне на най-новата база данни',''))
			assets = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../storage/%s.gz' % self.db_file_name)
			self.extract(assets)
	
	def download_assets(self):
		try:
			remote_db = 'http://github.com/harrygg/bgsport/blob/master/%s/resources/storage/%s.gz?raw=true' % (self.plugin.id, self.plugin.db_file_name)
			self.plugin.log.info('Downloading assets from url: %s' % remote_db)
			save_to_file = self.local_db if '.gz' not in remote_db else self.local_db + ".gz"
			f = urllib2.urlopen(remote_db)
			with open(save_to_file, "wb") as code:
				code.write(f.read())
			self.extract(save_to_file)
		except Exception, er:
			self.plugin.log.error(er)
			raise

	def extract(self, path):
		try:
			gz = gzip.GzipFile(path, 'rb')
			s = gz.read()
			gz.close()
			out = file(self.local_db, 'wb')
			out.write(s)
			out.close()
		except:
			raise

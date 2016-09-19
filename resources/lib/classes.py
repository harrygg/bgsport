# -*- coding: utf-8 -*-
import sys, os, re, sqlite3, requests, gzip, urllib2, base64
from StringIO import StringIO
from bs4 import BeautifulSoup
from xbmcswift2 import xbmc
import urlresolver


reload(sys)
sys.setdefaultencoding('utf8')

### Class Categories
class CategoryExt:
	def __init__(self, name, **kwargs):
		self.name = name
		default_attr = dict(id=0, parent_id=0, has_children=False, url='', disabled=False, thumb='')
		more_allowed_attr = []
		allowed_attr = list(default_attr.keys()) + more_allowed_attr
		default_attr.update(kwargs)
		self.__dict__.update((k,v) for k,v in default_attr.iteritems() if k in allowed_attr)
		
class Category:
	def __init__(self, attr):
		self.id = attr[0]
		self.name = attr[1]
		self.parent_id = attr[2]
		try: self.has_children = True if attr[3] == 1 else False
		except: self.has_children = False
		try: self.disabled = True if attr[4] == 1 else False
		except: self.disabled = True
		try: self.url = attr[5]
		except: self.url = ''

class Stream:
	def __init__(self, attr):
		self.id = attr[0]
		self.category_id = attr[1]
		self.name = attr[2]
		self.url = attr[3]
		try: self.disabled = attr[4]
		except: self.disabled = False
		try: self.thumb = attr[5]
		except: self.thumb = ''

class StreamExt:
	def __init__(self, name, **kwargs):
		self.name = name
		default_attr = dict(id=0, category_id=0, url='', disabled=0, thumb='')
		more_allowed_attr = []
		allowed_attr = list(default_attr.keys()) + more_allowed_attr
		default_attr.update(kwargs)
		self.__dict__.update((k,v) for k,v in default_attr.iteritems() if k in allowed_attr)

class Pagination:
	def __init__(self, url):
		try:
			import urlparse, urllib
			p = urlparse.urlparse(url)
			query = urlparse.parse_qs(p.query)
			try: 
				page = int(query['page'][0]) + 1
				query['page'][0] = str(page)
			except:
				page = int(query['start'][0]) + 1
				query['start'][0] = str(page)
				
			url = urlparse.ParseResult(p.scheme, p.netloc, p.path, p.params, urllib.urlencode(query, True), p.fragment).geturl()
			self.next_page = CategoryExt('Следваща страница >>>', url=url)
		except Exception, er:
			self.next_page = False
			#matches = re.compile('page=(\d+)').findall(url)
			#if len(matches) > 0:
			#	page = int(matches[0]) + 1
			#	url = url.replace(matches[0], str(page))
			#self.next_item = CategoryExt('Следваща страница >>>', url=url)
			pass

class Assets:
	db_file_name = 'assets.db'
	debug = True
	#TODO remove this for release version
	debug_db_file = 'C:\\Users\\genevh\\Documents\\Kodi\\BG Sport\\%s' % db_file_name
	delta = 6 #hours
	
	def __init__(self, plugin):
		self.plugin = plugin
		self.local_db = os.path.join(plugin.storage_path, self.db_file_name)
		self.check_assets()

	#Check whether the db file is old
	def check_assets(self):
		#Check whether the assets file is old
		try:					
			if self.debug:
				from shutil import copyfile
				copyfile(self.debug_db_file, self.local_db)
				return
			from datetime import datetime, timedelta
			if os.path.exists(self.local_db):
				treshold = datetime.now() - timedelta(hours=self.delta)
				fileModified = datetime.fromtimestamp(os.path.getmtime(self.local_db))
				if fileModified < treshold:
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
		
class Request():

	response = ''

	def __init__(self, url, is_mobile = False):
		user_agent = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'
		if is_mobile == True:
			user_agent = 'Mozilla/5.0 (Linux; Android 5.0.2; bg-bg; SAMSUNG GT-I9195 Build/JDQ39) AppleWebKit/535.19 (KHTML, like Gecko) Version/1.0 Chrome/18.0.1025.308 Mobile Safari/535.19' 
			
		req = urllib2.Request(url)
		req.add_header('Accept-Encoding', 'gzip')
		req.add_header('User-Agent', user_agent)
		res = urllib2.urlopen(req)
		self.response = self.parse_gzip(res)
		
		
	def parse_gzip(self, res):
		if res.info().get('Content-Encoding') == 'gzip':
			buf = StringIO(res.read())
			f = gzip.GzipFile(fileobj = buf)
			return f.read()
		else:
			return res.read()


### Class Helper
class Helper:
	def __init__(self, plugin):
		self.plugin = plugin
		
	def get_bg_foobtall_games(self):
		
		def translate(string):
			temp = ''
			try:
				temp = string.replace('&ndash;', '-')
				#temp = re.sub(r'', int(), temp, max=0)
				temp = temp.replace('at ', '')
			except: pass
			return temp 
			
		def format_name(time, title):
			return '[B]%s[/B] | [COLOR white]%s[/COLOR]' % (translate(time), translate(title))
			
		fixtures = []
		try:
			#url = 'http://play.gong.bg/fixture/index/1'
			url = 'http://livetv.sx/en/allupcomingsports/1/'
			r = Request(url)
			
			matches = re.compile('Bulgarian\s(?:A\s+PFG|Cup).*?<a.*?href="(.+?)Bulgarian', re.DOTALL).findall(r.response)
			for match in matches:
				if 'class="live"' not in match:
					times = re.compile('evdesc">(.+)\s+').findall(match)
					details = re.compile('(.*?)">(.+?)</a>').findall(match)
					name = format_name(times[0], details[0][1])
					cat = Category([0, name, 15])
					cat.url = 'http://livetv.sx/' + details[0][0]
					#cat.url = 'http://livetv.sx/en/eventinfo/403053_waratahs_rebels/'
					fixtures.append(cat)
			
			#soup = BeautifulSoup(response, 'html5lib')
			
			#dates = soup.find_all(P, class_='date-info')
			#hours = soup.find_all(P, class_='time-info')
			#titles = soup.find_all(A, class_='btn-table')

			#if len(dates) == len(hours) and len(hours) == len(titles):
			#	for i in range(0, len(dates)):
			#		title = '[B]%s %s[/B] | [COLOR white]%s[/COLOR]' % ( dates[i].get_text()[:9], hours[i].get_text(), titles[i]['title'] )
			#		fixtures.append([0, title, 15])
				
		except Exception, er:
			self.plugin.log.error(str(er))
		return fixtures

		
		
	def get_stream_from_url(self, url):	
		
		def resolve_web_player_url(url):
			stream = ''
			try:
				r = Request(url)
			except: pass
			return stream
			
		streams = []
		try:			
			
			if 'vbox7' in url:
				return self.get_vbox_clips(url)
			elif 'youtube' in url:
				return self.get_youtube_clips(url)
			elif 'sportal' in url:
				return self.get_sportal_clips(url)
			elif 'football24' in url:
				return self.get_football24_clips(url)
			else:
				r = Request(url)
				acestream_matches = re.compile('acestream://(.+?)["\'\s]+').findall(r.response)
				webplayer_matches = re.compile('href="(.+?webplayer.php\?t.+?)"').findall(r.response)
				
				if len(acestream_matches) == 0 and len(webplayer_matches) == 0:
					streams.append([0, 0, 'Директните предавания са достъпни около 30 минути преди началото.', ''])
				else:
					if acestream_matches > 0:
						for match in acestream_matches:
							playpath = 'plugin://program.plexus/?url=%s&mode=1&name=Acestream' % acestream_matches[0]
							streams.append([0, 0, 'Acestream поток, възпроизвеждане с Plexus', playpath])
					if webplayer_matches > 0:
						matches = webplayer_matches[::2]
						for i in range(0, len(matches)):
							url = ''# resolve_web_player_url(webplayer_matches[i])
							streams.append([0, 0, 'възпроизвеждане', url])
				
		except Exception, er:
			self.plugin.log.error(str(er))
		return streams
	
	def resolve_m3u(self, url):
		try:
			r = Request(url)
			matches = re.compile('(http.*m3u.*?)[\'"\s]+').findall(r.response)
			return matches[0]
		except Exception, er:
			self.plugin.log.error(str(er))
		return ''
	
	def is_resolved(self, url):
		allowed_types = ['ts', 'flv', 'mp4', 'm3u', 'm3u8', 'rtmp', 'program.plexus', 'video.youtube', 'video.vbox7', 'video.free.bgtvs' ]
		for type in allowed_types:
			if type in url:
				return True	
		return False
	
	def get_videos(self, url):
		if 'gong' in url:
			return self.get_vbox_clips(url)
		if 'sportal' in url:
			return self.get_sportal_clips(url)

	
	def get_youtube_clips(self, url):
		items = []
		try:
			r = Request(url, True)
			resp = r.response[4:]
			self.plugin.log.info(resp)
			import json
			data = json.loads(resp)
			is_channel = 'channel' in url
			
			#Get continuation tokens
			try: 
				continuations = data['content']['tab_settings']['available_tabs'][1]['content']['contents'][0]['continuations'][0]
			except:
				try: 
					continuations = data['content']['section_list']['contents'][0]['contents'][0]['continuations'][0]
				except: 
					try: 
						continuations = data['content']['continuation_contents']['continuations'][0]
					except: 
						continuations = None
				
				
			#===================================================================
			# try: continuation = data['content']['tab_settings']['available_tabs'][1]['content']['contents'][0]['continuations'][0]['continuation']
			# except:
			# 	try: continuation = data['content']['section_list']['contents'][0]['contents'][0]['continuations'][0]['continuation']
			# 	except: 
			# 		try: continuation = data['content']['continuation_contents']['continuations'][0]['continuation']
			# 		except: continuation = None
			# 		
			# try: click_tracking = data['content']['tab_settings']['available_tabs'][1]['content']['contents'][0]['continuations'][0]['click_tracking_params']
			# except:
			# 	try: click_tracking = data['content']['section_list']['contents'][0]['contents'][0]['continuations'][0]['click_tracking_params']
			# 	except:
			# 		try: click_tracking = data['content']['continuation_contents']['continuations'][0]['click_tracking_params'] 
			# 		except: click_tracking = None
			#===================================================================
				
			try: data = data['content']['tab_settings']['available_tabs'][1]['content']['contents'][0]['contents']
			except:
				try: data = data['content']['section_list']['contents'][0]['contents'][0]['contents']
				except: data = data['content']['continuation_contents']['contents']

			for d in data:
				title = d['title']['runs'][0]['text']
				
				try: views = d['view_count']['runs'][0]['text']
				except:	views = ''

				try: length = d['length']['runs'][0]['text']
				except: length = ''
							
				try: thumb = d['thumbnail_info']['url']
				except:
					try: thumb = 'http:' + d['thumbnail']['url']
					except: thumb = ''
				
				try: 	url = d['encrypted_id']
				except: url = d['video_id']

				url = 'plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=' + url
				title = '%s - %s (%s)' % (title, length, views)
				#strm = Stream(0, 0, title + ' ' + views, url])
				strm =  StreamExt( title, url=url, thumb=thumb)
				items.append(strm)
				
			if continuations != None:
				if is_channel:
					url = 'https://m.youtube.com/channel/UCl5a4nVdpmdyX6ZgQQnF96Q?action_continuation=1&ajax=1&ctoken=%s&itct=%s&layout=mobile&tsp=1&utcoffset=180'
				else:
					url = 'https://m.youtube.com/playlist?action_continuation=1&ajax=1&ctoken=%s&itct=%s&layout=mobile&list=PLQUOZJypzKHzUR85PQDvnO6jsK2Axisnr&tsp=1&utcoffset=180'
	
				ctoken = continuations['continuation']
				itct = continuations['click_tracking_params']
			
				url = url % (ctoken, itct)
				cat = CategoryExt('Следваща страница >>>', url=url)
				items.append(cat)

		except Exception, er:
			self.plugin.log.error(str(er))
			#items.append(StreamExt('Няма намерени видео потоци'))
		return items
		
		
	def get_vbox_clips(self, url):
		
		items = []
		try:
			r = Request(url, True)
			soup = BeautifulSoup(r.response.decode('utf-8', 'ignore'), 'html5lib')
			#self.plugin.log.info(r.response)
			thumbs = soup.find_all(div, class_='video-thumb')
			titles = soup.find_all(A, class_='video-info-title')
			urls = soup.find_all(div, class_='video-popup-btn')
			durations = soup.find_all(span, class_='vt-duration')
			#thumbs = re.compile('video-thumb(.*?)</div', re.DOTALL).findall(r.response)
			#titles = re.compile('video-info-title.*?>(.*?)</a',  re.DOTALL).findall(r.response)
			
			#matches = self.find_regex('a.*href=\"/play:([0-9a-zA-Z]{10})\".*img.*src=\"(.*?)\".*alt=\"(.*?)\"')
			if len(titles) == len(urls):
				for i in range(0, len(titles)):
					title = titles[i].get_text()
					try: title = durations[i].get_text() + ' | ' + title 
					except: pass
					id = urls[i]['data-mdkey']
					strm = StreamExt(title)
					strm.url = 'plugin://plugin.video.vbox7/?mode=2&url=%s' % id
					try: strm.thumb =  'http:' + thumbs[i].a.img[src]
					except: strm.thumb = ''
					items.append(strm)
				
				# Pagination
				pg = Pagination(url)
				if pg.next_page:
					items.append(pg.next_page)

		except Exception, er:
			self.plugin.log.error(str(er))
		return items

	def get_sportal_clips(self, url):			
		items = []
		try:
			r = Request(url, True)
			soup = BeautifulSoup(r.response.decode('utf-8', 'ignore'), 'html5lib')
			
			if 'video.php' in url: #If we are resolving sportal embedded videos
				iframe = soup.iframe[src]
				hmf = urlresolver.HostedMediaFile(url=iframe)
				#plugin.log.info("sources len: " + str(len(sources)))
				#source = urlresolver.choose_source(hmf)
				stream_url = hmf.resolve()
				if stream_url:
					items.append(StreamExt('Възпроизвеждане от ' + hmf._host, url=stream_url))
				else:
					items.append(StreamExt('Неуспешно извличане на видео поток.'))

			else:
				links = soup.find_all(A)
				imgs = soup.find_all(IMG)
				titles = soup.find_all(B)
				
				if len(links) > 0 and len(links) == len(titles):
					for i in range(0, len(links)):
						stream_url = links[i][HREF]
						title = titles[i].get_text()
						img = imgs[i][src]
						if 'mp4' in stream_url:
							item = StreamExt(title, url=stream_url, thumb=img)
						else: # Add category
							item = CategoryExt(title, url='http://mobile.sportal.bg/' + stream_url, thumb=img)
						items.append(item)
						
				# Pagination
				pg = Pagination(url)
				if pg.next_page:
					items.append(pg.next_page)
					
		except Exception, er:
			self.plugin.log.error(str(er))
		return items

	def get_football24_clips(self, url):
		items = []
		try:
			r = Request(url, True)
			soup = BeautifulSoup(r.response.decode('utf-8', 'ignore'), 'html5lib')
			
			if 'video_id' in url: #If we are resolving sportal embedded videos
				iframe = soup.iframe[src]
				hmf = urlresolver.HostedMediaFile(url=iframe)
				#plugin.log.info("sources len: " + str(len(sources)))
				#source = urlresolver.choose_source(hmf)
				stream_url = hmf.resolve()
				if stream_url:
					items.append(StreamExt('Възпроизвеждане от ' + hmf._host, url=stream_url))
				else:
					items.append(StreamExt('Неуспешно извличане на видео поток.'))

			else:
				container = soup.find(div, class_='videos')
				links = container.find_all(A, class_='video')
				imgs = container.find_all(IMG)
				titles = container.find_all(span, class_='title')
				
				if len(links) > 0 and len(links) == len(titles):
					for i in range(0, len(links)):
						stream_url = links[i][HREF]
						title = titles[i].get_text()
						img = imgs[i][src]
						item = CategoryExt(title, url='http://football24.bg/' + stream_url, thumb=img)
						items.append(item)
						
				# Pagination
				pg = Pagination(url)
				if pg.next_page:
					items.append(pg.next_page)
					
		except Exception, er:
			self.plugin.log.error(str(er))
		return items

	def get_bgsport_streams(self):
		streams = []
		try:
			#Volleyball
			sources = [{'name':'Волейбол', 'channels':[{'name':'BNT HD', 'epg_url':'http://smart.dir.bg/tv/292'}]}]
			for source in sources:
				for channel in source['channels']:
					r = Request(channel['epg_url'], True)
					#self.plugin.log.info(r.response)
					soup = BeautifulSoup(r.response.decode('utf-8', 'ignore'), 'html5lib')
					if 'dir.bg' in channel['epg_url']:
						program = soup.find(div, id='today')
						lis = program.find_all(li, class_='list-group-item')
						for l in lis:
							n = source['name']
							text = l.get_text()
							if n in text:
								streams.append(Stream([0, 0, text, 'plugin://plugin.video.free.bgtvs/?mode=play_channel&id=11']))
							
						#url = soup.iframe[src]
			
		except Exception, er:
			self.plugin.log.error(str(er))
		return streams
	
		
		

div = 'div'
P = 'p'
A = 'a'
B = 'b'
IMG = 'img'
src = 'src'
HREF = 'href'
span = 'span'
ul = 'ul'
url = 'url'
li = 'li'
CATEGORY = 'Category'
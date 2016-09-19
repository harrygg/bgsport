# -*- coding: utf-8 -*-
import sys, os, base64
from xbmcswift2 import Plugin

from resources.lib.classes import *
from resources.lib.mode import Mode

reload(sys)
sys.setdefaultencoding('utf8')
plugin = Plugin('plugin.video.bgsport')

#append_pydev_remote_debugger
REMOTE_DBG = False
if REMOTE_DBG:
	try:
		sys.path.append("C:\\Software\\Java\\eclipse-luna\\plugins\\org.python.pydev_4.4.0.201510052309\\pysrc")
		import pydevd
		xbmc.log("After import pydevd")
		#import pysrc.pydevd as pydevd # with the addon script.module.pydevd, only use `import pydevd`
		# stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
		pydevd.settrace('localhost', stdoutToServer=False, stderrToServer=False, suspend=False)
	except ImportError:
		xbmc.log("Error: You must add org.python.pydev.debug.pysrc to your PYTHONPATH.")
		sys.exit(1)
	except:
		xbmc.log("Unexpected error:", sys.exc_info()[0]) 
		sys.exit(1)
#end_append_pydev_remote_debugger	

#plugin entry screen camera categories
@plugin.route('/')
def index():
	cats = get_parent_categories()
	items = [{
		'label': cat.name, 
		'path': plugin.url_for(Mode.show_categories, category_id=cat.id)
	} for cat in cats]
	return items

def get_categories(category_id = 0):
	categories = []
	try:
		conn = sqlite3.connect(assets.local_db)
		if category_id != 0:
			cursor = conn.execute('''SELECT * FROM categories WHERE id == ? AND disabled == 0''',  [category_id])
			row = cursor.fetchone()
			cat = CategoryExt(row[1], id=row[0], parent_id=row[2], url=row[5])
			cat.has_children = row[3] == 1
			cat.disabled = row[4] == 1
			if cat.url != '':
				categories = helper.get_videos(category.url)
		else:
			cursor = conn.execute('''SELECT * FROM categories WHERE parent_id == ? AND disabled == 0''',  [category_id])
			for row in cursor:
				cat = CategoryExt(row[1], id=row[0], parent_id=row[2], url=row[5])
				cat.has_children = row[3] == 1
				cat.disabled = row[4] == 1
				categories.append(cat) 
				
	except Exception, er:
		plugin.log.error(str(er))
	return categories

def get_parent_categories(category_id = 0):
	categories = []
	try:
		conn = sqlite3.connect(assets.local_db)
		cursor = conn.execute('''SELECT * FROM categories WHERE parent_id == ? AND disabled == 0''',  [category_id])
		for row in cursor:
			cat = CategoryExt(row[1], id=row[0], parent_id=row[2], url=row[5])
			cat.has_children = row[3] == 1
			cat.disabled = row[4] == 1
			categories.append(cat)			
	except Exception, er:
		plugin.log.error(str(er))
	return categories

@plugin.route('/categories/<category_id>/')
def show_categories(category_id):
	items = []
	cats = get_parent_categories(category_id)
	for cat in cats:
		if cat.id == 15:
			path = plugin.url_for(Mode.show_fixtures)
		else:
			if cat.has_children:
				path = plugin.url_for(Mode.show_categories, category_id=cat.id)
			else:
				if cat.url == '':
					cat.url = 'None'
				path = plugin.url_for(Mode.show_streams, category_id=cat.id, url=cat.url, name=base64.b64encode(cat.name))
			
		plugin.log.info("cat.id: "+ str(cat.id))
		plugin.log.info("cat.name: "+ cat.name)
		plugin.log.info("cat.has_children: "+ str(cat.has_children))
		try:  plugin.log.info("cat.url: "+ cat.url)
		except: pass
		
		try: thumb = cat.thumb
		except: thumb = ''
		
		items.append({
			'label' : cat.name, 
			'path' : path,
			'icon' : thumb,
			'is_playable' : False
		})
	return items
	#return plugin.finish(items, view_mode=500)

@plugin.route('/fixtures/a-grupa/')
def show_fixtures(id = ''):
	items = []	
	try:
		cats = helper.get_bg_foobtall_games()
		for cat in cats:
			#plugin.log.info("cat.name: "+ cat.name)
			#plugin.log.info("cat.has_children: "+ str(cat.has_children))
			#plugin.log.info("cat.mode: "+ str(mode))
			items.append({
				'label' : cat.name, 
				'path' : plugin.url_for(Mode.show_streams, category_id=0, url=cat.url, name=base64.b64encode(cat.name)),
				'is_playable' : False
			})
	except Exception, er:
		plugin.log.error(er)
	return items
	#return plugin.finish(items, view_mode=500)


@plugin.route('/stream/<category_id>/<url>/<name>')
def show_streams(category_id, url, name):
	list_items = []
	try:
		items = get_streams(category_id, url)
		
		for item in items:
			if item.__class__.__name__ == 'CategoryExt': #Next item button or unresolved item
				list_items.append({
					'label' : item.name, 
					'path' : plugin.url_for(Mode.show_streams, category_id=item.id, url=item.url, name=base64.b64encode(item.name)),
					'is_playable' : False
				})
			else:	
				try: thumb = stream.thumb
				except: thumb = ''
				
				if item.name == None:
					item.name = base64.b64decode(name)
				if not helper.is_resolved(item.url):
					item.url = helper.resolve_m3u(item.url)
				
				sinfo = {'video': {'aspect': 1.78}}

				
				list_items.append({
					'label' : item.name, 
					'path' : item.url,
					'icon' : item.thumb,
					'is_playable' : True,
					'stream_info' : sinfo
				})
			plugin.log.info("item.id: "+ str(item.id))
			plugin.log.info("item.name: "+ item.name)
			plugin.log.info("item.url: "+ item.url)
			plugin.log.info("item.thumb: "+ item.thumb)
			#plugin.log.info("item.is_playable: "+ item.is_playable)
	except Exception, er:
		plugin.log.error(str(er))
	return list_items
	#return plugin.finish(list_items, view_mode=500)

def get_streams(category_id = 0, url = ''):
	streams = []
	try:
		if url != 'None' and url != '':
			streams = helper.get_stream_from_url(url)
		elif category_id == str(16): #Sport events
			streams = helper.get_bgsport_streams()
		else:
			conn = sqlite3.connect(assets.local_db)
			cursor = conn.execute('''SELECT * FROM streams WHERE category_id == ?''',  [category_id])
			for row in cursor:
				strm = StreamExt(row[2], id=row[0], category_id=row[1], url=row[3], disabled=row[4])
				streams.append(strm) 
	except Exception, er:
		plugin.log.error(str(er))
	return streams
	
#Play camera stream
#@plugin.route('/play/<url>/')
#def play_stream(camera_id):
#	stream = get_stream(camera_id)
#	plugin.log.info('Playing url: %s' % stream)
#	plugin.set_resolved_url(stream)

assets = Assets(plugin)
helper = Helper(plugin)
#helper.check_assets()

#Run addon
if __name__ == '__main__':
	plugin.run()

 

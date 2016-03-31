# -*- coding: utf-8 -*-
import sys, os
from xbmcswift2 import Plugin
import urlresolver
from resources.lib.classes import *

reload(sys)
sys.setdefaultencoding('utf8')
plugin = Plugin('plugin.video.bgsport')

#plugin entry screen camera categories
@plugin.route('/')
def index():
	#sources = [urlresolver.HostedMediaFile(url='http://www.dailymotion.com/video/x3z3l2c', title='dailymotion')]
	#plugin.log.info("sources len: " + str(len(sources)))
	#source = urlresolver.choose_source(sources)
	#if source:
	#	stream_url = source.resolve()
	#	addon.resolve_url(stream_url)
	#else:
	#	addon.resolve_url(False)
	#media_url = urlresolver.resolve('http://btvplus.bg/produkt/predavaniya/1810')
	#plugin.log.info("media_url: " + media_url)
	#stream_url = urlresolver.HostedMediaFile(host='dailymotion.com', media_id='x3z3l2c').resolve()
	#plugin.log.info("stream_url: " + stream_url)
	cats = get_categories()
	items = [{
		'label': cat.name, 
		'path': plugin.url_for('show_category', category_id=cat.id), 
		'is_playable': False
	} for cat in cats]
	return items

def get_categories(category_id = 0):
	conn = sqlite3.connect(helper.local_db)
	cursor = conn.execute('''SELECT * FROM categories WHERE parent_id == 0''',  [category_id])
	categories = [Category(row) for row in cursor] 
	return categories

@plugin.route('/categories/<category_id>/')
def show_category(category_id):
	items = []
	cats = get_categories(category_id)
	
	items.append({
			'label' : cat.name, 
			'path' : plugin.url_for('show_videos', category_id=cat.id),
			'icon' : '',
			'is_playable' : False
		})
	return items
	#return plugin.finish(items, view_mode=500)

@plugin.route('/videos/<category_id>/')
def show_videos(category_id):
	items = []
	cats = get_videos(category_id)
		
	items.append({
			'label' : video.name, 
			'path' : plugin.url_for('play_videos', video_id=cat.id),
			'icon' : '',
			'is_playable' : False
		})
	return items
	#return plugin.finish(items, view_mode=500)
	
#Play camera stream
#@plugin.route('/play/<url>/')
#def play_stream(camera_id):
#	stream = get_stream(camera_id)
#	plugin.log.info('Playing url: %s' % stream)
#	plugin.set_resolved_url(stream)
	
helper = Helper(plugin)
helper.check_assets()

#Run addon
if __name__ == '__main__':
	plugin.run()

 

# -*- coding: utf-8 -*-
import sys, os
from xbmcswift2 import Plugin
import urlresolver
#from resources.lib.classes import *

reload(sys)
sys.setdefaultencoding('utf8')
plugin = Plugin('plugin.video.bgsport')

#plugin entry screen camera categories
@plugin.route('/')
def index():
	sources = [urlresolver.HostedMediaFile(url='http://www.dailymotion.com/video/x3z3l2c', title='dailymotion')]
	plugin.log.info("sources len: " + str(len(sources)))
	#source = urlresolver.choose_source(sources)
	#if source:
	#	stream_url = source.resolve()
	#	addon.resolve_url(stream_url)
	#else:
	#	addon.resolve_url(False)
	media_url = urlresolver.resolve('http://btvplus.bg/produkt/predavaniya/1810')
	plugin.log.info("media_url: " + media_url)
	stream_url = urlresolver.HostedMediaFile(host='dailymotion.com', media_id='x3z3l2c').resolve()
	plugin.log.info("stream_url: " + stream_url)
	
	items = [{
		'label': "Dailymotion", 
		'path': media_url, 
		'is_playable': True
	}]
	return items

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

 
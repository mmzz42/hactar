#!/usr/local/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Alberto Cammozzo
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.#

import sys
import getopt
import codecs
import feedparser
import unicodedata
import httplib
import chardet
import socket
import datetime
import json
import time
import urltools
import re
import hashlib
import urlparse
from time import mktime
from pymongo import MongoClient
from lxml.html.clean import Cleaner
from optparse import OptionParser

from hactar.strings import normalize
from hactar.db import storeFeedItem
from hactar.db import logFeed
from hactar.net import getFeed


# #
# MAIN
# #

reload(sys)
sys.setdefaultencoding('utf-8')
socket.setdefaulttimeout(10)

usage = "usage: %prog [options] arg"
parser = OptionParser(usage)

parser = OptionParser()
parser.add_option("-r", "--reload", action="store_true", dest="reload",
        help="reload articles from url in db")
parser.add_option("-e", "--encoding", dest="encoding",
        help="force encoding. Default UTF-8 or as specified in HTML page")
parser.add_option("-g", "--guess", action="store_true", dest="guess",
        help="guess encoding by content")
parser.add_option("-R", "--reloadOnFail", action="store_true",  dest="rof",
        help="reload only if cdb copy is empty or failed")
parser.add_option("-u", "--url", dest="url",
        help="load one specific url")

(options, args) = parser.parse_args()
if options.guess and options.encoding:
    parser.error("options -g and -e are mutually exclusive")
if options.url and options.reload:
    parser.error("options -u and -r are mutually exclusive")


if options.url:
        (bozo,feedItems,exception) = getFeed(options.url)
	if bozo:
		print exception
	else:
		for item in feedItems:
			print item[ "link" ]
else:
	if (len(sys.argv[0].split('-'))<=1):
		print sys.argv[0],": give <url> as argument or invoke as ",sys.argv[0]+"dbname"
        	quit()

        (prog,dbname) = sys.argv[0].split('-',1)
        server="mongoPrimary:27017"

        client = MongoClient(server)
        db = client[dbname]
        now = datetime.datetime.now()

        feedsource="feedsource"+ str(now.year)
        feedsourceDB = db[feedsource]

	feedlog="log_feed"+str(now.year)
        feedlogDB = db[feedlog]

	feeditem="feeditem"+str(now.year)
        feeditemDB = db[feeditem]
        feeditemDB.create_index('itemMD5hash',unique=True)

	# read feeds collection
        all = feedsourceDB.find({"active": True, "protocol":"rss"},no_cursor_timeout=False)
        #all = feedsourceDB.find({"active": True},no_cursor_timeout=False)

	# collect data in each feed
        for feed in all:
                oid=feed['_id']
                url=feed['URL']
                site=feed['site']
		name=feed['name']

	        (bozo,feedItems,exception) = getFeed(url)
		num=len(feedItems)
		if bozo == 1:
			logFeed(feedlogDB,oid,site,name,num,url,exception)
		else:
			logFeed(feedlogDB,oid,site,name,num,url,"none")

		for item in feedItems:
                        title=link=author=published=summary=""
                        if ('title' in item):
			    title = normalize(item["title"])
                        if ('link' in item):
			    l = item[ "link"]
			    (link,frag) = urlparse.urldefrag(l) # remove fragments from URL
                        else:
                            next
                        if ('author' in item):
        		    author = item["author"].upper()
#                        if ('published' in item):
#       		     p = item["published"]
#                            published = dateutil.parser.parse(p)
                        if ('published_parsed' in item):
        		    p = item["published_parsed"]
                            if p != None:
                                published=datetime.datetime.fromtimestamp(mktime(p))
                            else:
			        logFeed(feedlogDB,oid,site,name,num,url,"no publishing date")
                                next
                        else:
			    logFeed(feedlogDB,oid,site,name,num,url,"no publishing date")
                            next
                        if ('summary' in item):
			    summary = normalize(item["summary"])

	                # to avoid fetching again the same item in further runs, calculate 
                        # hash based on site, feed, publication date, and link
                        itemhash=hashlib.md5(str(published)+link+name+site).hexdigest()
                	contenthash=hashlib.md5(str(published)+link+title).hexdigest()
                        if feeditemDB.find({"itemMD5hash": itemhash},no_cursor_timeout=False).count() == 0:
        		    storeFeedItem(feeditemDB,oid,itemhash,url,site,name,title,link,published,author,summary)

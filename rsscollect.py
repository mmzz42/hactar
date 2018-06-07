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
from argparse import ArgumentParser
#
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

parser = ArgumentParser()
parser.add_argument("dbname", type=str,help='database name')
parser.add_argument("-u", "--url", dest="url",help="load one specific url")
parser.add_argument("-v", "--verbose", action="store_true", help="be chatty")

(args) = parser.parse_args()
    
if args.url:
        (bozo,feedItems,exception) = getFeed(args.url)
	if bozo:
		print exception
	else:
		for item in feedItems:
                    if args.verbose:
                        print "feed:",args.url,"item",item[ "link" ]
else:
	if (not args.dbname) :
		print sys.argv[0],
                ": give -u url as RSS feed or dbname (feedsouce collection needed) "
        	quit()

        server="mongoPrimary:27017"
        dbname=args.dbname

        client = MongoClient(server)
        db = client[dbname]
        now = datetime.datetime.now()

        feedsource="feedsource"
        feedsourceDB = db[feedsource]

	feedlog="log_feed"
        feedlogDB = db[feedlog]

	feeditem="feeditem"
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
                if args.verbose:
                    print "FEED: ",site+"|"+name

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
                            if args.verbose:
                                print "NEW ITEM: ",site,name,link

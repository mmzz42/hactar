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
import bson
import bz2
import re
import validators
import md5
import lxml
import unicodedata
import datetime
import httplib
import chardet
from scrapy.selector import Selector
from bson import Binary
from pymongo import MongoClient
from lxml.html.clean import Cleaner
from lxml import etree, html
from argparse import ArgumentParser

from hactar.net import geturl
from hactar.db import logArticle
from hactar.db import storeArticle


#
# MAIN
#

reload(sys)
sys.setdefaultencoding('utf-8')

parser = ArgumentParser()
parser.add_argument("dbname", type=str,help='database name')
parser.add_argument("-v", "--verbose", action="store_true", help="be chatty")

(args) = parser.parse_args()
if (not args.dbname) : 
    print sys.argv[0], 
    ": database name argument needed" 
    quit()
dbname=args.dbname

server="mongoPrimary:27017"
client = MongoClient(server)
db = client[dbname]
now = datetime.datetime.now()

articleDB = db["article"]
feeditemDB = db["feeditem"]
articlelogDB = db["log_article"]
    
all = feeditemDB.find({'collected': False},no_cursor_timeout=False)

for feeditem in all:
    oid=feeditem['_id']
    link=feeditem['itemLink']
    title=feeditem['itemTitle']
    site=feeditem['feedSite']
    summary=feeditem['itemSummary']
    name=feeditem['feedName']
    published=feeditem['itemPublished']
    channel=feeditem['channel']
    author=feeditem['itemAuthor']
    source=channel+'|'+site+'|'+name

    # download article from link URL
    (html,http,code,realurl,headers,error) = geturl(link)
    feeditemDB.update({'_id': oid},{'$set': {'collected':True}})
    textsize=len(html)

    logArticle(articlelogDB, oid, published, source, link, http, realurl, textsize, code, headers)
    if textsize==0:
        print error, source, link, http, realurl, textsize, code
        continue

    bzhtml=bz2.compress(html)
    storeArticle(articleDB,source,title,summary,published,author,bzhtml,code,realurl,headers)
    if args.verbose:
        print "NEW ARTICLE: ",source,realurl

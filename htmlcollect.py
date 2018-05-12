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
from optparse import OptionParser


#
# retrieve URL
#
def geturl(url):
	import requests
        #https://github.com/requests/requests/issues/1604
        import requests_patch


        url.strip()
	err=code=http=""

	#get URL
        try:
            r = requests.get(url)
        except requests.exceptions.RequestException as err:
	    print err,url
            return("","","",url,"",err)

        #http status code
        http = str(r.status_code)

	#empty page                
        if (len(r.text) == 0):
	    print "[%s][%s][%s][%s]" % (http,r.encoding,code,err)
            return("",http,"",r.url,r.headers,"emptyPage")

        #detect content type
        if ("text" not in r.headers['content-type'].lower()):
	    print "[%s][%s][%s][%s]" % (http,r.encoding,code,r.headers['content-type'])
            return("",http,"",r.url,r.headers,"noText")
            

	#detect encoding
        if r.encoding is None or r.encoding == 'ISO-8859-1':
            r.encoding = r.apparent_encoding

        return(r.text,http,r.encoding,r.url,r.headers,err)

	encoding = chardet.detect(r.content) # guess encoding
	detected = encoding['encoding']
        header = r.encoding

        if detected == None:
            detected = "none"
        if header == None:
            header="none"
        if detected.upper() != header.upper():
	    err = "code mismatch:"+detected+"/"+header
        code=detected
        if code == "none":
            code="utF-8"

        try: 
       	    #html =  unicode(r.text).decode(code,'ignore')
       	    html =  unicode(r.text).decode(code,'strict')
        except UnicodeDecodeError as err:
		print "[%s][%s][%s][%s]" % (http,r.encoding,code,err)
                return(html,http,code,r.url,r.headers,err)

	print "[%s][%s][%s][%s]" % (http,r.encoding,code,err)
        return(html,http,code,r.url,r.headers,err)

# log 
def logArticle(articlelogDB, oid, published, source, link, http, realurl, textsize, code, headers):
    articlelogDB.insert_one(
       {
        'feedItemOid': oid,
        'published': published,
        'source': source,
        'link': link,
        'httpCode': http,
        'URL': realurl,
        'textsize': textsize,
        'encoding': code,
        'headers': headers,
       }
      )

# store successufully retrieved article, content gzipped
def storeArticle(articleDB,source,title,summary,published,author,bzhtml,code,realurl,headers):
    articleDB.insert_one(
        {
            'source': source,
            'title': title,
            'published': published,
            'author': author,
            'bzhtml': Binary(bzhtml),
            'encoding': code,
            'URL': realurl,
            'scraped': False,
            'summary': summary,
            'downloaded': datetime.datetime.utcnow(),
        }
     )
#
# MAIN
#

reload(sys)
sys.setdefaultencoding('utf-8')


usage = "usage: %prog [options] arg"
parser = OptionParser(usage)

parser = OptionParser()
(options, args) = parser.parse_args()

if (len(sys.argv[0].split('-'))<=1):
    print sys.argv[0],": give <url> as argument or invoke as ",sys.argv[0]+"dbname"
    quit()

(prog,dbname) = sys.argv[0].split('-',1)
server="mongoPrimary:27017"
client = MongoClient(server)
db = client[dbname]
now = datetime.datetime.now()

articleDB = db["article"+str(now.year)]
feeditemDB = db["feeditem"+str(now.year)]
articlelogDB = db["log_article"+str(now.year)]
    
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
    print source,code,published,realurl

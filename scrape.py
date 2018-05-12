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
import httplib
import chardet
import datetime
import hashlib
from scrapy.selector import Selector
from pymongo import MongoClient
from lxml.html.clean import Cleaner
from lxml import etree, html
from optparse import OptionParser


#
# retrieve URL
#
def geturl(url):
	import requests
        r = requests.get(url)
        http = str(r.status_code)
	code='utf-8'
	if (http == "200"):
		# prefer declared encoding in case of mismatch 
		if (code != r.encoding):
			code = r.encoding
		# override encoding if option is given to guess encoding by content
		if options.guess:
			encoding = chardet.detect(r.content) # guess encoding
			code= encoding['encoding']
		# override if encoding is given by default
		if options.encoding:
			code = options.encoding
        	html =  unicode(r.text).decode(code)
	else:
		html = ""
		code = "none"
	
        return(html,http,code,r.url)

#
# scrape
# 
def scrape(lineHashDB,html,encoding):
	# cleaner setup
	cleaner = Cleaner(allow_tags=['div','p'], remove_unknown_tags=False)
	cleaner.javascript = True # activate the javascript filter
	cleaner.style = True      #  activate the styles & stylesheet filter
	cleaner.comments = True
	cleaner.annoying_tags = True
	cleaner.inline_style = True
	cleaner.page_structure = False
	cleaner.remove_tags = ['b','a','h']
	cleaner.kill_tags = ['script']
	
	#invoke cleaner
        #ValueError: Unicode strings with encoding declaration are not supported. Please use bytes input or XML fr 
	page=cleaner.clean_html(html)
	page8=page
	page8 = re.sub(u'\n',' ',page8) # remove NL 
#	page8 = re.sub(u'\s','',page8,re.UNICODE) # blanks -> space
	page8 = re.sub(u'&#13;',' ',page8) # remove CR
	page8 = re.sub(u'<!--.*?-->',' ',page8) # remove comments
	page8 = re.sub(u' class=".*?"',' ',page8) # remove attributes
	page8 = re.sub(u' id=".*?"',' ',page8)
	page8 = re.sub(u' rel=".*?"',' ',page8)
	page8 = re.sub(u'\[an error occurred while processing this directive\]',' ',page8)
	page8 = re.sub(u'>\s*?<','><',page8) # remove blanks between tags 

	# cycle to remove spurious divs
	for count in range (1,20):  
		page8 = re.sub(u'>.{0,10}<','><',page8) # remove words under 10 chars between tags
		page8 = re.sub(u'<div></div>',' ',page8)
		page8 = re.sub(u'<p></p>',' ',page8)
		page8 = re.sub(u'<span></span>',' ',page8)

	page8 = re.sub(u'\s+',' ',page8)  # remove repeated blanks

        #XPATHs
	xpath='//*[((p) or (a) or (b) or (div) or (span)) ]/node()[(string-length() > 300)]/text()'
	xpath='//*[((p) or (div))]/node()[(string-length() > 100)]/text()'

	sel=Selector(text=page8, type="html")
	text= sel.xpath(xpath).extract()
	content = u""
	if text:
	    for s in text:
		# squash duplicate whitespaces
	        ' '.join(s.split())
		# remove short lines
                # on empirical analysis, no unfrequent sentence under 40 chars is a relevant part of the article text, excluding repetition of title, authors, dates, etc. 
		if len(s) < 40:		
			next
		# remove leading whitespace 
		#if s.endswith(" "): s = s[:-1]
    		if s.startswith(" "): s = s[1:]
		content += s
		content += "\n"
	return content

def cleanupText(lineHashDB,page,lineThreshold):
	content= u""
	for line in page.splitlines():
        	md5hash=hashlib.md5(line).hexdigest()
		hashline=lineHashDB.find_one({'hash':md5hash})
        	if hashline:
                    dups=hashline['count']
        	    if dups < lineThreshold:
			content += "~"
			content += line
			content += " "
	                print "+",dups,line
	            else:
	                print "-",dups,line
        	else:
			content += "~"
			content += line
			content += " "
	                print "+ 0 ",line
	return(content)




# get page, scrape, print out
#
def print_content(url):
	(html,http,encoding,rurl) = geturl(url)

	if http != "200":
		print "\nERR ",http,rurl,encoding
	else:	
		print "\nOK ",http,rurl,encoding
		page=scrape(lineHashD,Bhtml,encoding)
		#s = page.decode(encoding,'ignore').encode('utf-8')
		print(page)


# Store a hash of each string in page, 
def storeLineHash(lineHashDB,page):
    for line in page.splitlines():
        md5hash=hashlib.md5(line).hexdigest()
        ts = datetime.datetime.utcnow()
        dups= lineHashDB.find({'hash':md5hash}).count() 
	if dups >0:
            lineHashDB.update({'hash':md5hash},
                    {
                        '$inc': {'count':1},
                        '$set': {'last':ts}
                    },
                    upsert=True,
                    multi=True)
        else:
            lineHashDB.insert_one(
                {
                    'hash': md5hash,
                    'first': ts,
                    'last': ts,
                    'line': line,
                    'count': 1
                }
            )

            # update article: scraped 
def markScraped (articleDB,oid,exception):
	ts = datetime.datetime.utcnow()
	articleDB.update({'_id':oid},
		{
			'$set': { 
                            'scraped':ts,
                            'scrapingException':exception
			},
		},
                upsert=True,
                multi=False)

# update article with scraped text data
def storeArticle (articleDB,oid,page):
	ts = datetime.datetime.utcnow()
	articleDB.update({'_id':oid},
		{
			'$set': { 
				'text': page,
				'scraped': ts
			},
		},
                upsert=True,
                multi=False)
		
#
# retrieve and scrape from URL or rescrape from DB
# invoke as 
# 	scrape-dbname 
# or 
# 	scrape Url
#

reload(sys)
sys.setdefaultencoding('utf-8')


usage = "usage: %prog [options] arg"
parser = OptionParser(usage)

parser = OptionParser()
parser.add_option("-r", "--reload", action="store_true", dest="reload", 
	help="reload articles from url in db")
parser.add_option("-e", "--encoding", dest="encoding", 
	help="force encoding. Default UTF-8 or as specified in HTML page")
parser.add_option("-g", "--guess", action="store_true", dest="guess", 
	help="guess encoding by content, works with -u ")
parser.add_option("-t", "--train", action="store_true",  dest="train", 
	help="train lineHash db: insert all lines even over threshold")
parser.add_option("-u", "--url", dest="url", 
	help="load one specific url")
(options, args) = parser.parse_args()
if options.guess and not options.url:
    parser.error("option -g works with -u")
if options.guess and options.encoding:
    parser.error("options -g and -e are mutually exclusive")
if options.url and options.reload:
    parser.error("options -u and -r are mutually exclusive")


if options.url:
	print_content(options.url)
else:
	if (len(sys.argv[0].split('-'))<=1):
		print sys.argv[0],": give <url> as argument or invoke as ",sys.argv[0]+"dbname"
		quit()

	(prog,dbname) = sys.argv[0].split('-',1)
	server="mongoPrimary:27017"

	client = MongoClient(server)
	db = client[dbname]
        now = datetime.datetime.now()

	articleDB = db['article'+str(now.year)]
	articleDB.create_index('scraped')

	lineHashDB = db['lineHash'+str(now.year)]
	lineHashDB.create_index('hash', unique=True)


        all = articleDB.find({'scraped': False},no_cursor_timeout=False)
	items=all.count()
	counter=0

	for article in all:
		counter +=1
		oid=article['_id']
		url=article['URL']
		feed=article['source']
		code=article['encoding']

		# download article from stored URL
		if options.reload==True:
			print_content(url)
			continue

		# extract from archived copy
	        bzText=article['bzhtml']
		html=bz2.decompress(bzText)
		textsize=len(html)

		#decode and convert to UTF8
		if code is None:
		        encoding = chardet.detect(html) # guess encoding
			if encoding['confidence'] > 0.5:
			        code= encoding['encoding'].upper()
			else:
				print "\nKO",oid, feed, url, "text size:",textsize,"no encoding guessed", code
				continue

		try:
	       		html8 = unicode(html).decode(code,'strict')
			page=scrape(lineHashDB,html8,code)
		except UnicodeDecodeError:
			print "\nKO",oid, feed, url, "text size:",textsize,"decoding exception:", code
                        exception="decoding exception"+code
                        markScraped(articleDB,oid,exception)
			pass
		if len(page)==0:
                    next

		# store line hashes and update article with scraped text
 		print "OK", str(counter)+"/"+str(items),url
                storeLineHash(lineHashDB,page)
		if not options.train:
		# threshold 
			threshold = 12
			text=cleanupText(lineHashDB,page,threshold)
			storeArticle(articleDB,oid,text)


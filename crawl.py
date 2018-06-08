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
import validators
import lxml
import datetime
from pymongo import MongoClient
from lxml.html.clean import Cleaner
from lxml import etree, html
from argparse import ArgumentParser
from hactar.net import geturl
from urlparse import urlparse
from urlparse import urljoin
from scrapy.linkextractors import LinkExtractor
from scrapy.selector import Selector


def cleanpage(html):
	# cleaner setup
	cleaner = Cleaner()
        cleaner.html = True
        cleaner.page_structure = False
        cleaner.meta = False
        cleaner.safe_attrs_only = False
        cleaner.links = False
	cleaner.javascript = True # activate the javascript filter
	cleaner.style = True      #  activate the styles & stylesheet filter
        cleaner.links = False
        cleaner.frames = True
        cleaner.embedded = True
	cleaner.comments = True
	cleaner.annoying_tags = True
	cleaner.inline_style = True
	cleaner.page_structure = False
#	cleaner.remove_tags = ['b','img','h']
	cleaner.kill_tags = ['img','script']
	
	#invoke cleaner
        try:
            content=cleaner.clean_html(html)
        except:
            #error: ValueError: Unicode strings with encoding declaration are not supported. Please use bytes input or XML fr 
            content = u""
        return content

def getInternalLinks(html,baseurl):
    internalLinks=[]
    xpath='//a[@href]'
    xpath='//@href'
    sel=Selector(text=html, type="html") 
    links=sel.xpath(xpath).extract() 
    if links: 
        for i in links: 
            i=i.replace("\n", "") 
            i = urljoin(baseurl, i)
            if i.startswith(baseurl):
               if i not in internalLinks:
                   internalLinks.append(i)
               if args.debug: print "internal ", i 
            else:
               if (validators.url(i)):
                    if args.debug: print "external ", i 
               else:
                    if args.debug: print "rejected ",i
    return(internalLinks) 

def getBase(url):
    links=[]
    parsed=urlparse(url)
    scheme=parsed.scheme
    netloc=parsed.netloc
    baseurl=scheme+'://'+netloc
    (html,http,code,url,headers,err)=geturl(url)
    if (http == "200") and ("text/html" in headers['Content-Type'].lower()):
        html=cleanpage(html)
        links=getInternalLinks(html,baseurl)
    return(links)



#page ratio sub
    #validate URL
    #get page
    #clean page (scrub)
    #for each a href path inside page


    #ratio: (textlenght/internal links)* url length * --# of dashes in url/ factor (500)



##
##MAIN
##

parser = ArgumentParser()
parser.add_argument("dbname", type=str,help='database name')
parser.add_argument("-v", "--verbose", action="store_true", help="be chatty")
parser.add_argument("-u", "--url", dest="url", help="load one specific url")
parser.add_argument("-d", "--debug", dest="debug", help="debug extra output")

(args) = parser.parse_args()

if args.url:
    url=args.url
    firstLinks=getBase(url)
    if args.verbose: print "internal first links: ",len(firstLinks), url
    for link in firstLinks:
        secondLinks = getBase(link)
        if args.verbose: print "internal second links: ",len(secondLinks), link

    
else:
    dbname=args.dbname
    server="mongoPrimary:27017"
    
    client = MongoClient(server)
    db = client[dbname]
    now = datetime.datetime.now()

    feedsourceDB = db['feedsource']
    articleDB = db['article']
    
    feeds = feedsourceDB.find({"active": True, "protocol":"http"},no_cursor_timeout=False)    
    items=feeds.count()
    counter=0
    if args.verbose: print dbname+"/feedsource","has ",items," items"

    for feed in feeds:
        oid=feed['_id']
        url=feed['URL']
        site=feed['site']
        name=feed['name']
        if args.verbose: print "FEED: ",site+"|"+name

        firstLinks=getBase(url)
        if args.verbose: print "internal first links: ",len(firstLinks), url
        for link in firstLinks:
            secondLinks = getBase(link)
            if args.verbose: print "internal second links: ",len(secondLinks), link




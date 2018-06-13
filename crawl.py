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
import hashlib

from pymongo import MongoClient
from lxml.html.clean import Cleaner
from lxml import etree, html
from argparse import ArgumentParser
from hactar.net import geturl
from hactar.db import storeLineHash
from hactar.db import storeArticle
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

        return(html,links)


def pageRatio(url,html):
    
        ratio=-10
        parameter=500
        textxpath="//*[((p) or (a) or (div)) ]/node()/text()"
        dashes = url.count('_')
        dashes = dashes + url.count('-')
    
        # URL metrics
        urlLen = len(url)
        # page content metrics
        html=cleanpage(html)
        sel=Selector(text=html, type="html")
        text= sel.xpath(textxpath).extract()
        textLen = len(text)
        # links metrics
        links=len(getInternalLinks(html,url))
        
        if links > 0: 
            ratio=((textLen/links)*urlLen*--dashes)/parameter
            ratio = ratio -1

        return(ratio)

def html2unicode(html):
        from bs4 import BeautifulSoup
        html8 = BeautifulSoup(html,"lxml")

        return(html8.text)

def getMeta(html):
        import re
        import time
        from dateutil.parser import parse

        r = re.search( "<title>(.*)<\title>", html )
        r = re.search( "<meta property=\"og:title\".*?content=\"([^\"]*)\"", html )
        if r is None:
            title=None
        else:
            t=r.group( 1 )
            title=html2unicode(t)

        r = re.search( "<meta property=\"article:published_time\".*?content=\"([^\"]*)\"", html )
        if r is None:
            published=None
        else:
            p=r.group( 1 )
            if p != None: published=parse(p)
                                                                             

        r=re.search( "<meta property=\"article:author\".*?content=\"([^\"]*)\"", html )
        if r is None:
            author=None
        else:
            a=r.group( 1 )
            author=html2unicode(a)

        r=re.search( "<meta property=\"og:description\".*?content=\"([^\"]*)\"", html )
        if r is None:
            summary=None
        else:
            s=r.group( 1 )
            summary=html2unicode(s)


        return(title,summary,author,published)

##
##MAIN
##

parser = ArgumentParser()
parser.add_argument("dbname", type=str,help='database name')
parser.add_argument("-v", "--verbose", action="store_true", help="be chatty")
parser.add_argument("-u", "--url", dest="url", help="load one specific url")
parser.add_argument("-d", "--debug", dest="debug", help="debug extra output")
parser.add_argument("-t", "--train", action="store_true", help="train url hash db")

(args) = parser.parse_args()

if args.url:
    url=args.url
    (html,feedLinks)=getBase(url)
    # follow feed page links 
    print feedLinks
    for link in feedLinks:
        (html,pageLinks) = getBase(link)
        ratio=pageRatio(link,html)
        if args.verbose: print ratio, link
    
else:
    dbname=args.dbname
    server="mongoPrimary:27017"
    protocol="http"
    
    client = MongoClient(server)
    db = client[dbname]
    now = datetime.datetime.now()

    feedsourceDB = db['feedsource']
    articleDB = db['article']
    urlhashDB = db['urlhash']
    urlhashDB.create_index('line', unique=True)
    feeds = feedsourceDB.find({"active": True, "protocol":protocol},no_cursor_timeout=False)    
    items=feeds.count()
    counter=0
    if args.verbose: print dbname+"/feedsource","has ",items," items"

    for feed in feeds:
        oid=feed['_id']
        url=feed['URL']
        site=feed['site']
        name=feed['name']
        source=protocol+'|'+site+'|'+name
        if args.verbose: print "FEED: ",site+"|"+name

        (html,feedLinks)=getBase(url)
        for link in feedLinks:
            (html,pageLinks) = getBase(link)
#            ratio=pageRatio(link,html)
            getMeta(html)          
            if args.train:  
                storeLineHash(urlhashDB,link)
            else:
                samelink=urlhashDB.find_one({"line": link})
                if samelink: count = samelink['count']

                if count > 10:
                    (title,summary,author,published)=getMeta(html)
                    #if args.verbose: print "REJECT: ",source,title,summary,author
                else:
                    (html,http,code,realurl,headers,error) = geturl(link)
                    if args.verbose: 
                        print "ACCEPT: ",link
                        print "title ",title
                        print "summary ",summary
                        print "author ", author
                        print "published ",published
                    storeLineHash(urlhashDB,link)
                    
                    textsize=len(html)
                    if textsize==0:
                        if args.verbose: print error, source, link, http, realurl, textsize, code
                        continue
                    (title,summary,author,published)=getMeta(html)

                    bzhtml=bz2.compress(html)
                    storeArticle(articleDB,source,title,summary,published,author,bzhtml,code,realurl,headers)


# add feedhealth ranking
# add TS date for retrieved

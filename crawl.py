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
from scrapy.selector import Selector
from pymongo import MongoClient
from lxml.html.clean import Cleaner
from lxml import etree, html
from optparse import OptionParser



def extractLinks(html):
    xpath='//img[@href]'
    sel=Selector(text=html, type="html") 
    links=sel.xpath(xpath).extract() 
    if links: 
        for i in links: 
            i=i.replace("\n", "") 
            if (not validators.url(i)):
                print "rejected ",i
                continue 
            else:
                print "accepted ",i
        

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
parser.add_argument("-u", "--url", dest="url", 	help="load one specific url")

(args) = parser.parse_args()

if args.url:
    (html,http,code,r.url,r.headers,err)=geturl(url)
    extract_links(html)

else:
    dbname=args.dbname
    server="mongoPrimary:27017"
    
    client = MongoClient(server)
    db = client[dbname]
    now = datetime.datetime.now()

    articleDB = db['sourceFeed']
    articleDB = db['article']
    
    all = feedsourceDB.find({"active": True, "protocol":"html"},no_cursor_timeout=False)    
    all = articleDB.find({'scraped': False},no_cursor_timeout=False)
    items=all.count()
    counter=0

    for feed in all:
                oid=feed['_id']
                url=feed['URL']
                site=feed['site']
		name=feed['name']
                if args.verbose:
                    print "FEED: ",site+"|"+name

# get page URL






        # Page cleanup

# Extract http links in page

# for each link
    # break link in components
    # add host part in relative links (host=='')
    # validate link or next
    # count unique internal links

# for each unique internal links
    # calculate pageratio
    # if accept save page
    #




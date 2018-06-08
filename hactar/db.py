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
import unicodedata
import httplib
import chardet
import socket
import datetime
import time
import urltools
import re
import hashlib
import urlparse
from time import mktime
from lxml.html.clean import Cleaner
from optparse import OptionParser



# populate feed sources db
def populateFeedSource(feedsourceDB,URL,homepage,site,active,protocol,name):
    from pymongo import MongoClient
    ts= datetime.datetime.utcnow()
    feedsourceDB.insert_one(
           {
               'dateAdded':ts,
               'URL':URL,
               'site':site,
               'active':active,
               'name':name,
               'protocol':protocol,
               'rating':'',
               'oldRating':'',
            }
     )

# log feed statistics and errors
def logFeed(feedlogDB,oid,site,name,num,url,exception):
        import json
        from pymongo import MongoClient
        ts = datetime.datetime.utcnow()
        feedlogDB.insert_one(
                {
                        'timestamp':ts,
                        'feedSourceOID':oid,
                        'feedSite':site,
                        'feedName':name,
                        'itemsFound':num,
                        'feedURL':url,
                        'exception':str(exception),
                }
        )

# store feed items in mongodb collection
def storeFeedItem(feeditemDB,oid,itemhash,url,site,name,title,link,published,author,summary):
        import json
        from pymongo import MongoClient
        feeditemDB.insert_one(
                        {
                                'itemTitle': title,
                                'feedSite': site,
                                'feedName': name,
                                'feedURL': url,
                                'itemLink': link,
                                'itemPublished': published,
                                'itemAuthor': author,
                                'itemSummary': summary,
                                'itemMD5hash': itemhash,
                                'collected': False,
                                'channel': "rss"
                        }
        )
        return(1)



# log 
def logArticle(articlelogDB, oid, published, source, link, http, realurl, textsize, code, headers):
    import json
    from pymongo import MongoClient
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
    import json
    from pymongo import MongoClient
    from bson import Binary
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


# update article with scraped text data
def storeArticleText (articleDB,oid,page):
    import datetime
    from pymongo import MongoClient

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

# update article: scraped 
def markArticleScraped (articleDB,oid,exception):
    import datetime
    from pymongo import MongoClient

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


# Store a hash of each string in page, 
def storeLineHash(lineHashDB,page):
    import md5
    import datetime

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


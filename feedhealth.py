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
import socket
import datetime
import time
import re
import hashlib
from pymongo import MongoClient

def classify_feed(items,periodA,periodB):
    # classify feed accesses according to feeds found (count will include
    # items already lounted in previous runs

    #  Classify feed health status
    # A: has items since periodA
    # B: has items since periodB
    # C: has items
    # D: DRY, no exceptions in last month, no articles in 1 year
    # P: exceptions in 1 month, no articles in 1 year

    excC = excB = excA =0
    itmC = itmB = itmA =0
    for itm in items:
        ts=itm['timestamp']
        found= itm['itemsFound']
        exception=itm['exception']

        itmC = itmC +found
        if exception != 'none':
            excC = excC +1
        if ts > periodB:
            itmB = itmB + found
            if exception != 'none':
                excB = excB +1
        if ts > periodA:
            itmA = itmA + found

    if itmC > 0:
        if itmA > 0:
            rate='A'
        elif itmB > 0 :
            rate='B'
        else:
            rate='C'
    else:
        if excB > 0:
            rate='D'
        else:
            rate='P'
    return(rate,itmA,itmB,itmC)

def classify(items,timestamp_field,periodA,periodB):
    # classify feed items and articles according to time
    #  Classify feed health status
    # A: has items since periodA
    # B: has items since periodB
    # C: has items in period C
    # D: DRY, no exceptions in periodB, no articles in periodC 

    itmC = itmB = itmA =0
    for itm in items:
        itmC = itmC +1 
        ts=itm[timestamp_field]
        if ts > periodB:
            itmB = itmB +1 
        if ts > periodA:
            itmA = itmA +1 
    if itmC > 0:
        if itmA > 0:
            rate='A'
        elif itmB > 0 :
            rate='B'
        else:
            rate='C'
    else:
        rate='D'
    return(rate,itmA,itmB,itmC)



# #
# MAIN
# #

reload(sys)
sys.setdefaultencoding('utf-8')
socket.setdefaulttimeout(10)

if (len(sys.argv[0].split('-'))<=1):
	print sys.argv[0],": invoke as ",sys.argv[0]+"-dbname"
       	quit()

(prog,dbname) = sys.argv[0].split('-',1)
server="mongoPrimary:27017"

client = MongoClient(server)
db = client[dbname]
now = datetime.datetime.now()

feedsourceDB = db['feedsource'+ str(now.year)]
articleDB = db['article'+str(now.year)]
feedlogDB = db['log_feed'+str(now.year)]
feeditemDB = db['feeditem'+str(now.year)]

#periodC = now.replace(year=now.year - 1)
periodC = now - datetime.timedelta(days=30)
periodB = now - datetime.timedelta(days=7)
periodA = now - datetime.timedelta(days=1)


# read feeds collection
feeds = feedsourceDB.find({"active": True},no_cursor_timeout=False)
# collect data in each feed
totalItems=0
totalArticles=0
contents=""
for feed in feeds:
    oid=feed['_id']
    site=feed['site']
    oldRating=feed['rating']
    name=feed['name']
    source="rss|"+site+"|"+name

    items = feedlogDB.find({'feedSite': site, 'feedName':name,'timestamp': {"$gte": periodC}})
    (feedClass,feedA,feedB,feedC)=classify_feed(items,periodA,periodB)

    items = feeditemDB.find({'feedSite': site, 'feedName':name,'itemPublished': {"$gte": periodC}})
    (itemClass,itemA,itemB,itemC)=classify(items,'itemPublished',periodA,periodB)
    totalItems=totalItems+itemC

    items = articleDB.find({'source':source, 'published': {"$gte": periodC}})
    (articleClass,artA,artB,artC)=classify(items,'published',periodA,periodB) 
    totalArticles=totalArticles+artC

    #itemShare=round((float(feedC)/float(totalItems))*100,2)
    #articleShare=round((float(artC)/float(totalArticles))*100,2)

    newRating=feedClass+itemClass+articleClass

    if oldRating != newRating:
        feedsourceDB.update({'_id':oid},
            {
                '$set': {
                    'rating': newRating,
                    'oldRating': oldRating,
                    },
            },
            upsert=True,
            multi=False)

        print  datetime.datetime.utcnow(), str(oldRating)+"->"+str(newRating)+'\t'+str(itemC)+'\t'+str(artC)+'\t',dbname+"|"+source

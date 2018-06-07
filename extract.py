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
import os
import re
import validators
import md5
import lxml
import unicodedata
import datetime
import httplib
import chardet
from bson import Binary
from pymongo import MongoClient
from lxml.html.clean import Cleaner
from lxml import etree, html
from argparse import ArgumentParser


reload(sys)
sys.setdefaultencoding('utf-8')

parser = ArgumentParser()
parser.add_argument("dbname", type=str,help='database name')
parser.add_argument("dir", type=str,help='target directory name')
parser.add_argument("-v", "--verbose", action="store_true", help="be chatty")
(args) = parser.parse_args()
if (not args.dbname) :
        print sys.argv[0], ": database name argument needed"
        quit()
dbname=args.dbname

try: 
        os.makedirs(args.dir)
except OSError:
       if not os.path.isdir(args.dir):
           raise
           quit()

server="mongoPrimary:27017"
client = MongoClient(server)
db = client[dbname]
now = datetime.datetime.now()

articleDB = db["article"]

all = articleDB.find({},no_cursor_timeout=False)
UTF8Writer = codecs.getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)

#sys.setdefaultencoding('utf-8')

for item in all:
    oid=str(item['_id'])
    code=item['encoding']
    code='utf-8'
    #fname='article'+str(datetime.datetime.now().year)+'-'+oid+'.txt'
    fname=args.dir+'/article'+'-'+oid+'.txt'
    f=open(fname, 'w+')
    sys.stdout = f
    f.write( u"oid: "+oid+"\n")
    f.write( u'source: ')
    f.write( item['source'].encode(code,'ignore'))
    f.write( "\n" )
    f.write( u"date: "+str(item['published'])+"\n" )
    f.write( u'author: ')
    f.write( item['author'].encode(code,'ignore'))
    f.write( "\n" )
    f.write( u"url: "+item['URL']+"\n" )
    f.write( u'title: ')
    f.write( item['title'].encode(code,'ignore'))
    f.write( "\n" )
    f.write( u'summary: ')
    f.write( item['summary'].encode(code,'ignore'))
    f.write( "\n" )
    f.write( u'text: ')
    f.write( item['text'].encode(code,'ignore'))
    f.write( "\n" )
    f.flush()
    f.close()

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
import datetime
import json
import time
import urltools
import urlparse
from pymongo import MongoClient
from argparse import ArgumentParser

from hactar.db import populateFeedSource


# #
# MAIN
# #

reload(sys)
sys.setdefaultencoding('utf-8')

parser = ArgumentParser()
parser.add_argument("dbname", type=str,help='database name')
parser.add_argument("-v", "--verbose", action="store_true", help="be chatty")
parser.add_argument("-i", "--interactive", action="store_true", dest="interactive")

(args) = parser.parse_args()
dbname=args.dbname


server="mongoPrimary:27017"

client = MongoClient(server)
db = client[dbname]
now = datetime.datetime.now()

feedsource="feedsource"
feedsourceDB = db[feedsource]

homepage=False
if args.interactive:
    site = raw_input('SITE (newspaper) ')  
    name = raw_input('feed name ')  
    URL = raw_input('feed URL ')  
    hp = raw_input('homepage (True/False) ')  
    protocol = raw_imput('protocol (rss|http)')
    if hp.lower == "true": 
         homepage = True
    if args.verbose: print site, name, URL, protocol, str(homepage)
    populateFeedSource(feedsourceDB,URL,homepage,site,True,protocol,name)
else:
    print "TAB separated values in stdin: site name Homepage:True/False protocol:(rss|http) url"
    for line in sys.stdin:
        (site,name,hp,protocol,URL)=line.strip().split("\t")
        if hp.lower == "true": 
                homepage= True
        if args.verbose: print site, name, URL, protocol, str(homepage)
        populateFeedSource(feedsourceDB,URL,homepage,site,True,protocol,name)



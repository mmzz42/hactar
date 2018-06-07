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


#page ratio sub
    #validate URL
    #get page
    #clean page (scrub)
    #for each a href path inside page


    #ratio: (textlenght/internal links)* url length * --# of dashes in url/ factor (500)



##
##MAIN
##

# get page URL
(html,http,code,r.url,r.headers,err)=geturl(url)

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




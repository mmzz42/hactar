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
import httplib
import chardet
import socket
import datetime
import json
import time
import urltools
import re
import hashlib
import urlparse
from time import mktime
from lxml.html.clean import Cleaner
from optparse import OptionParser



# collect entries in feeds or exceptions
def getFeed(url):
        import feedparser
        f=feedparser.parse(url)
        if f.bozo == 1 :
                if f["entries"]:
                        return (f.bozo,f["entries"],f.bozo_exception)
                else:
                        return (f.bozo,'',f.bozo_exception)
        else:
                return (f.bozo,f["entries"],"none")

# retrieve URL
def geturl(url):
        import codecs
        import unicodedata
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
        if (('content-type' not in r.headers) or ("text" not in r.headers['content-type'].lower())):
            print "[%s][%s][%s][%s]" % (http,r.encoding,code,str(r.headers))
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


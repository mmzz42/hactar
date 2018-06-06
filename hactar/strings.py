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





# normalize strings avoiding duplicate blanks, vertical spacing, etc
def normalize(each):
    import re
    
    each = each.replace(u'\n', '',re.UNICODE| re.MULTILINE) # remove newlines
    each = each.replace(u'\r', '',re.UNICODE| re.MULTILINE) # remove linefeed
    each = each.replace(u'\t', ' ',re.UNICODE| re.MULTILINE) # remove tabs
    each = each.replace(u'^\s+', '',re.UNICODE) # remove leading whitespace
    each = each.replace(u'\s+$', '',re.UNICODE) # remove trailing whitespace
    each = " ".join(re.split("\s+", each, flags=re.UNICODE))
    cleanr = re.compile('<.*?>')
    text = re.sub(cleanr, '', each)
    return(text)


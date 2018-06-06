#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import chardet

def monkey_patch():
    prop = requests.models.Response.content
    def content(self):
        _content = prop.fget(self)
        if self.encoding == 'ISO-8859-1':
            encodings = requests.utils.get_encodings_from_content(_content)
            if encodings:
                self.encoding = encodings[0]
            else:
                self.encoding = chardet.detect(_content)['encoding']

            if self.encoding:
                _content = _content.decode(self.encoding, 'replace').encode('utf8', 'replace')
                self._content = _content
                self.encoding = 'utf8'

        return _content
    requests.models.Response.content = property(content)

monkey_patch()


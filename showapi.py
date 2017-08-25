#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib2
import urllib
import json
import hashlib
import time


def zh2py(content):
    show_api_appid = "44703"
    show_api_timestamp = time.strftime("%Y%m%d%H%M%S", time.localtime())
    show_api_secret = "b1e4c9dfa292465a96041b3b8888de15"
    md5str = "content" + content + \
             "showapi_appid" + show_api_appid + \
             "showapi_timestamp" + show_api_timestamp + show_api_secret
    md5obj = hashlib.md5()
    md5obj.update(md5str)
    show_api_sign = md5obj.hexdigest().upper()
    url = "http://route.showapi.com/99-38"
    send_data = urllib.urlencode([
        ('showapi_appid', show_api_appid)
        , ('showapi_sign', show_api_sign)
        , ('content', content)
        , ('showapi_timestamp', show_api_timestamp)

    ])

    req = urllib2.Request(url)
    try:
        response = urllib2.urlopen(req, data=send_data.encode('utf-8'), timeout=10)
        result = response.read().decode('utf-8')
        result_json = json.loads(result)
        res = result_json.get('showapi_res_body').get('data')
        letters = res.split(' ')
        statement = ''
        for l in letters:
            L = l.upper()
            newl = L[0]+l[1:]
            statement += newl
        print res
        print statement
    except Exception as e:
        print e.message

if __name__ == '__main__':
    zh2py("你好")

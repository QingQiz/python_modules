#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from . import *

loginUrl = 'https://uis.nwpu.edu.cn/cas/login'


def login(username, password, s=None):
    if s is None:
        s = requests.Session()

    req(loginUrl, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
    }, s=s)

    req(loginUrl, data={
        'username': username,
        'password': password,
        'currentMenu': 1,
        'execution': 'e1s1',
        '_eventId': 'submit',
    }, s=s)
    return s

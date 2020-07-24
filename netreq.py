#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import requests


def login_aoxiang(username, password):
    url = 'https://uis.nwpu.edu.cn/cas/login'

    s = requests.Session()

    s.headers.update({
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
        "Origin": "https://uis.nwpu.edu.cn",
    })

    s.get(url)
    s.get(url)

    form_data = {
        'username': username,
        'password': password,
        'currentMenu': 1,
        'execution': 'e2s1',
        '_eventId': 'submit',
        'geolocation': '',
        'submit': 'One moment please...'
    }
    r = s.post(url, data=form_data)

    return s

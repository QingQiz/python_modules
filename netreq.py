#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import requests
import parallel


def login_aoxiang(username, password, s=None):
    url = 'https://uis.nwpu.edu.cn/cas/login'

    if s is None:
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


def url_content(url, encoding='', headers={}, data={}, params={}, s=None):
    if s is None:
        s = requests.Session()

    s.headers.update(headers)

    r = s.post(url, data=data, params=params)

    if r.encoding:
        r.encoding = encoding

    return r.content


def url_html(url, encoding='', headers={}, data={}, params={}, s=None):
    if s is None:
        s = requests.Session()

    s.headers.update(headers)

    r = s.post(url, data=data, params=params)

    if r.encoding:
        r.encoding = encoding

    return r.text


def url_json(url, encoding='', headers={}, data={}, params={}, s=None):
    if s is None:
        s = requests.Session()

    s.headers.update(headers)

    r = s.post(url, data=data, params=params)

    if r.encoding:
        r.encoding = encoding

    return r.json()


def urls_content(urls, encoding='', headers={}, data={}, params={}, s=None, job=8):
    if s is None:
        s = requests.Session()

    params = [[url, encoding, headers, data, params, s] for url in urls]

    return parallel.init(job)(url_content, params)


def urls_html(urls, encoding='', headers={}, data={}, params={}, s=None, job=8):
    if s is None:
        s = requests.Session()

    params = [[url, encoding, headers, data, params, s] for url in urls]

    return parallel.init(job)(url_html, params)


def urls_json(urls, encoding='', headers={}, data={}, params={}, s=None, job=8):
    if s is None:
        s = requests.Session()

    params = [[url, encoding, headers, data, params, s] for url in urls]

    return parallel.init(job)(url_json, params)

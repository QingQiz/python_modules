#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from .. import parallel


def req(url, headers={}, data={}, params={}, encoding='', s=None):
    '''
    :param str url: url
    :param dict headers: headers
    :param dict data: post data
    :param dict params: get parameters
    :param requests.Session s: session to use
    :return: requests.request
    '''
    if s is None:
        s = requests.Session()

    s.headers.update(headers)

    if data:
        r = s.post(url, data=data)
    else:
        r = s.get(url, params=params)

    if encoding:
        r.encoding = encoding

    return r


def url_content(url, encoding='', headers={}, data={}, params={}, s=None):
    r = req(url, headers, data, params, s)

    if r.encoding:
        r.encoding = encoding

    return r.content


def url_html(url, encoding='', headers={}, data={}, params={}, s=None):
    r = req(url, headers, data, params, s)

    if r.encoding:
        r.encoding = encoding

    return r.text


def url_json(url, encoding='', headers={}, data={}, params={}, s=None):
    r = req(url, headers, data, params, s)

    if r.encoding:
        r.encoding = encoding

    return r.json()


def urls_content(urls, encoding='', headers={}, data={}, params={}, s=None, job=8):
    params = [[url, encoding, headers, data, params, s] for url in urls]
    return parallel.init(job)(url_content, params)


def urls_html(urls, encoding='', headers={}, data={}, params={}, s=None, job=8):
    params = [[url, encoding, headers, data, params, s] for url in urls]
    return parallel.init(job)(url_html, params)


def urls_json(urls, encoding='', headers={}, data={}, params={}, s=None, job=8):
    params = [[url, encoding, headers, data, params, s] for url in urls]
    return parallel.init(job)(url_json, params)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class SoundCloud():
    def __init__(self, session=None):
        import requests, re
        from . import url_html

        if not session:
            self.session = requests.Session()

        x = url_html('http://soundcloud.com', s=self.session)
        x = re.findall(r'script crossorigin src="(.+?)"></script>', x)

        x = url_html(x[-1], s=self.session)
        self.apiKey = re.search(r'client_id:"(.+?)"', x).group(1)
        self._resource = None

    def req(self, url, headers={}, data={}, params={}, encoding=''):
        '''
        make a request with current session
        '''
        from . import req as netreq

        return netreq(url, headers=headers, data=data, params=params, s=self.session)

    def search(self, q, offset=0, limit=20):
        url = 'https://api-v2.soundcloud.com/search'

        tracks = self.req(url, encoding='utf-8', params={
            'q': q,
            'client_id': self.apiKey,
            'limit': 20,
            'offset': 0
        }).json()

        return [i for i in tracks['collection'] if i.get('kind') in ['playlist', 'track']]

    @property
    def resource(self):
        return self._resource

    def completeResource(self):
        import functools
        from . import urls_json

        info = resource['tracks'] if resource.get('track_count') else [resource]

        ids = [i['id'] for i in info if i.get('comment_count') is None]
        ids = list(map(str, ids))
        ids_split = ['%2C'.join(ids[i:i+10]) for i in range(0, len(ids), 10)]
        api_url = 'https://api-v2.soundcloud.com/tracks?ids={ids}&client_id={client_id}&%5Bobject%20Object%5D=&app_version=1584348206&app_locale=en'

        urll = [api_url.format(ids=ids, client_id=client_id) for ids in ids_split]

        res = urls_json(urll, s=self.session)

        if res:
            res = functools.reduce(operator.iconcat, res)

        res = iter(res)

        info = [next(res) if i.get('comment_count') is None else i for i in info]

        self._resource = info
        return info

    def getResource(self, resourceUrl):
        import re, json

        r = self.req(resource_url, encoding='utf-8').text

        x = re.escape('forEach(function(e){n(e)})}catch(t){}})},')
        x = re.search(r'' + x + r'(.*)\);</script>', r)

        info = json.loads(x.group(1))[-1]['data'][0]

        self._resource = info
        return self.completeResource()

    def getM3U8(self):
        raise NotImplementedError('TODO')








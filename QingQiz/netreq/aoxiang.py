#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def table2json(html, tableIndex=-1):
    '''
    covert table in html to json like
        [
            {
                'table head1': 'table value1'
                'table head2': 'table value2'
                'table head3': 'table value3'
            },
        ]
    '''
    import re

    table = re.findall(r'<table.*?</table>', html, re.DOTALL)[-1]
    # do not set regex to r'<th.*>(.*?)</th>', this will match <thead>...<th>...</th>
    tableHeader = re.findall(r'<th .*?>(.*?)</th>', table, re.DOTALL)

    tableRows = re.findall(r'<tr.*?>(.*?)</tr>', table, re.DOTALL)[1:]
    if not tableRows: return None
    if len(tableRows) == 1 and tableRows[0].strip() == '': return None

    def row2data(row):
        '''
        row may like:
            \t\t<td>20xx-20xx X</td>\r
            \t\t<td>UXXXXXXXX</td>\r
            \t\t<td>UXXXXXXXX.XX</td>\r
            <td>\t\t\t\t<a href="javascript:void(0)"  onclick="showInfo(xxxxxxxx)" >XXXXXXX</a>\r
            \t\t\r
            \t\t</td>\r
            <td>XXXXXXXXX</td>\t\t<td>xxx</td>\r
            <td style=""></td><td style=""></td><td style="">\t  \t\t\txx \r
            </td><td style="">\t  \t\t\txx \r\n</td><td style="">\t\t\t\txx\r\n\t\t\t\r
            </td><td>\t\t\t\t\txx\r
            \t\t\t\r\n</td>\t\t\r

        '''
        res = []
        for data in re.findall(r'<td.*?>(.*?)</td>', row, re.DOTALL):
            if data.find('href') != -1:
                data = re.search(r'>(.*?)</a>', data, re.DOTALL).group(1)
            res.append(data.strip())
        return res

    # tableData: [[data, data]]
    tableData = list(map(row2data, tableRows))
    # [{key: data}]
    return [{tableHeader[i]: rowData[i] for i in range(len(tableHeader))} for rowData in tableData]


class Aoxiang():
    _termId = None

    def __init__(self, username, password, session=None):
        '''
        :param username: username to uis.nwpu.edu.cn
        :param password: password to uis.nwpu.edu.cn
        :param session: session to use, None to create a new session
        '''
        import requests
        from . import req

        if session is None:
            self.session = requests.Session()
        else:
            self.session = session

        # login to uis.nwpu.edu.cn
        loginUrl = 'https://uis.nwpu.edu.cn/cas/login'
        req(loginUrl, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
        }, s=self.session)

        req(loginUrl, data={
            'username': username,
            'password': password,
            'currentMenu': 1,
            'execution': 'e1s1',
            '_eventId': 'submit',
        }, s=self.session)

        '''
        if login successed, cookies will be:
            {
                'SESSION': 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
                'TGC': 'TGT-aaaaa-aaaaaaaaaaaaaaaaaa-aaaaaaaaaaa-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaacas-server-site-webapp-aaaaaaaaa-aaaaa'
            }
        '''
        assert self.session.cookies.get_dict().get('TGC'), 'wrong username or password'

        # login to us.nwpu.edu.cn
        self.req("http://us.nwpu.edu.cn/eams/sso/login.action")

        '''
        if login successed, cookies will be:
            {
                'SESSION': 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
                'TGC': 'TGT-aaaaa-aaaaaaaaaaaaaaaaaa-aaaaaaaaaaa-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaacas-server-site-webapp-aaaaaaaaa-aaaaa',
                'GSESSIONID': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                'JSESSIONID': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
            }
        '''
        assert self.session.cookies.get_dict().get('GSESSIONID'), 'login to us.nwpu.edu.cn failed.'

        # switch language of us.nwpu.edu.cn to Chinese
        self.req('http://us.nwpu.edu.cn/eams/home.action', data={
            "session_locale": "zh_CN"
        })

    def req(self, url, headers={}, data={}, params={}):
        '''
        make a request with current session
        '''
        import re
        from . import req as netreq

        while True:
            r = netreq(url, headers=headers, data=data, params=params, s=self.session)
            if re.search(r'请不要过快点击', r.text) is not None:
                __import__('time').sleep(0.5)
                continue
            return r

    @property
    def termId(self):
        '''
        :return:
            {
                'term1': [id1, id2, ...],
                ...
            }
        '''
        import re
        from .. import parallel

        if self._termId:
            return self._termId

        res = self.req('http://us.nwpu.edu.cn/eams/dataQuery.action', data={
            'dataType': 'semesterCalendar',
            'value': 98,
            'empty': False
        }).text

        # dicts: ['{id:xx,schoolYear:"20xx-20xx",name:"X"}']
        dicts = re.findall(r'{(.*?)}', res)

        def searchAll(s, regexes):
            res = []
            for regex in regexes:
                res += re.findall(regex, s)
            return res

        # info: [[id, schoolYear, name]]
        info = parallel.init(8)(lambda x: searchAll(x, [r'id:(.*?),', r'"(.*?)"']), [[i] for i in dicts], thread=False)

        res = {}
        for i in info:
            term = i[1].split('-')[0][-2:]
            if res.get(term):
                res[term].append(i[0])
            else:
                res[term] = [i[0]]
        self._termId = res

        return res

    def grade(self, *terms):
        '''
        :param list(int) terms: which term grade to get, set [] to get all terms' grade, for example: grade(17, 18)
        :return: for example:
            [
                [
                    {
                        '学年学期': '20xx-20xx X',
                        '课程代码': 'Uxxxxxxxx',
                        '课程序号': 'Uxxxxxxxx.xx',
                        '课程名称': 'XXXXXXX',
                        '课程类别': 'XXXXXX',
                        '学分': 'xx',
                        '平时成绩': 'xx',
                        '期中成绩': 'xx',
                        '实验成绩': 'xx',
                        '期末成绩': 'xx',
                        '总评成绩': 'xx',
                        '最终': 'xx',
                        '绩点': 'xx'
                    }
                ]
            ]
        '''
        import re, functools
        from .. import parallel

        if terms:
            termId = self.termId

            gradeUrl = "http://us.nwpu.edu.cn/eams/teach/grade/course/person!search.action?semesterId="

            # foldl (\zero x -> zero + termId[x]) term []
            idSpace = functools.reduce(lambda x, y: x + termId[str(y)], terms, [])

            # us.nwpu.edu.cn won't return data if request too fast
            # therefore we cannot request data in parallel
            htmls = [self.req(gradeUrl + str(i)).text for i in idSpace]

            # parse html to json in parallel
            res = parallel.init(8)(table2json, [[html] for html in htmls], thread=False)
        else:
            allGradeUrl = "http://us.nwpu.edu.cn/eams/teach/grade/course/person!historyCourseGrade.action"

            html = self.req(allGradeUrl).text
            res = [table2json(html)]

        return [i for i in res if i]

    def examInformations(self, *terms):
        '''
        :param list(int) terms: terms, for example: examInformations(17, 18)
        :return: for example
            {
                '20xx-20xx学年x学期xxxx': [
                    {
                        '课程序号': 'UXXXXXXXX.XX',
                        '课程名称': 'XXXXX',
                        '考试类型': 'XXXX',
                        '考试日期': '20xx-xx-xx',
                        '考试时间': 'xx:xx~xx:xx',
                        '考场校区': 'xx校区',
                        '考场教学楼': 'XXXXXX',
                        '考场教室': 'xxxxxx',
                        '考试情况': '正常',
                        '其它说明': ''
                    }
                ]
            }
        '''
        import re, functools

        examTableUrl = 'http://us.nwpu.edu.cn/eams/stdExamTable!examTable.action?examBatch.id='

        # same as: concatMap (\x -> termId[x]) terms
        termIds = functools.reduce(lambda zero, x: zero + self.termId[str(x)], terms, [])

        tableIds = []
        for termId in termIds:
            r = self.req('http://us.nwpu.edu.cn/eams/stdExamTable.action', data={
                'semester.id': termId
            })
            tableIds += re.findall(r'option value="(.*?)".*?>(.*?)</option>', r.text)
        # tableIds will be: {'501': '2019-2020学年秋学期期中考试', '482': '2019-2020秋课程考试', '481': '2019-2020秋补考', ...}
        tableIds = dict(tableIds)

        res = {}
        for tableId in tableIds:
            html = self.req(examTableUrl + tableId).text
            json = table2json(html)

            if json:
                res[tableIds[tableId]] = json
        return res

    def classTable(self, timeStart=None, timeEnd=None):
        '''
        :param timeStart: class time begin date, for example: 2020-08-01, default: today
        :param timeEnd: class time end date, for example: 2020-10-01, default: today + 360 days
        :return:
            [
                {
                    'allDay': 'x',
                    'description': 'null',
                    'end': '20xx-xx-xx xx:xx:xx',
                    'location': '[XXXXXX]XXXXXX',
                    'recurrenceType': 'x',
                    'repeatEnd': 'x',
                    'repeatEndDate': '20xx-x-xx xx:xx:xx',
                    'repeatEndTimes': 'x',
                    'repeatFrequencyDay': '',
                    'repeatFrequencyMonth': '',
                    'repeatFrequencyMonthDay': '',
                    'repeatFrequencyWeek': '',
                    'repeatFrequencyWeekDay': '',
                    'repeatFrequencyYear': '',
                    'repeatFrequencyYearDay': '',
                    'repeatFrequencyYearMonth': '',
                    'start': '20xx-xx-xx xx:xx:xx',
                    'startTime': '20xxxxxxxxxx00',
                    'stopTime': '20xxxxxxxxxx00',
                    'title': 'XXXXXXXXXXXX'
                }
            ]
        '''
        import datetime

        # login to ecampus.nwpu.edu.cn
        self.req('https://ecampus.nwpu.edu.cn/portal-web/html/index.html')
        accessToken = self.session.cookies.get_dict().get('access_token')

        if timeStart is None:
            timeStart = datetime.date.today().strftime('%Y-%m-%d')
        if timeEnd is None:
            timeEnd = (datetime.date.today() + datetime.timedelta(days=360)).strftime('%Y-%m-%d')

        apiUrl = f'https://ecampus.nwpu.edu.cn/portal-web/api/proxy/calendar/api/personal/schedule/getEduEvents?startDate={timeStart}&endDate={timeEnd}&access_token={accessToken}'

        res = self.req(apiUrl).json()

        assert res['status'] == 'OK', 'wrong response status, error message: ' + res['message']
        return res['data']['events'][2]
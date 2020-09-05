#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class Aoxiang():
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
        self.username = username

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
        loginUrl = "http://us.nwpu.edu.cn/eams/sso/login.action"
        req(loginUrl, s=self.session)

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
        req('http://us.nwpu.edu.cn/eams/home.action', data={
            "session_locale": "zh_CN"
        }, s=self.session)

    def grade(self, term=[]):
        '''
        :param int term: which term grade to get, set [] to get all terms' grade, for example term=[17, 18]
        :return: [[{key: data}]]
            key: '学年学期', '课程代码', '课程序号', '课程名称', '课程类别', '学分', '平时成绩', '实验成绩', '期末成绩', '总评成绩', '最终', '绩点'
        '''
        import re
        from . import url_html
        from .. import parallel

        def table2json(html):
            '''
            covert the last table in html to json like
                [
                    {
                        'table head1': 'table value1'
                        'table head2': 'table value2'
                        'table head3': 'table value3'
                    },
                ]
            '''
            table = re.findall(r'<table.*?</table>', html, re.DOTALL)[-1]
            # do not set regex to r'<th.*>(.*?)</th>', this will match <thead>...<th>...</th>
            tableHeader = re.findall(r'<th .*?>(.*?)</th>', table, re.DOTALL)

            tableRows = re.findall(r'<tr.*?>(.*?)</tr>', table, re.DOTALL)[1:]
            if not tableRows: return None

            def row2data(row):
                '''
                row may like this:
                    \t\t<td>20xx-20xx X</td>\r
                    \t\t<td>UXXXXXXXX</td>\r
                    \t\t<td>UXXXXXXXX.XX</td>\r
                    <td>\t\t\t\t<a href="javascript:void(0)"  onclick="showInfo(xxxxxxxx)" title="查看成绩详情" >XXXXXXX</a>\r
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


        if term:
            gradeUrl = "http://us.nwpu.edu.cn/eams/teach/grade/course/person!search.action?semesterId="
            # table id: current_term (上学期), current_term + 18 (下学期)
            # current term: current_year % 100
            idSpace = [i % 100 for i in term] + [i % 100 + 18 for i in term]

            htmls = []
            for i in idSpace:
                while True:
                    uri = gradeUrl + str(i)
                    html = url_html(uri, s=self.session)

                    # us.nwpu.edu.cn won't return data if request too fast
                    # therefore we cannot request data in parallel
                    if re.search(r'请不要过快点击', html) is not None:
                        __import__('time').sleep(0.5)
                    else:
                        htmls.append(html)
                        __import__('time').sleep(0.5)
                        break

            # parse html to json in parallel
            res = parallel.init(8)(table2json, [[html] for html in htmls], thread=False)
        else:
            allGradeUrl = "http://us.nwpu.edu.cn/eams/teach/grade/course/person!historyCourseGrade.action"

            html = url_html(allGradeUrl, s=self.session)
            res = [table2json(html)]

        return [i for i in res if i]


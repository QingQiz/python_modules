#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def table2json(html, tableIndex=-1, dataFixer=None):
    '''covert table in html to json
    :param html: html include <table> </table>
    :param tableIndex: which table to parse
    :param rowFixer: function to fix table data, for example: `lambda x: return x.replace('xxx', 'yyy')`
    :return: for example:
        [
            {
                'table head1': 'table value1'
                'table head2': 'table value2'
                'table head3': 'table value3'
            }
        ]
    '''
    import re

    if dataFixer is None:
        dataFixer = lambda x: x

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
        return [dataFixer(data) for data in re.findall(r'<td.*?>(.*?)</td>', row, re.DOTALL)]

    # tableData: [[data, data]]
    tableData = list(map(row2data, tableRows))
    # [{key: data}]
    return [{tableHeader[i]: rowData[i] for i in range(len(tableHeader))} for rowData in tableData]


class Aoxiang():
    _termId = None
    _xIdToken = None
    _userInfo = None
    _accessToken = None

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
        assert self.session.cookies.get_dict().get('TGC'), 'login failed'

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

    @property
    def accessToken(self):
        '''
        access_toke for some apis of ecampus.nwpu.edu.cn
        '''
        if self._accessToken:
            return self._accessToken

        self.req('https://ecampus.nwpu.edu.cn/portal-web/html/index.html')
        self._accessToken = self.session.cookies.get_dict().get('access_token')
        return  self._accessToken

    @property
    def xIdToken(self):
        '''
        x-id-token for some apis of personal-center.nwpu.edu.cn
        '''
        if self._xIdToken:
            return self._xIdToken

        self._xIdToken = self.fullUserInfo['idTokenJWT']
        return self._xIdToken

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
        '''term to termId
        :return:
            {
                '学期': [秋学期Id, 春学期Id, 夏学期Id],
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

    @property
    def fullUserInfo(self):
        '''get full user infomation
        :return: please try it
        '''
        import re

        if self._userInfo:
            return self._userInfo

        # 学生信息，这块在翱翔门户里
        res = self.req(f'https://ecampus.nwpu.edu.cn/portal-web/api/rest/portalUser/selectUserInfoByCurrentUser', params={
            'access_token': self.accessToken
        }, headers={'Accept': 'application/json, text/javascript, */*; q=0.01'}).json()
        assert res['status'] == 'OK', 'error on request, message: ' + res['message']

        # 学籍信息，这块在教务系统里
        tables = self.req('http://us.nwpu.edu.cn/eams/stdDetail.action').text

        action = re.findall(r"bg.Go\('(.*?)'", tables)
        if action != []:
            tables = self.req('http://us.nwpu.edu.cn' + action[0]).text

        tables = re.findall(r'<table.*?>(.*?)</table>', tables, re.DOTALL)

        studentStatus = re.findall(r'<td.*?class="title".*?>(.*?)</td>.*?<td.*?>(.*?)</td>', tables[0], re.DOTALL)
        contact = re.findall(r'<td class.*?>(.*?)</td>[\n\t\r\s]*?<td.*?>(.*?)</td', tables[-2], re.DOTALL)

        procData = lambda data: dict(map(lambda x: (x[0].replace('：', ''), x[1]), data))

        studentStatus = procData(studentStatus)
        del studentStatus['']
        contact = procData(contact)

        res['studentStatus'] = studentStatus
        res['contact'] = contact

        self._userInfo = res
        return self._userInfo

    @property
    def userInfo(self):
        '''get user information
        :return: please try it
        '''
        res = self.fullUserInfo

        return {
            "basicInformation": {
                'id': res['data']['userInfo']['id'],
                'name': res['data']['userInfo']['name'],
                'gender': '男' if res['data']['userInfo']['gender'] == 1 else '女',
                'mobile': res['data']['userInfo']['mobile'],
                'email': res['data']['userInfo']['email'],
                res['data']['userInfo']['identityType']: res['data']['userInfo']['identityNo'],
                'org': res['data']['org']['name'],
                'securityUserType': res['data']['securityUserType']['name']
            },
            "studentStatus": res['studentStatus'],
            "contact": res['contact'],
        }

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

        def dataFixer(data: str):
            if data.find('href') != -1:
                return re.search(r'>(.*?)</a>', data, re.DOTALL).group(1)
            return data.strip()

        if terms:
            termId = self.termId

            gradeUrl = "http://us.nwpu.edu.cn/eams/teach/grade/course/person!search.action?semesterId="

            # foldl (\zero x -> zero + termId[x]) term []
            idSpace = functools.reduce(lambda x, y: x + termId[str(y)], terms, [])

            # us.nwpu.edu.cn won't return data if request too fast
            # therefore we cannot request data in parallel
            htmls = [self.req(gradeUrl + str(i)).text for i in idSpace]

            # parse html to json in parallel
            res = parallel.init(8)(lambda x: table2json(x, dataFixer=dataFixer), [[html] for html in htmls], thread=False)
        else:
            allGradeUrl = "http://us.nwpu.edu.cn/eams/teach/grade/course/person!historyCourseGrade.action"

            html = self.req(allGradeUrl).text
            res = [table2json(html, dataFixer=dataFixer)]

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

        def dataFixer(data: str):
            if data.find('未安排的') != -1:
                return None
            if data.find('href') != -1:
                return re.search(r'>(.*?)</a>', data, re.DOTALL).group(1)
            return data.strip()

        res = {}
        for tableId in tableIds:
            html = self.req(examTableUrl + tableId).text
            json = table2json(html, dataFixer=dataFixer)

            if json:
                res[tableIds[tableId]] = json
        return res

    def myCourses(self, term):
        '''get my course information
        :param int term: term
        :return: for example:
            [
                {
                    '学分': 'x',
                    '序号': 'x',
                    '操作': '',
                    '教学大纲': 'xxxxxxx',
                    '教师': 'xxxxxx',
                    '校区': 'xxxx',
                    '考试类型': 'xxxx',
                    '课程介绍': '课程链接：https://xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
                    '课程代码': 'Uxxxxxxxx',
                    '课程名称': 'xxxx',
                    '课程安排': '',
                    '课程序号': 'Uxxxxxxxx.xx',
                    '起止周': 'x-x'
                }
            ]
        '''
        import re

        def dataFixer(data: str):
            data = data.replace('<br>', '\n').strip()

            if data.find('href') != -1:
                return re.search(r'>(.*?)</a>', data, re.DOTALL).group(1)
            return data

        ids = self.req('http://us.nwpu.edu.cn/eams/courseTableForStd.action').text
        ids = re.search(r'"ids","([0-9]+)"', ids).group(1)

        res = []
        for t in self.termId[str(term)]:
            json = table2json(self.req('http://us.nwpu.edu.cn/eams/courseTableForStd!courseTable.action', data={
                'ignoreHead': 1,
                'setting.kind': 'std',
                'startWeek': 1,
                'semester.id': t,
                'ids': ids
            }).text, dataFixer=dataFixer)
            res += json if json else []
        return res

    def classTable(self, timeStart=None, timeEnd=None):
        '''get classtable in json format
        :param timeStart: class time begin date, for example: 2020-08-01, default: today
        :param timeEnd: class time end date, for example: 2020-10-01, default: today + 180 days
        :return:
            [
                {
                    'allDay': 'x',
                    'description': 'null',
                    'end': '20xx-xx-xx xx:xx:xx',
                    'location': '[XXXXXX]XXXXXX',
                    'start': '20xx-xx-xx xx:xx:xx',
                    'startTime': '20xxxxxxxxxx00',
                    'stopTime': '20xxxxxxxxxx00',
                    'title': 'XXXXXXXXXXXX'
                }
            ]
        '''
        import datetime, functools, json, re
        from .. import parallel

        timeFormat = '%Y-%m-%d'

        if timeStart is None:
            timeStart = datetime.date.today().strftime(timeFormat)
        if timeEnd is None:
            timeEnd = (datetime.date.today() + datetime.timedelta(days=180)).strftime(timeFormat)

        # NOTE 这个 API 有问题：当时间间隔超过一周的时候返回的数据会出BUG，所以需要分块请求
        start = datetime.datetime.strptime(timeStart, timeFormat)
        end = datetime.datetime.strptime(timeEnd, timeFormat)

        params = []
        while start < end:
            nextStart = start + datetime.timedelta(days=6)

            l = start.strftime(timeFormat)
            r = (nextStart if nextStart <= end else end).strftime(timeFormat)
            params.append([l, r])

            start = nextStart + datetime.timedelta(days=1)

        def reqTable(l, r):
            res = self.req('https://ecampus.nwpu.edu.cn/portal-web/api/proxy/calendar/api/personal/schedule/getEduEvents', params={
                'startDate': l,
                'endDate': r,
                'access_token': self.accessToken
            }).json()

            assert res['status'] == 'OK', 'wrong response status, error message: ' + res['message']
            return res['data']['events'][2]

        # request data in parallel
        ret = parallel.init(16)(reqTable, params)

        ret = sorted(functools.reduce(lambda zero, x: zero + x, ret, []), key=lambda x: x['startTime'])

        for i in ret:
            toDel = [j for j in i if j[:2] == 're']
            for x in toDel:
                del i[x]
            i['location'] = re.sub(r'(\[.*?\])(.*)', r'\2', i['location'])
        ret = [json.dumps(i) for i in ret]
        ret = list(dict.fromkeys(ret))
        ret = [json.loads(i) for i in ret]
        return ret

    def courseInquiry(self, **kwargs):
        '''get class information
        for example:
            self.classInformation(**{'lesson.no': 'xxx'})
        possiable parameters:
            lesson.no:  课程序号 see `self.termId`
            lesson.course.name: 课程名称
            lesson.courseType.name: 课程类别
            lesson.teachDepart.name: 开设院系
            lesson.teachClass.name: 教学班
            teacher.name: 教师
            lesson.course.period: 总课时
            lesson.teachClass.limitCount: 上限
            lesson.上课时间: 上课时间
            lesson.上课地点: 上课地点
            lesson.course.credits: 学分
            lesson.coursePeriod: 学时/周
            lesson.project.id: 1
            lesson.semester.id: 学期Id, 参见 `self.termId`
        request example:
            curl $'http://us.nwpu.edu.cn/eams/stdSyllabus\u0021search.action' \
                -H 'Cookie: semester.id=98; JSESSIONID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx; GSESSIONID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' \
                --data-raw 'lesson.no=&lesson.course.name=&lesson.courseType.name=&lesson.teachDepart.name=&lesson.teachClass.name=&teacher.name=&lesson.course.period=&lesson.teachClass.limitCount=&lesson.%E4%B8%8A%E8%AF%BE%E6%97%B6%E9%97%B4=&lesson.%E4%B8%8A%E8%AF%BE%E5%9C%B0%E7%82%B9=&lesson.course.credits=&lesson.coursePeriod=&lesson.project.id=1&lesson.semester.id=98&_=1599306961924'
        '''
        raise NotImplementedError("TODO")

    def classInformation(self, classId):
        '''
        request example:
            curl $'http://us.nwpu.edu.cn/eams/stdSyllabus\u0021info.action' \
                -H 'Cookie: semester.id=98; JSESSIONID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx; GSESSIONID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' \
                --data-raw 'lesson.project.id=1&lesson.semester.id=98&_=1599308698360&params=lesson.project.id%3D1%26lesson.semester.id%3D98%26_%3D1599308698360&lesson.id=130702'
            params is the form data in `courseInquiry`
            NOTE: most important parameter is lesson.id and semester.id
        '''
        raise NotImplementedError("TODO")

    def yqtb(self, location='学校'):
        '''疫情填报，叫 yqtb 的原因是他的那个 sb 域名是 yqtb

        :param location: 所在地: 西安、学校或你所在的位置如: 龙游县、鸠江区、镇沅彝族哈尼族拉祜族自治县
        :return:
            {
                'state': '您已提交今日填报重新提交将覆盖上一次的信息。',
                '当前所在位置': '在学校',
                '今天的体温范围': '37.3度以下',
                '您有无疑似症状?（可多选）': '无',
                '西安市一码通状态': '绿码'
            }
        '''
        import re, json

        uid    = self.userInfo['basicInformation']['id']
        name   = self.userInfo['basicInformation']['name']
        mobile = self.userInfo['basicInformation']['mobile']
        org    = self.userInfo['basicInformation']['org']

        locationDict = {
            "学校": "1",
            "西安": "2"
        }

        otherDict = self.req('http://yqtb.nwpu.edu.cn/wx/js/eams.area.data.js')
        otherDict = re.findall(r'{(.*)}', otherDict.text, re.DOTALL)[0]
        otherDict = json.loads('{' + otherDict + '}')
        otherDict = {k: v for v, k in otherDict.items()}

        locationDict = {**locationDict, **otherDict}

        self.locationDict = locationDict

        assert locationDict[location] is not None, "No such place: " + location

        data   = {
            "xasymt": "1",              # 西安市一码通
            "actionType": "addRbxx",
            "userLoginId": uid,
            "fxzt": "9",                # 返校状态
            "userType": "2",            # 猜不出来
            "userName": name,
            "szcsbm": locationDict[location],   # 所咋城市编码
            "szcsmc": location,         # 所在城池名称（为啥是在学校啊） FIXME 这块似乎得加上省和城市名，懒得改了....
            "sfyzz": "0",               # 是否有症状
            "sfqz": "0",                # 是否确诊
            "tbly": "sso",              # 填报(？留言)
            "qtqksm": "",               # 其它情况说明
            "ycqksm": "",               # ？？情况说明
            "qrlxzt": "",               # 确认离（？留）校状态
            "xymc": org,                # 学院名称
            "xssjhm": mobile,           # 学生手机号码
        }

        self.req('http://yqtb.nwpu.edu.cn/')
        self.req('http://yqtb.nwpu.edu.cn/wx/ry/ry_util.jsp', data=data, headers={
            "Referer": "http://yqtb.nwpu.edu.cn/wx/ry/jrsb.jsp",
            "Origin": "http://yqtb.nwpu.edu.cn",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        })

        r = self.req('http://yqtb.nwpu.edu.cn/wx/ry/jrsb.jsp')

        x = re.findall(r'(?<!>)\n.*div.*weui-cells__title">(.*)</div>', r.text)
        x = list(filter(lambda x: '时间' not in x and '说明' not in x, x))
        y = re.findall(r'.*div.*\n.*<p>(.*?)<.*\n.*\n.*\n.*input.*checked.*', r.text)
        x = list(zip(x, y))

        res = { 'state': re.findall(r'i class=.co4.>(.*?)</i', r.text)[0] }

        for i, j in x:
            res[i] = j

        return res

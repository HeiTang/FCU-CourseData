#!/usr/bin/python
# -*- coding: UTF-8 -*-
import requests
import json, os, sys
from bs4 import BeautifulSoup

SMS = [1, 2, 3, 4]    # 1:上學期 2:下學期 3:暑修上 4:暑修下
DEGREE = [1, 3, 4, 5] # 1:大學部 3:碩士班 4:博士班 5:進修班

class CourseDump:
    def __init__(self, year, sms):
        self.headers = {
            "Content-Type":"application/json; charset=UTF-8",
            "user-agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3573.0 Safari/537.36",
        }

        self.payload = {
            "baseOptions": {
                "lang": "cht",
                "year": year,
                "sms": sms
            }
        }

    def getDeptList(self):
        self.payload["degree"] = "1"
        url = 'https://coursesearch03.fcu.edu.tw/Service/Search.asmx/GetDeptList'
        r = requests.post(url, headers = self.headers, data = json.dumps(self.payload))
        r = self.stringProcess(r.text)
        return json.loads(r)

    def getCourseList(self, degree, dept_id):
        self.payload["typeOptions"] = {
            "degree": degree,
            "deptId": dept_id,
            "unitId": "*",
            "classId": "*"
        }

        url = "https://coursesearch04.fcu.edu.tw/Service/Search.asmx/GetType1Result"
        r = requests.post(url, headers = self.headers, data = json.dumps(self.payload))
        r = self.stringProcess(r.text)
        r = json.loads(r)                                                            # JSON -> dict
        r = json.dumps(r, ensure_ascii = False, indent = 4, separators=(',', ': '))  # dict -> JSON
        return r

    def saveFile(self, data, path, file_name):
        with open(os.path.join(path, file_name), 'w') as f:
            f.write(data)
            f.flush()
            f.close() 

    def stringProcess(self, string):
        string = string.replace('\\"', '"' )            # 將 \" 過濾成 "
        string = string.replace('\\\"', '"')            # 將 \\" 過濾成 "
        string = string.replace('"d":"{', '"d": {' )   
        string = string.replace('"d":"[{', '"d": [{' )
        string = string.replace(']}"}', ']}}')
        string = string.replace('}]"}', '}]}')
        return string

if __name__ == '__main__': 
    years = sys.argv[1].split(',')
    for year in years:
        # 確認資料夾是否存在，否則建立學年度資料夾
        path = '{}/{}'.format(os.getcwd(), str(year))
        if not os.path.exists(path):
            os.mkdir(path)
    
        for sms in SMS:
            course = CourseDump(year, sms)
            dept = course.getDeptList()['d']

            if dept != '[]':                     # 確認是否有開放查詢
                for degree in DEGREE:
                    for i in range(len(dept)):
                        dept_id = dept[i]['id']
                        data = course.getCourseList(degree, dept_id)
                        file_name = '{}{}-{}-{}.json'.format(str(year), str(sms), str(degree), dept_id)
                        course.saveFile(data, path, file_name)
                        print(f"+ {file_name}")
            else:
                print("- {}{}: No data".format(str(year), str(sms)))
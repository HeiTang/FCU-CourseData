#!/usr/bin/python
# -*- coding: UTF-8 -*-

import requests,os,sys
import json
from bs4 import BeautifulSoup

# 設定 Header 
headers = {
    "Accept": "*/*",
    "Accept-Language": 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6',
    "DNT": "1",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Content-Type":"application/json; charset=UTF-8",
    "user-agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3573.0 Safari/537.36",
    }


def PostGetType1Result(path,year,sms,degree,deptId):

    payload = {
        "baseOptions":{
            "lang":"cht",     #cht:中文 en:英文
            "year":year,
            "sms":sms         # 1:上學期 2:下學期 3:暑修上 4:暑修下
        },
        "typeOptions":{
            "degree":degree,     # 1:大學 3:碩士 4:博士 5:進修    
            "deptId":deptId,     # OD:跨領域設計學院(籌備 CC:創能學院 GE:通識中心 CA:工程與科學學院 CB:商學院 CH:人社學院 CI:資電學院 CD:建設學院 CF:金融學院 NM:國際科技與管理學院 AS:建築專業學院 PC:學分學程 XA:外語文 XC:通識核心課 XD:體育選項課 XE:綜合班 XF:統籌科目 XH:軍訓
            "unitId":"*",
            "classId":"*"
        }
    }

    payload = json.dumps(payload)
    url = "https://coursesearch04.fcu.edu.tw/Service/Search.asmx/GetType1Result"

    r = requests.post(url,headers=headers,data = payload)  
    r = r.text                                             

    r = r.replace('\\"','"' )            # 將 \" 過濾成 "
    r = r.replace('\\\"','"')            # 將 \\" 過濾成 "
    r = r.replace('"d":"{','"d": {' )    
    r = r.replace(']}"}',']}}')

    r = json.loads(r)                                                            # JSON -> dict
    r = json.dumps(r , ensure_ascii=False , indent=4 , separators=(',', ': '))   # dict -> JSON

    name = str(year) + str(sms) + "-" + str(degree) + "-" + deptId + ".json"
    print(name)

    with open(os.path.join(path,  name), 'w') as fo:
        # fo = open(name, "w")
        fo.write(str(r))
        fo.flush()
        fo.close() 

if __name__ == '__main__': 
    for year in range(110,111):  
        path = os.getcwd() + '/' +str(year)
        if not os.path.exists(path):
            os.mkdir(path)
        for sms in 1 , 2 , 3 , 4 :
            for degree in 1 , 3 , 4 , 5 :
                for deptId in "OD" , "CC" , "GE" , "CA" , "CB" , "CH" , "CI" , "CD" , "CF" , "NM" , "AS" , "PC" , "XA" , "XC" , "XD" , "XE" , "XF" , "XH":
                    PostGetType1Result(path,year,sms,degree,deptId)
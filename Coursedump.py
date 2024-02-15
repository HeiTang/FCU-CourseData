#!/usr/bin/python
# -*- coding: UTF-8 -*-
import json, os, sys
import logging
import argparse
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)24s - %(levelname)8s - %(message)s', 
                    filemode='w',
                    encoding='utf-8',
                    )

class CourseDump:
    # 學期選項
    SEMESTER_OPT = {
        "1": "上學期",
        "2": "下學期",
        "3": "暑修上",
        "4": "暑修下"
    }

    # 學制選項
    DEGREE_OPT = {
        "1": "大學部",
        "3": "碩士班",
        "4": "博士班",
        "5": "進修班"
    }

    def __init__(self):
        self.path = ''

    def argparse(self, now_year) -> argparse.Namespace:
        '''
        參數設定

        Args:
            now_year (int): 當前民國年
        '''
        parser = argparse.ArgumentParser(description='輸入學年度，取得課程資料。')
        parser.add_argument('-y', '--year', nargs='+',  type=int, help='學年度，輸入格式: 110 111 112', choices=range(100, now_year+1))
        # parser.add_argument('-s', '--semester', help='學期，輸入格式: 1,2,3,4')
        # parser.add_argument('-d', '--degree', help='學制，輸入格式: 1,3,4,5')
        args = parser.parse_args()
        return args

    def is_folder_exist(self, folder_name) -> str:
        '''
        確認資料夾是否存在，否則建立學年度資料夾。

        Args:
            folder_name (str): 資料夾名稱
        '''
        folder_path = os.path.join(os.getcwd(), folder_name)
        logging.debug(folder_path)

        if os.path.exists(folder_path):
            logging.info(f'學年度資料夾({folder_name}) 已存在。')
        else:
            os.mkdir(folder_path)
            logging.info(f'學年度資料夾({folder_name}) 建立成功。')
        return folder_path

    def _save_file(self, task_id, file_name, data) -> None:
        '''
        存檔

        Args:
            task_id (str): 任務編號
            file_name (str): 檔案名稱
            data (str): 資料
        '''
        data = json.dumps(data, ensure_ascii=False, indent=4)

        try:
            with open(os.path.join(self.path, file_name), 'w') as f:
                f.write(data)
                f.flush()
                f.close() 
            logging.info(f'[{task_id}] {file_name} 存檔成功！')
        except:
            logging.error(f'[{task_id}] {file_name} 存檔失敗！')

    def _get_res_json(self, url, payload) -> json:
        '''
        取得學院列表／學院代碼

        Args:
            url (str): 網址
            payload (json): 查詢條件
        '''
        headers = {
            "Content-Type":"application/json; charset=UTF-8",
            "user-agent": UserAgent().random
        }

        try:
            res = requests.post(url, headers=headers, data=json.dumps(payload))
            res.raise_for_status() # 檢查: 回應狀態碼是否為 200

            if res.text.find('處理此要求時發生錯誤') != -1: # 檢查回應內容是否為錯誤訊息
                logging.error(f'查詢失敗，請檢查輸入資料。')
                return None

            return res.json()

        except requests.exceptions.RequestException as e:
            logging.error(f'連線失敗，請檢查網路連線。')
            logging.debug(e)
            sys.exit(1)

    def get_course_data(self, year, semester, degree):
        '''
        取得課程資料

        Args:
            year (int): 學年度
            semester (str): 學期
            degree (str): 學制
        '''
        task_id = f'{year}{semester}-{degree}'
        task_name = f'{year} 學年度第 {semester} 學期 {self.DEGREE_OPT[degree]}'
        logging.info(f'[{task_id}] {task_name} 查詢開始。')

        payload_base = {
            "baseOptions": {
                "lang": "cht",
                "year": year,
                "sms": semester
            }
        } 

        # Step.1 學院列表
        payload_dept = payload_base
        payload_dept["degree"] = degree

        url = 'https://coursesearch01.fcu.edu.tw/Service/Search.asmx/GetDeptList'
        dept_list = self._get_res_json(url, payload_dept)
        dept_list_count = len(dept_list)

        if dept_list == None: # 確認是否有開放查詢
            logging.error(f'[{task_id}] 學院列表查詢失敗。')
            return None

        elif dept_list_count == 0: # 確認是否有學院列表
            logging.warning(f'[{task_id}] 查無學院列表。')
            return None

        else:
            logging.info(f'[{task_id}] 學院列表查詢成功({dept_list_count})。')
            logging.debug(dept_list)

        # Step.2 課程資料
        for dept in dept_list:
            dept_id = dept['id']

            payload_course = payload_base
            payload_course["typeOptions"] = {
                "degree": degree,
                "deptId": dept_id,
                "unitId": "*",
                "classId": "*"
            }

            url = "https://coursesearch01.fcu.edu.tw/Service/Search.asmx/GetType1Result"
            course_data = self._get_res_json(url, payload_course)
            course_data_count = course_data["total"]

            if course_data == None:         # 確認是否有開放查詢
                logging.error(f'[{task_id}] {dept["name"]}({dept_id}) 課程資料查詢失敗。')
                return None

            elif course_data_count == 0:    # 確認是否有課程資料
                logging.warning(f'[{task_id}] {dept["name"]}({dept_id}) 查無課程資料。')
                return None

            else:
                logging.info(f'[{task_id}] {dept["name"]}({dept_id}) 課程資料查詢成功({course_data_count})。')
                logging.debug(course_data)

            # Step.3 存檔
            file_name = f'{year}{semester}-{degree}-{dept_id}.json'
            self._save_file(task_id, file_name, course_data)

if __name__ == '__main__':
    course = CourseDump()
    now_year = int(os.popen('date +%Y').read()) - 1911 # 取得當前民國年
    args = course.argparse(now_year) # 參數設定

    # 取得學年度選項
    if args.year:
        year_list = args.year
    else:
        year_list = [now_year - 1, now_year] # 預設取得前一年度及當年度

    for year in year_list:
        # 檢查資料夾是否存在，否則建立學年度資料夾
        course.path = course.is_folder_exist(str(year))

        # 學期選項
        semster_list = list(course.SEMESTER_OPT.keys())
        degree_list = list(course.DEGREE_OPT.keys())

        # 取得課程資料
        for semester in semster_list:
            for degree in degree_list:
                course.get_course_data(year, semester, degree)

    logging.info('查詢結束。')

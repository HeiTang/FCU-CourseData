[![Python CI](https://github.com/HeiTang/FCU-CourseData/actions/workflows/python-app.yml/badge.svg)](https://github.com/HeiTang/FCU-CourseData/actions/workflows/python-app.yml)

     _________                                   ________          __          
     \_   ___ \  ____  __ _________  ______ ____ \______ \ _____ _/  |______   
     /    \  \/ /  _ \|  |  \_  __ \/  ___// __ \ |    |  \\__  \\   __\__  \  
     \     \___(  <_> )  |  /|  | \/\___ \\  ___/ |    `   \/ __ \|  |  / __ \_
      \______  /\____/|____/ |__|  /____  >\___  >_______  (____  /__| (____  /
             \/                         \/     \/        \/     \/          \/ 

逢甲大學從 101 學年度起各年度開設的所有課程資訊，提供給有需要直接取得資料的人使用。

- 友善連結
   - [FCU-CourseData](https://github.com/HeiTang/FCU-CourseData)：逢甲大學所有課程資訊。
   - [FCU-ClassID](https://github.com/HeiTang/FCU-ClassID)：逢甲大學的所有學院 ID 、 系所 ID 和班級 ID。

## 命名規則
```
[學年度][學期]-[學歷]-[院所/其他]
```
- 學期
  - 1：上學期 
  - 2：下學期 
  - 3：暑修上 
  - 4：暑修下
  
- 學制
  - 1：大學 
  - 3：碩士 
  - 4：博士 
  - 5：進修    
  
- 院所/其他
  - OD：跨領域設計學院(籌備 
  - CC：創能學院 
  - GE：通識中心 
  - CA：工程與科學學院 
  - CB：商學院 
  - CH：人社學院 
  - CI：資電學院 
  - CD：建設學院 
  - CF：金融學院 
  - NM：國際科技與管理學院 
  - AS：建築專業學院 
  - PC：學分學程 
  - XA：外語文 
  - XC：通識核心課 
  - XD：體育選項課 
  - XE：綜合班 
  - XF：統籌科目 
  - XH：軍訓

## 使用方法
1. 安裝 Python 套件

    ```
    pip3 install -r requirements.txt 
    ```

2. 執行程式

    ```
    python3 Coursedump.py
    ```

    > 若需要特定學年度的課程資訊，可以使用 `-y` 或 `--year` 參數指定學年度。
    > 預設為去年與當前學年度。

    | 參數 | 說明 | 範例 |
    | --- | --- | --- |
    | -h, --help | 顯示幫助訊息 | |
    | -y, --year | 學年度 | `python3 Coursedump.py -y 110` |





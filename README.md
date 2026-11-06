[![Python CI](https://github.com/HeiTang/FCU-CourseData/actions/workflows/python-app.yml/badge.svg)](https://github.com/HeiTang/FCU-CourseData/actions/workflows/python-app.yml)

     _________                                   ________          __          
     \_   ___ \  ____  __ _________  ______ ____ \______ \ _____ _/  |______   
     /    \  \/ /  _ \|  |  \_  __ \/  ___// __ \ |    |  \\__  \\   __\__  \  
     \     \___(  <_> )  |  /|  | \/\___ \\  ___/ |    `   \/ __ \|  |  / __ \_
      \______  /\____/|____/ |__|  /____  >\___  >_______  (____  /__| (____  /
             \/                         \/     \/        \/     \/          \/ 

逢甲大學從 100 學年度起各年度開設的所有課程資訊，提供給有需要直接取得資料的人使用。

- 課程查詢網站：[逢甲選課手帳](site/)（Astro 靜態站，滑過課程即可預覽它貼進課表哪一格）
- 架構說明：[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)　資料格式：[docs/SCHEMA.md](docs/SCHEMA.md)
- 友善連結
   - [FCU-CourseData](https://github.com/HeiTang/FCU-CourseData)：逢甲大學所有課程資訊。
   - [FCU-ClassID](https://github.com/HeiTang/FCU-ClassID)：逢甲大學的所有學院 ID 、 系所 ID 和班級 ID。

## 命名規則

原始檔（`100/` … `115/`）的檔名格式：

```
[學年度][學期]-[學制]-[院所/其他].json
```

- **學期**：`1` 上學期、`2` 下學期
  （`3` 暑修上、`4` 暑修下官方 API 不開放查詢，本資料集沒有）
- **學制**：`1` 大學部、`3` 碩士班、`4` 博士班、`5` 進修班
- **院所/其他**：

  | 代碼 | 名稱 | 代碼 | 名稱 |
  | --- | --- | --- | --- |
  | CA | 工程與科學學院 | CB | 商學院 |
  | CD | 建設學院 | CF | 金融學院 |
  | CH | 人社學院 | CI | 資電學院 |
  | AS | 建築專業學院 | NM | 國際科技與管理學院 |
  | MB | 商學專業學院 | SX | 社會創新學院 |
  | CC | 創能學院 | OD | 跨領域設計學院 |
  | SG | 永續發展與社會責任處 | GE | 通識中心 |
  | PC | 學分學程 | XA | 外語文 |
  | XC | 通識核心課 | XD | 體育選項課 |
  | XE | 綜合班 | XF | 統籌科目 |
  | XH | 軍訓 | XK | 其他 |
  | CE | 電機資訊學院（已改組） | CS | 理學院（已改組） |

  同一門課可能同時掛在多個學院底下（約 1%），所以同一個選課代號會出現在多個原始檔中。
  `data/` 已經把它合併成單一課程並記錄成 `depts` 陣列。

## 資料格式

| 路徑 | 內容 |
| --- | --- |
| `100/` … `115/` | 原始 API 回應，一個「學年度-學期-學制-學院」一個檔 |
| `data/{學年度}{學期}.json` | 正規化後的課程資料，一學期一檔，已去除重複、上課時間已剖析 |
| `data/index.json` | 學期清單與學院／學制／節次時間對照 |

多數情況你要的是 `data/`：原始資料裡同一門課會因為開給多個班級而重複好幾列（145,632 列
實際上只有 120,643 門課），而且上課時間是 `(二)06-07 資電B06 (五)09 資電107 劉維正`
這種需要自己剖析的字串。詳細設計見 [docs/SCHEMA.md](docs/SCHEMA.md)。

```
# 取得 113 學年度上學期所有課程
curl -s https://raw.githubusercontent.com/HeiTang/FCU-CourseData/master/data/1131.json
```

## 使用方法

1. 安裝相依套件

    ```
    python3 -m venv .venv
    source .venv/bin/activate
    python3 -m pip install -r requirements.txt
    ```

2. 抓取課程資料（會自動重建 `data/`）

    ```
    python3 scripts/fetch.py
    ```

    | 參數 | 說明 | 範例 |
    | --- | --- | --- |
    | `-h`, `--help` | 顯示說明 | |
    | `-y`, `--year` | 指定學年度，預設為上一學年度與當學年度 | `python3 scripts/fetch.py -y 110 111` |
    | `--no-build` | 只抓原始資料，不重建 `data/` | |

3. 只從既有原始資料重建 `data/`

    ```
    python3 scripts/build.py           # 重建
    python3 scripts/build.py --demo    # 剖析器自我檢查
    ```

> 暑修（學期 3、4）官方 API 不開放查詢，學院清單一律回空陣列，因此本資料集沒有暑修課程。

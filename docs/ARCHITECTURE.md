# 架構

## 資料流

```mermaid
flowchart TB
    api(["逢甲課程查詢 API<br/>coursesearch01.fcu.edu.tw"])

    subgraph fetch["scripts/fetch.py"]
        direction TB
        F1["對每組 學年度 × 學期 × 學制<br/>呼叫 GetDeptList 取學院清單"]
        F2["8 執行緒並行呼叫 GetType1Result<br/>單一學院失敗只跳過該學院"]
        F3["原子寫檔　tmp → rename"]
        F1 --> F2 --> F3
    end

    R["<b>100/ … 115/</b>　原始存檔<br/>1084 個檔　109 MB<br/>檔名 = 一次 API 查詢<br/><i>write-only，只有 build.py 讀</i>"]

    subgraph build["scripts/build.py"]
        direction TB
        B1["以 (學年度, 學期, 選課代號) 去重<br/>145,632 列 → 120,643 門"]
        B2["剖析 scr_period → sessions[]<br/>覆蓋率 99.98%"]
        B3["合併 classes / depts / degrees"]
        B4["省略所有 falsy 欄位"]
        B1 --> B2 --> B3 --> B4
    end

    D1["<b>data/{學年度}{學期}.json</b><br/>一行一門課"]
    D2["<b>data/index.json</b><br/>學期 / 學院 / 節次時間"]

    subgraph site["site/　Astro 靜態站"]
        direction TB
        S1["建置期：讀 index.json 產生下拉選單"]
        S2["瀏覽期：fetch 單一學期　135 KB gzip"]
        S3["純前端過濾與重繪"]
        S1 --> S2 --> S3
    end

    consumer(["其他使用者<br/>curl raw.githubusercontent.com"])

    api <--> F1
    api <--> F2
    F3 --> R --> B1
    B4 --> D1 & D2
    D2 --> S1
    D1 --> S2
    D1 --> consumer

    style R fill:#fff4e6,stroke:#d9822b
    style D1 fill:#e6f4ff,stroke:#1d4ed8
    style D2 fill:#e6f4ff,stroke:#1d4ed8
```

關鍵設計：**raw 的結構壞掉沒關係，因為它被隔離在 `build.py` 後面。**
檔名 `1131-1-CI.json` 記的是「對 API 問了什麼」而不是「這是什麼」，
所以跨學院掛牌的課會被複製到多個檔（17.2% 的列是重複的）。
`build.py` 第一件事就是把檔名拆開丟掉、把 `total`/`message` 信封拆掉。

## 自動化

```mermaid
flowchart LR
    cron["每日 00:00 UTC<br/>schedule"] --> wf1
    manual["workflow_dispatch"] --> wf1

    subgraph wf1["python-app.yml"]
        direction TB
        W1["build.py --demo<br/>剖析器自我檢查"] --> W2["fetch.py<br/>抓上一與當學年度"]
        W2 --> W3["自動接著跑 build.py"]
        W3 --> W4{"有變動？"}
        W4 -->|否| W5["結束，不 commit"]
        W4 -->|是| W6["commit + push"]
    end

    W6 --> push["Update course data 成功完成<br/>workflow_run（master）"]
    push --> wf2

    human["一般 push to master"] --> gate

    gate{"site/** 或<br/>data/** 有動？"}
    gate -->|是| wf2
    gate -->|否| skip["不部署"]

    subgraph wf2["pages.yml"]
        direction TB
        P1["npm ci"] --> P2["npm run build<br/>先把 ../data 複製進 public/"]
        P2 --> P3["upload-pages-artifact"]
    end

    P3 --> pages["GitHub Pages"]
```

`build.py --demo` 跑在抓取之前，是刻意的：剖析器的自我檢查若壞了，
就不該用它去覆蓋既有的 `data/`。

## 為什麼前端不需要搜尋函式庫

```mermaid
flowchart LR
    L["載入<br/>fetch 1 個學期"] --> H["預先算好 hay 字串<br/>課名+教師+課號+教室+班級+備註"]
    H --> W["等待輸入"]
    W -->|"每次按鍵"| M["courses.filter(match)<br/>3,602 筆"]
    M --> SORT["依課名符合度排序"]
    SORT --> RENDER["渲染前 50 筆"]
    RENDER --> URL["history.replaceState<br/>查詢條件寫進網址"]
    URL --> W
```

搜尋與重繪都在瀏覽器執行。單一學期約 3,600 筆物件，
`String.includes` 就夠了；Fuse.js / MiniSearch 這種等級的工具在這裡是純負擔。

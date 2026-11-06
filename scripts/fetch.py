#!/usr/bin/env python3
"""從逢甲課程查詢 API 抓取各學年度課程資料，存成 {學年度}/{學年度}{學期}-{學制}-{學院}.json。

用法:
    python3 scripts/fetch.py              # 抓上一學年度與當學年度
    python3 scripts/fetch.py -y 110 111   # 抓指定學年度
    python3 scripts/fetch.py --no-build   # 只抓 raw，不重建 data/
"""

import argparse
import json
import logging
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API = "https://coursesearch01.fcu.edu.tw/Service/Search.asmx"
ROOT = Path(__file__).resolve().parent.parent

# 官方 API 只開放上、下學期查詢，暑修（3、4）的學院清單一律回空陣列
SEMESTERS = ["1", "2"]
DEGREES = {"1": "大學部", "3": "碩士班", "4": "博士班", "5": "進修班"}

WORKERS = 8
TIMEOUT = 30

log = logging.getLogger("fetch")


def make_session():
    s = requests.Session()
    retry = Retry(
        total=4,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["POST"]),
    )
    s.mount("https://", HTTPAdapter(max_retries=retry, pool_maxsize=WORKERS))
    s.headers.update(
        {
            "Content-Type": "application/json; charset=UTF-8",
            # 學校主機會擋掉沒有 UA 的請求，固定一個就夠，不需要 fake-useragent
            "User-Agent": "FCU-CourseData/2.0 (+https://github.com/HeiTang/FCU-CourseData)",
        }
    )
    return s


def post(session, method, payload):
    """呼叫 API，失敗回 None（讓呼叫端決定要不要繼續）。"""
    try:
        res = session.post(f"{API}/{method}", data=json.dumps(payload), timeout=TIMEOUT)
        res.raise_for_status()
    except requests.RequestException as e:
        log.error("%s 連線失敗: %s", method, e)
        return None

    if "處理此要求時發生錯誤" in res.text:  # ASP.NET 把錯誤包成 200 回來
        log.error("%s 回應錯誤頁，請檢查查詢條件", method)
        return None
    try:
        return res.json()
    except ValueError:
        log.error("%s 回應不是 JSON", method)
        return None


def save(path, data):
    """原子寫檔：先寫暫存再 rename，中途中斷不會留下半個檔案。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")
    tmp.replace(path)


def fetch_dept(session, year, sem, degree, dept):
    """抓單一學院的課程並存檔，回傳課程數（失敗回 None）。"""
    tag = f"{year}{sem}-{degree}-{dept['id']}"
    data = post(
        session,
        "GetType1Result",
        {
            "baseOptions": {"lang": "cht", "year": year, "sms": sem},
            "typeOptions": {
                "degree": degree,
                "deptId": dept["id"],
                "unitId": "*",
                "classId": "*",
            },
        },
    )
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        log.error("[%s] %s 查詢失敗", tag, dept["name"])
        return None

    total = data.get("total")
    if not isinstance(total, int) or total != len(data["items"]):
        log.error("[%s] 課程數與 items 不符", tag)
        return None
    if total == 0:  # 該學院這學期沒開課，是正常狀況
        log.info("[%s] %s 查無課程", tag, dept["name"])
        return 0

    save(ROOT / str(year) / f"{tag}.json", data)
    log.info("[%s] %s %d 門", tag, dept["name"], total)
    return total


def fetch_year(session, year):
    total = 0
    for sem in SEMESTERS:
        for degree in DEGREES:
            depts = post(
                session,
                "GetDeptList",
                {
                    "baseOptions": {"lang": "cht", "year": year, "sms": sem},
                    "degree": degree,
                },
            )
            if (
                depts is None
                or not isinstance(depts, list)
                or any(
                    not isinstance(d, dict) or not d.get("id") or not d.get("name")
                    for d in depts
                )
            ):
                raise RuntimeError(f"{year}{sem}-{degree} 學院清單查詢失敗")
            if not depts:
                log.info("[%s%s-%s] 無學院清單，略過", year, sem, degree)
                continue

            # 各學院互不相干，一個失敗不該中斷其他學院
            with ThreadPoolExecutor(max_workers=WORKERS) as pool:
                counts = list(
                    pool.map(lambda d: fetch_dept(session, year, sem, degree, d), depts)
                )
            if None in counts:
                raise RuntimeError(f"{year}{sem}-{degree} 部分學院查詢失敗")
            total += sum(c for c in counts if c)
    return total


def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s"
    )

    this_year = date.today().year - 1911
    parser = argparse.ArgumentParser(description="抓取逢甲大學課程資料")
    parser.add_argument(
        "-y",
        "--year",
        nargs="+",
        type=int,
        choices=range(100, this_year + 1),
        metavar="YEAR",
        help="學年度，如 110 111；預設為上一學年度與當學年度",
    )
    parser.add_argument("--no-build", action="store_true", help="不要重建 data/")
    args = parser.parse_args()

    years = args.year or [this_year - 1, this_year]
    session = make_session()

    grand_total = 0
    for year in years:
        log.info("=== %s 學年度 ===", year)
        try:
            grand_total += fetch_year(session, year)
        except RuntimeError as exc:
            log.error("%s；不重建 data/", exc)
            return 1

    if grand_total == 0:
        log.error("完全沒抓到資料，視為失敗")
        return 1

    log.info("抓取完成，共 %d 筆", grand_total)

    if not args.no_build:
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build.py")], check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

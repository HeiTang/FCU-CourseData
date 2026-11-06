#!/usr/bin/env python3
"""把 raw 課程 JSON 正規化成一學期一檔的 data/*.json。

raw 一列 = 一個「開課班級」，同一門課會因為開給多個班級而重複。
真正的主鍵是 (學年度, 學期, 選課代號)，因此以它為單位合併，
把 cls_id/cls_name 收成 classes[]。
"""

import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data"

DAY = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "日": 7}

# (週)起節[-迄節] 教室 ；教室可能含括號，所以吃到下一個 (週)節 為止
SESSION_RE = re.compile(
    r"\(([一二三四五六日])\)(\d{2})(?:-(\d{2}))?[ ]*(.*?)(?=\([一二三四五六日]\)\d{2}|$)"
)

# 教室是「還沒排定」而非真的地點
UNASSIGNED_ROOMS = {"未排教室", "待排", "未排定", ""}

DEGREES = {1: "大學部", 3: "碩士班", 4: "博士班", 5: "進修班"}

# ponytail: 學院名稱先硬編（raw 檔沒存），改寫抓取程式時直接把 GetDeptList
# 的結果存成 data/depts.json 就能拿掉這份常數
DEPTS = {
    "OD": "跨領域設計學院", "CC": "創能學院", "GE": "通識中心",
    "CA": "工程與科學學院", "CB": "商學院", "CH": "人社學院",
    "CI": "資電學院", "CD": "建設學院", "CF": "金融學院",
    "NM": "國際科技與管理學院", "AS": "建築專業學院", "SG": "永續發展與社會責任處",
    "PC": "學分學程", "XA": "外語文", "XC": "通識核心課", "XD": "體育選項課",
    "XE": "綜合班", "XF": "統籌科目", "XH": "軍訓", "XK": "其他",
    "CE": "電機資訊學院", "CS": "理學院", "MB": "商學專業學院", "SX": "社會創新學院",
}

# 節次對應的上課時間。109 學年度起夜間部時間有調整，取自官方查詢系統。
PERIOD_TIMES = {
    ">=109": ["08:10", "09:10", "10:10", "11:10", "12:10", "13:10", "14:10",
              "15:10", "16:10", "17:10", "18:30", "19:25", "20:25", "21:20"],
    "<109": ["08:10", "09:10", "10:10", "11:10", "12:10", "13:10", "14:10",
             "15:10", "16:10", "17:10", "18:10", "19:10", "20:10", "21:10"],
}


def parse_sessions(period, teacher):
    """把 scr_period 拆成 [{day, from, to, room}]。無法完整解析時回 None。"""
    text = (period or "").strip()
    if teacher and text.endswith(teacher):
        text = text[: -len(teacher)].strip()

    sessions, pos = [], 0
    for m in SESSION_RE.finditer(text):
        if m.start() != pos:  # 中間有解析不掉的殘骸
            return None
        pos = m.end()
        start = int(m.group(2))
        room = m.group(4).strip()
        sessions.append(
            {
                "day": DAY[m.group(1)],
                "from": start,
                "to": int(m.group(3)) if m.group(3) else start,
                "room": None if room in UNASSIGNED_ROOMS else room,
            }
        )
    if pos != len(text):
        return None
    return sessions


def split_teachers(raw):
    return [t for t in re.split(r"[,，、]", (raw or "").strip()) if t]


def num(v):
    """1.0 -> 1，省掉每筆兩個 byte；非數字原樣回傳。"""
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def normalize(row, degree, dept):
    sessions = parse_sessions(row.get("scr_period"), row.get("scr_teacher"))
    exams = [
        row.get("scr_examid") == "是",
        row.get("scr_examfn") == "是",
        row.get("scr_exambf") == "是",
    ]
    course = {
        "id": row["scr_selcode"],
        "code": row.get("sub_id3"),
        "name": (row.get("sub_name") or "").strip(),
        "credit": num(row.get("scr_credit")),
        "required": row.get("scj_scr_mso") == "必修",
        # 約 1% 的課跨學院／跨學制掛牌，所以這兩個是關係不是屬性
        "degrees": [int(degree)],
        "depts": [dept],
        "unit": row.get("unt_ls"),
        "teachers": split_teachers(row.get("scr_teacher")),
        "classes": [],
        "sessions": sessions if sessions is not None else [],
        "quota": num(row.get("scr_precnt")),
        "enrolled": num(row.get("scr_acptcnt")),
        "online": row.get("scr_ldl") == "線上教學On-line",
        "english": row.get("scr_english") == "Y",
        # 期中／期末／期初考，全 false 佔絕大多數，輸出時整個省略
        "exams": exams if any(exams) else None,
        # 92% 是「全學期」，當預設值省略
        "period": None if row.get("scr_date") == "全學期" else row.get("scr_date"),
        "note": (row.get("scr_remarks") or "").strip() or None,
        "subject_id": row.get("sub_id"),
        # 88% 是 "001"，當預設值省略
        "section": None if row.get("scr_dup") == "001" else row.get("scr_dup"),
    }
    if sessions is None:  # 上游字串壞掉，留原文讓前端至少能顯示
        course["raw_period"] = row.get("scr_period")
    return course


def merge_row(course, row, degree, dept):
    cid = row.get("cls_id")
    if cid and not any(c["id"] == cid for c in course["classes"]):
        course["classes"].append({"id": cid, "name": row.get("cls_name")})
    if dept not in course["depts"]:
        course["depts"].append(dept)
    if int(degree) not in course["degrees"]:
        course["degrees"].append(int(degree))


def drop_empty(course):
    """省掉 null / 空集合 / false / 0 — 消費端一律當預設值處理。"""
    return {k: v for k, v in course.items() if v}


def dump_courses(courses):
    """一行一門課。

    gzip 後跟完全 minify 一模一樣（實測 135 KB），未壓縮只多 0.8%，
    但換來 git diff 能精確到「哪幾門課變了」而不是「整個檔案變了」，
    也讓 grep 派得上用場。indent=2 未壓縮要多 69%，不划算。
    """
    rows = ",\n".join(
        json.dumps(c, ensure_ascii=False, separators=(",", ":")) for c in courses
    )
    return f"[\n{rows}\n]\n"


def build():
    OUT.mkdir(exist_ok=True)
    semesters = {}  # (year, sem) -> OrderedDict[selcode] = course
    depts = {}  # dept id -> 名稱（raw 裡沒有，先留 id）

    raw_files = sorted(p for p in ROOT.glob("1[0-9][0-9]/*.json"))
    if not raw_files:
        sys.exit("找不到 raw 課程檔")

    for path in raw_files:
        year_sem, degree, dept = path.stem.split("-")
        year, sem = int(year_sem[:3]), int(year_sem[3])
        bucket = semesters.setdefault((year, sem), OrderedDict())
        depts.setdefault(dept, dept)

        for row in json.loads(path.read_text(encoding="utf-8"))["items"]:
            key = row["scr_selcode"]
            if key not in bucket:
                bucket[key] = normalize(row, degree, dept)
            merge_row(bucket[key], row, degree, dept)

    index = []
    for (year, sem), bucket in sorted(semesters.items()):
        courses = [drop_empty(c) for c in bucket.values()]
        name = f"{year}{sem}.json"
        (OUT / name).write_text(dump_courses(courses), encoding="utf-8")
        index.append(
            {
                "year": year,
                "sem": sem,
                "file": name,
                "count": len(courses),
                "bytes": (OUT / name).stat().st_size,
            }
        )

    seen_depts = sorted(d for d in depts if d in DEPTS) + sorted(
        d for d in depts if d not in DEPTS
    )
    (OUT / "index.json").write_text(
        json.dumps(
            {
                "semesters": index,
                "degrees": DEGREES,
                "depts": {d: DEPTS.get(d, d) for d in seen_depts},
                "periodTimes": PERIOD_TIMES,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return index


def demo():
    """自我檢查：解析器的邊界情況。"""
    assert parse_sessions("(二)06-07 資電B06 (五)09     資電107 劉維正", "劉維正") == [
        {"day": 2, "from": 6, "to": 7, "room": "資電B06"},
        {"day": 5, "from": 9, "to": 9, "room": "資電107"},
    ]
    # 教室含括號
    assert parse_sessions("(二)08-09 體館301(主球場) 王亭文", "王亭文") == [
        {"day": 2, "from": 8, "to": 9, "room": "體館301(主球場)"}
    ]
    # 未排教室 -> room=None
    assert parse_sessions("(三)00     待排 何晉瑋", "何晉瑋") == [
        {"day": 3, "from": 0, "to": 0, "room": None}
    ]
    # 沒有教室
    assert parse_sessions("(五)02-04 陳某", "陳某") == [
        {"day": 5, "from": 2, "to": 4, "room": None}
    ]
    # 壞資料 -> None
    assert parse_sessions("00     未排教室", "") is None
    assert split_teachers("張永吉,古陳蜀東") == ["張永吉", "古陳蜀東"]
    assert num(3.0) == 3 and num(0.5) == 0.5
    # 跨學院掛牌：dept/degree 要累加而不是覆蓋
    c = normalize({"scr_selcode": "1", "scr_credit": 3.0}, "1", "CB")
    merge_row(c, {"cls_id": "X"}, "3", "CF")
    assert c["depts"] == ["CB", "CF"] and c["degrees"] == [1, 3]
    # 全 false 的考試旗標與 001 分班要被丟掉
    assert "exams" not in drop_empty(c) and "section" not in drop_empty(c)
    print("demo ok")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        for row in build():
            print(f"{row['year']}-{row['sem']}  {row['count']:6d} 門  {row['bytes']:>9,} bytes")

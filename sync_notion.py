"""
sync_notion.py
Notion Database -> data.json 변환기

노션 DB 컬럼 구조 (예시):
    Name     : 키워드 이름 (title)
    Type     : weak / strong (select)
    Unit     : 소인수분해 / 정수와유리수 (select)
    Mistakes : 오답 횟수 (number)
    Correct  : 정답 횟수 (number)
    Weight   : 구체 크기 1~5 (number)
    Color    : hex 색상 (rich_text)
    Link     : weakness / problems (select)
    Tip      : 학습 팁 (rich_text)
"""
import os, json, requests
from datetime import datetime, timezone, timedelta

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DB_ID = os.environ["NOTION_DB_ID"]

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

NOTION_LINKS = {
    "mainPage": "https://www.notion.so/YOUR_MAIN_PAGE_ID",
    "problems": "https://www.notion.so/YOUR_PROBLEMS_PAGE_ID",
    "weakness": "https://www.notion.so/YOUR_WEAKNESS_PAGE_ID",
    "dataMining": "https://www.notion.so/YOUR_DATAMINING_PAGE_ID",
}

DEFAULT_COLORS = {
    "weak": "#ff2d55",
    "strong": "#2ed573",
}

def get_prop(props, key, kind):
    p = props.get(key, {})
    if kind == "title":
        return "".join(t["plain_text"] for t in p.get("title", []))
    if kind == "select":
        return (p.get("select") or {}).get("name", "")
    if kind == "number":
        return p.get("number") or 0
    if kind == "rich_text":
        return "".join(t["plain_text"] for t in p.get("rich_text", []))
    return ""

def fetch_all_rows():
    rows, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        res = requests.post(
            f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query",
            headers=HEADERS,
            json=body
        )
        res.raise_for_status()
        data = res.json()
        rows.extend(data["results"])
        if not data.get("has_more"):
            break
        cursor = data["next_cursor"]
    return rows

def build_json(rows):
    keywords = []
    total_correct = 0
    total_questions = 0
    for row in rows:
        p = row["properties"]
        name = get_prop(p, "Name", "title")
        ktype = get_prop(p, "Type", "select").lower()
        unit = get_prop(p, "Unit", "select")
        mistakes = int(get_prop(p, "Mistakes", "number"))
        correct = int(get_prop(p, "Correct", "number"))
        weight = int(get_prop(p, "Weight", "number")) or 3
        color = get_prop(p, "Color", "rich_text") or DEFAULT_COLORS.get(ktype, "#aaa")
        link = get_prop(p, "Link", "select") or "problems"
        tip = get_prop(p, "Tip", "rich_text")
        if not name:
            continue
        entry = {
            "t": name,
            "type": ktype,
            "w": weight,
            "c": color,
            "link": link,
            "unit": unit,
            "tip": tip,
        }
        if ktype == "weak":
            entry["mistakes"] = mistakes
            total_questions += mistakes
        else:
            entry["correct"] = correct
            total_correct += correct
        total_questions += correct
        keywords.append(entry)
    kst = timezone(timedelta(hours=9))
    score = round((total_correct / total_questions * 100) if total_questions else 0)
    return {
        "meta": {
            "title": "수학 키워드",
            "score": score,
            "total": total_questions,
            "correct": total_correct,
            "updatedAt": datetime.now(kst).isoformat(),
        },
        "notionLinks": NOTION_LINKS,
        "keywords": keywords,
    }

if __name__ == "__main__":
    print("📡 Notion DB 쿼리 중...")
    rows = fetch_all_rows()
    print(f"  {len(rows)}개 행 수신")
    result = build_json(rows)
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ data.json 저장 완료 (키워드 {len(result['keywords'])}개, 점수 {result['meta']['score']}점)")

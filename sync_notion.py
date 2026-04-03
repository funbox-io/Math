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
    actual_key = key
    for k in props:
        if k.lower() == key.lower():
            actual_key = k
            break
    p = props.get(actual_key, {})
    if kind == "title":
        return "".join(t["plain_text"] for t in p.get("title", []))
    if kind == "select":
        return (p.get("select") or {}).get("name", "")
    if kind == "number":
        return p.get("number") or 0
    if kind == "rich_text":
        return "".join(t["plain_text"] for t in p.get("rich_text", []))
    if kind == "multi_select":
                        items = p.get("multi_select", [])
                return ", ".join(i["name"] for i in items) if items else ""
    if kind == "status":
                return (p.get("status") or {}).get("name", "")
    return ""


def fetch_all_rows():
    rows, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        res = requests.post(
            f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query",
            headers=HEADERS, json=body
        )
        res.raise_for_status()
        data = res.json()
        rows.extend(data["results"])
        if not data.get("has_more"):
            break
        cursor = data["next_cursor"]
    return rows


def get_db_schema():
    res = requests.get(
        f"https://api.notion.com/v1/databases/{NOTION_DB_ID}",
        headers=HEADERS
    )
    res.raise_for_status()
    data = res.json()
    props = data.get("properties", {})
    print("=== DB column list ===")
    for name, info in props.items():
        print(f"  '{name}' : {info.get('type', '?')}")
    return props


def build_json(rows):
    keywords = []
    total_correct = 0
    total_questions = 0

    for row in rows:
        p = row["properties"]
        if not keywords:
            print("=== First row columns ===")
            for k, v in p.items():
                print(f"  '{k}' : {v.get('type', '?')}")

        name = get_prop(p, "문제집", "title")
                score_val = int(get_prop(p, "점수", "number"))
                level = get_prop(p, "수준", "rich_text")
                keyword_text = get_prop(p, "키워드", "rich_text")
                importance = get_prop(p, "중요도", "multi_select")
                ktype = "weak" if score_val < 60 else "strong"
                unit = importance if importance else "기타"
                mistakes = max(1, (100 - score_val) // 20) if ktype == "weak" else 0
                correct = score_val // 20 if ktype == "strong" else 0
                weight = 5 if score_val < 40 else (3 if ktype == "weak" else 2)
                color = DEFAULT_COLORS.get(ktype, "#aaa")
                link = "weakness" if ktype == "weak" else "problems"
                tip = keyword_text if keyword_text else f"점수: {score_val}"

        if not name:
            continue

        entry = {
            "t": name, "type": ktype, "w": weight,
            "c": color, "link": link,
            "unit": unit, "tip": tip,
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
            "title": "수학 키워드 데이터 마이닝",
            "score": score,
            "total": total_questions,
            "correct": total_correct,
            "updatedAt": datetime.now(kst).isoformat(),
        },
        "notionLinks": NOTION_LINKS,
        "keywords": keywords,
    }


if __name__ == "__main__":
    print("Checking Notion DB schema...")
    get_db_schema()
    print("Querying Notion DB...")
    rows = fetch_all_rows()
    print(f"  Received {len(rows)} rows")

    result = build_json(rows)

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"data.json saved: {len(result['keywords'])} keywords, score {result['meta']['score']}")

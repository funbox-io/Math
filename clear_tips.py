""" clear_tips.py
Notion DB Tip 컬럼 값 삭제 (비우기)
"""
import os, requests

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DB_ID = os.environ["NOTION_DB_ID"]

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

def query_db():
    rows, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        res = requests.post(
            f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query",
            headers=HEADERS,
            json=body,
        )
        res.raise_for_status()
        data = res.json()
        rows.extend(data["results"])
        if not data.get("has_more"):
            break
        cursor = data["next_cursor"]
    return rows

def clear_tip(page_id):
    body = {
        "properties": {
            "Tip": {
                "rich_text": []
            }
        }
    }
    res = requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=HEADERS,
        json=body,
    )
    res.raise_for_status()
    print(" -> Tip 초기화 완료")

if __name__ == "__main__":
    print("Notion DB Tip 값 삭제 중...")
    rows = query_db()
    count = 0
    for row in rows:
        props = row["properties"]
        name = "".join(t["plain_text"] for t in props.get("Name", {}).get("title", []))
        print(f" {name}")
        clear_tip(row["id"])
        count += 1
    print(f"총 {count}개 항목 Tip 초기화 완료!")

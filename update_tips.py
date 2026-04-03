""" update_tips.py
Notion DB Tip 컬럼 값 수정
"""
import os, requests

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DB_ID = os.environ["NOTION_DB_ID"]

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

# 수정할 Tip 값 (keyword: tip)
TIPS = {
    "통분": "분모를 같게 만드는게 핵심",
    "소인수분해": "1 보다 큰 자연수를 소수만 곱해서 나타내기",
    "소인과 합성수": "소수는 1 과 자기 자신만으로 나누어떨어지는 수",
    "정수 사칙연산": "부호와 절대값을 먼저 생각하기",
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

def update_tip(page_id, tip_text):
    body = {
        "properties": {
            "Tip": {
                "rich_text": [{"text": {"content": tip_text}}]
            }
        }
    }
    res = requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=HEADERS,
        json=body,
    )
    res.raise_for_status()
    print(f"  -> Tip 업데이트: {tip_text}")

if __name__ == "__main__":
    print("Notion DB Tip 수정 중...")
    rows = query_db()
    for row in rows:
        props = row["properties"]
        name = "".join(t["plain_text"] for t in props.get("Name", {}).get("title", []))
        if name in TIPS:
            print(f" {name}")
            update_tip(row["id"], TIPS[name])
    print("완료!")

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

BASE = "http://127.0.0.1:8000"

SAMPLE_CODE = (
    "import sqlite3\n"
    "password = 'admin123'\n"
    "def get_user(username):\n"
    "    conn = sqlite3.connect('users.db')\n"
    "    query = f\"SELECT * FROM users WHERE name = '{username}'\"\n"
    "    return conn.execute(query).fetchall()\n"
)


def main():
    # 1. Create session
    r = httpx.post(f"{BASE}/sessions")
    assert r.status_code == 200, f"Create session failed: {r.text}"
    session_id = r.json()["session_id"]
    print(f"1. Created session: {session_id[:12]}...")

    # 2. Submit code for review
    r = httpx.post(
        f"{BASE}/sessions/{session_id}/review",
        json={"code": SAMPLE_CODE},
        timeout=120,
    )
    assert r.status_code == 200, f"Review failed: {r.text}"
    review = r.json()
    print(f"2. Review: {review['summary']}")
    print(f"   Findings: {len(review['findings'])}")
    for f in review["findings"]:
        print(f"   [{f['severity']}] {f['title']}")

    # 3. Get findings filtered by severity
    r = httpx.get(f"{BASE}/sessions/{session_id}/findings?severity=critical")
    print(f"3. Critical findings: {len(r.json())}")

    # 4. Chat about findings
    r = httpx.post(
        f"{BASE}/sessions/{session_id}/chat",
        json={"message": "How do I fix the SQL injection?"},
        timeout=60,
    )
    assert r.status_code == 200, f"Chat failed: {r.text}"
    print(f"4. Chat reply: {r.json()['reply'][:120]}...")

    # 5. Get chat history
    r = httpx.get(f"{BASE}/sessions/{session_id}/chat/history")
    print(f"5. Chat history: {len(r.json())} messages")

    # 6. List sessions
    r = httpx.get(f"{BASE}/sessions")
    print(f"6. Total sessions: {len(r.json())}")

    # 7. Cleanup
    r = httpx.delete(f"{BASE}/sessions/{session_id}")
    print(f"7. Deleted session: {r.json()['detail']}")

    print("\nAll API tests passed!")


if __name__ == "__main__":
    main()

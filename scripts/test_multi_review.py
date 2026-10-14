import sys
import os
import zipfile
import tempfile
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

BASE = "http://127.0.0.1:8000"

# Two Python files with cross-file issues
FILE_A = '''
import sqlite3
from utils import get_connection

password = "secret123"

def get_user(username):
    conn = get_connection()
    query = f"SELECT * FROM users WHERE name = '{username}'"
    return conn.execute(query).fetchall()

def process_users():
    users = get_user("admin")
    result = ""
    for u in users:
        result += str(u) + "\\n"
    return result
'''

FILE_B = '''
import sqlite3

DB_PATH = "users.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def get_user_by_id(user_id):
    conn = get_connection()
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return conn.execute(query).fetchone()

def save_user(name, email):
    conn = get_connection()
    conn.execute(f"INSERT INTO users VALUES ('{name}', '{email}')")
    conn.commit()
    conn.close()
'''


def create_test_zip():
    tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    with zipfile.ZipFile(tmp.name, "w") as zf:
        zf.writestr("app.py", FILE_A)
        zf.writestr("utils.py", FILE_B)
    return tmp.name


def main():
    # 1. Create session
    r = httpx.post(f"{BASE}/sessions")
    assert r.status_code == 200
    session_id = r.json()["session_id"]
    print(f"1. Created session: {session_id[:12]}...")

    # 2. Upload zip for multi-level review
    zip_path = create_test_zip()
    print("2. Uploading zip for multi-level review...")
    with open(zip_path, "rb") as f:
        r = httpx.post(
            f"{BASE}/sessions/{session_id}/review/upload",
            files={"file": ("test.zip", f, "application/zip")},
            timeout=300,
        )
    os.unlink(zip_path)
    assert r.status_code == 200, f"Upload failed: {r.text}"
    result = r.json()

    print(f"\n=== RESULTS ===")
    print(f"Summary: {result['summary']}")
    print(f"Files reviewed: {result.get('files_reviewed', [])}")

    # Level 1 results
    for fname, freview in result.get("file_reviews", {}).items():
        print(f"\n--- Level 1: {fname} ---")
        print(f"  {freview['summary']}")
        for f in freview["findings"]:
            print(f"  [{f['severity']}] {f['title']}")

    # Level 2 results
    cross = result.get("cross_file_findings", [])
    print(f"\n--- Level 2: Cross-File Issues ({len(cross)}) ---")
    for f in cross:
        file_tag = f" [{f['file_name']}]" if f.get("file_name") else ""
        print(f"  [{f['severity']}]{file_tag} {f['title']}")
        print(f"    {f['description'][:120]}...")

    # 3. Test findings filter by file_name
    r = httpx.get(f"{BASE}/sessions/{session_id}/findings?file_name=app.py")
    if r.status_code == 200:
        print(f"\n3. Findings for app.py: {len(r.json())}")
    else:
        print(f"\n3. Findings filter: {r.status_code}")

    # 4. Cleanup
    httpx.delete(f"{BASE}/sessions/{session_id}")
    print("\n4. Session cleaned up")
    print("\nMulti-level review test complete!")


if __name__ == "__main__":
    main()

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

BASE = "http://127.0.0.1:8000"

# A small public Python file on GitHub
TEST_URL = "https://github.com/pallets/flask/blob/main/src/flask/json/__init__.py"


def main():
    # 1. Create session
    r = httpx.post(f"{BASE}/sessions")
    session_id = r.json()["session_id"]
    print(f"1. Created session: {session_id[:12]}...")

    # 2. Submit GitHub URL
    print(f"2. Reviewing: {TEST_URL}")
    r = httpx.post(
        f"{BASE}/sessions/{session_id}/review/github",
        json={"github_url": TEST_URL},
        timeout=180,
    )
    assert r.status_code == 200, f"Failed: {r.status_code} {r.text}"
    result = r.json()

    print(f"\n=== RESULTS ===")
    print(f"Summary: {result.get('summary')}")
    findings = result.get("findings", [])
    print(f"Findings: {len(findings)}")
    for f in findings[:5]:
        print(f"  [{f['severity']}] {f['title']}")

    # 3. Cleanup
    httpx.delete(f"{BASE}/sessions/{session_id}")
    print("\n3. Session cleaned up")
    print("GitHub URL review test passed!")


if __name__ == "__main__":
    main()

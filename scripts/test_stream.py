import sys
import os
import json
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
    # Create session
    r = httpx.post(f"{BASE}/sessions")
    session_id = r.json()["session_id"]
    print(f"Session: {session_id[:12]}...\n")

    # Stream review
    print("Streaming review events:")
    print("-" * 50)

    with httpx.stream(
        "POST",
        f"{BASE}/sessions/{session_id}/review/stream",
        json={"code": SAMPLE_CODE},
        timeout=120,
    ) as response:
        event_name = None
        for line in response.iter_lines():
            if not line:
                continue
            if line.startswith("event:"):
                event_name = line[len("event:"):].strip()
            elif line.startswith("data:") and event_name:
                data = json.loads(line[len("data:"):].strip())

                if event_name == "code_analysis":
                    print(f"  🔬 Code Analysis: {data.get('language')} — {data.get('total_lines')} lines")
                elif event_name == "review_complete":
                    print(f"  ✅ Review Complete: {data.get('summary')}")
                    print(f"     Total findings: {len(data.get('findings', []))}")
                else:
                    count = len(data.get("findings", []))
                    print(f"  📋 {event_name}: {count} findings")

                event_name = None

    print("-" * 50)

    # Cleanup
    httpx.delete(f"{BASE}/sessions/{session_id}")
    print("\nStreaming test passed!")


if __name__ == "__main__":
    main()

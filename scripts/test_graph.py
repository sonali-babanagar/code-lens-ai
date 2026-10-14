import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.graph.builder import build_review_graph

SAMPLE_CODE = """
import sqlite3

password = "admin123"

def get_user(username):
    conn = sqlite3.connect("users.db")
    query = f"SELECT * FROM users WHERE name = '{username}'"
    result = conn.execute(query)
    return result.fetchall()

class UserManager:
    def __init__(self):
        self.db = sqlite3.connect("users.db")

    def get_all_users(self):
        users = self.db.execute("SELECT * FROM users").fetchall()
        result = ""
        for user in users:
            orders = self.db.execute(f"SELECT * FROM orders WHERE user_id = {user[0]}").fetchall()
            result += str(user) + str(orders) + "\\n"
        return result
"""


async def main():
    print("Building review graph...")
    graph = build_review_graph()

    print("Running full pipeline (3 agents in parallel)...\n")
    result = await graph.ainvoke({
        "code": SAMPLE_CODE,
        "session_id": "test-graph-001",
    })

    analysis = result["code_analysis"]
    print(f"Code Analysis: {analysis['language']}, {analysis['total_lines']} lines, "
          f"{analysis['function_count']} functions, {analysis['class_count']} classes")

    review = result["final_review"]
    print(f"\n{review.summary}")
    print(f"Total findings: {len(review.findings)}\n")

    for f in review.findings:
        line = f"L{f.line_number}" if f.line_number else "  "
        print(f"  [{f.severity.value:8}] [{f.category.value:12}] {line:4} {f.title}")


if __name__ == "__main__":
    asyncio.run(main())

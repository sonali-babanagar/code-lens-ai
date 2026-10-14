import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag.retriever import KnowledgeRetriever
from src.agents.security_agent import SecurityAgent
from src.agents.architecture_agent import ArchitectureAgent
from src.agents.performance_agent import PerformanceAgent
from src.agents.code_analyzer import CodeAnalyzer
from src.agents.synthesizer import Synthesizer

SAMPLE_CODE = """
import sqlite3
import os

password = "admin123"
DB_URL = "postgresql://admin:secret@localhost/mydb"

def get_user(username):
    conn = sqlite3.connect("users.db")
    query = f"SELECT * FROM users WHERE name = '{username}'"
    result = conn.execute(query)
    return result.fetchall()

class UserManager:
    def __init__(self):
        self.db = sqlite3.connect("users.db")
        self.cache = {}

    def create_user(self, data):
        self.validate(data)
        self.db.execute(f"INSERT INTO users VALUES ('{data['name']}', '{data['email']}')")
        self.db.commit()
        self.send_email(data["email"])
        self.log_audit(data)
        self.generate_report()

    def validate(self, data):
        pass

    def send_email(self, email):
        pass

    def log_audit(self, data):
        pass

    def generate_report(self):
        pass

    def get_all_users(self):
        users = self.db.execute("SELECT * FROM users").fetchall()
        result = ""
        for user in users:
            orders = self.db.execute(f"SELECT * FROM orders WHERE user_id = {user[0]}").fetchall()
            result += str(user) + str(orders) + "\\n"
        return result
"""


async def main():
    retriever = KnowledgeRetriever()

    # Test CodeAnalyzer (no LLM)
    analyzer = CodeAnalyzer()
    analysis = analyzer.analyze(SAMPLE_CODE)
    print(f"--- Code Analysis ---")
    print(f"  Language: {analysis['language']}")
    print(f"  Lines: {analysis['total_lines']}")
    print(f"  Functions: {analysis['function_count']}")
    print(f"  Classes: {analysis['class_count']}")

    # Test each agent
    agents = [
        SecurityAgent(retriever),
        ArchitectureAgent(retriever),
        PerformanceAgent(retriever),
    ]

    outputs = []
    for agent in agents:
        print(f"\n--- {agent.agent_name} ---")
        output = await agent.analyze(SAMPLE_CODE, "python")
        outputs.append(output)
        print(f"  Found {len(output.findings)} findings")
        for f in output.findings:
            print(f"  [{f.severity.value}] {f.title}")

    # Test Synthesizer
    synthesizer = Synthesizer()
    review = synthesizer.synthesize("test-session", SAMPLE_CODE, "python", outputs)
    print(f"\n--- Synthesized Review ---")
    print(f"  {review.summary}")
    print(f"  Total findings: {len(review.findings)}")
    for f in review.findings:
        print(f"  [{f.severity.value}] [{f.category.value}] {f.title} (by {f.agent_name})")


if __name__ == "__main__":
    asyncio.run(main())

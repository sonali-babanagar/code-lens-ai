import re


class CodeAnalyzer:
    """Analyzes code metadata without LLM — detects language, counts functions/classes."""

    LANGUAGE_HINTS = {
        "python": [r"\bdef\b", r"\bimport\b", r"\bclass\b.*:", r"self\.", r"async def"],
        "javascript": [r"\bfunction\b", r"\bconst\b", r"\blet\b", r"=>", r"\brequire\b"],
        "typescript": [r"\binterface\b", r":\s*string", r":\s*number", r"\btype\b\s+\w+"],
        "java": [r"\bpublic\s+class\b", r"\bprivate\b", r"\bvoid\b", r"\bSystem\.out"],
    }

    def analyze(self, code: str, language: str | None = None) -> dict:
        if not language:
            language = self._detect_language(code)

        lines = code.strip().splitlines()
        return {
            "language": language,
            "total_lines": len(lines),
            "function_count": self._count_pattern(code, language),
            "class_count": len(re.findall(r"^\s*class\s+\w+", code, re.MULTILINE)),
            "has_imports": bool(re.search(r"^\s*(import|from|require|include)", code, re.MULTILINE)),
        }

    def _detect_language(self, code: str) -> str:
        scores = {}
        for lang, patterns in self.LANGUAGE_HINTS.items():
            scores[lang] = sum(1 for p in patterns if re.search(p, code))
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "unknown"

    def _count_pattern(self, code: str, language: str) -> int:
        patterns = {
            "python": r"^\s*(async\s+)?def\s+\w+",
            "javascript": r"(function\s+\w+|\w+\s*=\s*(async\s+)?\(.*?\)\s*=>)",
            "typescript": r"(function\s+\w+|\w+\s*=\s*(async\s+)?\(.*?\)\s*=>)",
            "java": r"(public|private|protected)\s+\w+\s+\w+\s*\(",
        }
        pattern = patterns.get(language, patterns["python"])
        return len(re.findall(pattern, code, re.MULTILINE))

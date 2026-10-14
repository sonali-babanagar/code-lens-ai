from src.schemas.review import AgentOutput, Finding, ReviewResult, Severity


class Synthesizer:
    """Merges findings from all agents into a single ReviewResult."""

    def synthesize(
        self,
        session_id: str,
        code: str,
        language: str,
        agent_outputs: list[AgentOutput],
    ) -> ReviewResult:
        all_findings = []
        for output in agent_outputs:
            all_findings.extend(output.findings)

        all_findings = self._deduplicate(all_findings)
        all_findings = self._sort_by_severity(all_findings)
        summary = self._build_summary(all_findings)

        return ReviewResult(
            session_id=session_id,
            code_snippet_preview=code[:200],
            language=language,
            findings=all_findings,
            summary=summary,
        )

    def _deduplicate(self, findings: list[Finding]) -> list[Finding]:
        seen = set()
        unique = []
        for f in findings:
            key = (f.title.lower(), f.line_number, f.file_name)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    def _sort_by_severity(self, findings: list[Finding]) -> list[Finding]:
        order = {Severity.critical: 0, Severity.warning: 1, Severity.info: 2}
        return sorted(findings, key=lambda f: order.get(f.severity, 3))

    def _build_summary(self, findings: list[Finding]) -> str:
        if not findings:
            return "No issues found. The code looks clean."

        counts = {}
        for f in findings:
            counts[f.severity.value] = counts.get(f.severity.value, 0) + 1

        parts = []
        if counts.get("critical"):
            parts.append(f"{counts['critical']} critical")
        if counts.get("warning"):
            parts.append(f"{counts['warning']} warning(s)")
        if counts.get("info"):
            parts.append(f"{counts['info']} info")

        return f"Found {len(findings)} issue(s): {', '.join(parts)}."

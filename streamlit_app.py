import streamlit as st
import requests
import json

API_BASE = "http://127.0.0.1:8000"

SUPPORTED_CODE_EXTENSIONS = ["py", "js", "ts", "java", "go", "rb", "rs", "cpp", "c", "cs", "php", "kt", "swift", "scala"]

SEVERITY_BADGES = {
    "critical": "🔴",
    "warning": "🟡",
    "info": "🔵",
}

# ── Page config ──────────────────────────────────────────────
st.set_page_config(page_title="CodeLens AI", page_icon="🔍", layout="wide")

# ── Session state defaults ───────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "review" not in st.session_state:
    st.session_state.review = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "📝 Submit Code"


# ── API helpers ──────────────────────────────────────────────
def api_post(path, **kwargs):
    try:
        r = requests.post(f"{API_BASE}{path}", timeout=180, **kwargs)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Is the backend running on port 8000?")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"API error: {e.response.text}")
        return None


def api_get(path, **kwargs):
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=30, **kwargs)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Is the backend running on port 8000?")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"API error: {e.response.text}")
        return None


def api_delete(path):
    try:
        r = requests.delete(f"{API_BASE}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


AGENT_LABELS = {
    "code_analysis": ("🔬", "Code Analysis"),
    "security_findings": ("🛡️", "Security Agent"),
    "architecture_findings": ("🏗️", "Architecture Agent"),
    "performance_findings": ("⚡", "Performance Agent"),
    "review_complete": ("✅", "Review Complete"),
}


def stream_review(session_id: str, code: str, language: str | None, progress_container):
    """Stream review via SSE endpoint, updating progress in real-time."""
    try:
        r = requests.post(
            f"{API_BASE}/sessions/{session_id}/review/stream",
            json={"code": code, "language": language},
            stream=True,
            timeout=180,
        )
        r.raise_for_status()
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API.")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"API error: {e.response.text}")
        return None

    final_data = None
    event_name = None
    progress_lines = []

    for line in r.iter_lines(decode_unicode=True):
        if not line:
            continue
        if line.startswith("event:"):
            event_name = line[len("event:"):].strip()
        elif line.startswith("data:") and event_name:
            data = json.loads(line[len("data:"):].strip())
            icon, label = AGENT_LABELS.get(event_name, ("🔄", event_name))

            if event_name == "code_analysis":
                progress_lines.append(f"{icon} **{label}**: {data.get('language', '?')} — {data.get('total_lines', '?')} lines, {data.get('function_count', '?')} functions")
            elif event_name == "review_complete":
                final_data = data
                progress_lines.append(f"{icon} **{label}**!")
            else:
                count = len(data.get("findings", []))
                progress_lines.append(f"{icon} **{label}**: {count} findings")

            # Re-render all lines so far
            progress_container.markdown("\n\n".join(progress_lines))
            event_name = None

    return final_data


# ── Sidebar: Session Management ──────────────────────────────
with st.sidebar:
    st.title("🔍 CodeLens AI")
    st.caption("Multi-agent AI Code Reviewer")

    if st.button("➕ New Review Session", use_container_width=True):
        data = api_post("/sessions")
        if data:
            st.session_state.session_id = data["session_id"]
            st.session_state.review = None
            st.session_state.active_tab = "📝 Submit Code"
            st.rerun()

    st.divider()
    st.subheader("Sessions")

    sessions = api_get("/sessions") or []
    for s in reversed(sessions):
        sid = s["session_id"]
        label = f"{s.get('language', '?') or '?'} • {s['status']}"
        cols = st.columns([4, 1])
        with cols[0]:
            if st.button(f"📄 {sid[:10]}...\n{label}", key=f"sel_{sid}", use_container_width=True):
                st.session_state.session_id = sid
                review = api_get(f"/sessions/{sid}/review")
                st.session_state.review = review
                st.session_state.active_tab = "📊 Review Results" if review else "📝 Submit Code"
                st.rerun()
        with cols[1]:
            if st.button("🗑️", key=f"del_{sid}"):
                api_delete(f"/sessions/{sid}")
                if st.session_state.session_id == sid:
                    st.session_state.session_id = None
                    st.session_state.review = None
                st.rerun()


# ── Main Area ────────────────────────────────────────────────
if not st.session_state.session_id:
    # Auto-create a session so the user lands on a usable page, not a blank one
    data = api_post("/sessions")
    if data:
        st.session_state.session_id = data["session_id"]
        st.rerun()
    st.stop()

session_id = st.session_state.session_id
st.caption(f"Session: `{session_id[:16]}...`")

active_tab = st.radio(
    "View",
    ["📝 Submit Code", "📊 Review Results", "💬 Chat"],
    key="active_tab",
    horizontal=True,
    label_visibility="collapsed",
)
st.divider()


# ── Section: Submit Code ─────────────────────────────────────
if active_tab == "📝 Submit Code":
    has_review = st.session_state.review is not None

    if has_review:
        st.success(f"✅ {st.session_state.review.get('summary', 'Review complete')}")
        st.caption("This session already has a review. Start a new session or re-upload below.")
        if st.button("🔄 New Review (same session)", type="secondary"):
            st.session_state.review = None
            st.rerun()
    else:
        input_method = st.radio(
            "How do you want to submit code?",
            ["Paste Code", "Upload File", "Upload Zip", "GitHub URL"],
            horizontal=True,
        )

        if input_method == "Paste Code":
            language = st.selectbox(
                "Language (optional — auto-detected if blank)",
                ["", "python", "javascript", "typescript", "java", "go", "ruby", "rust", "cpp", "c", "csharp", "php"],
            )
            code = st.text_area("Paste your code here", height=300, placeholder="def get_user(username):\n    ...")

            if st.button("🚀 Run Review", type="primary", disabled=not code):
                progress = st.empty()
                progress.markdown("⏳ Starting review pipeline...")
                data = stream_review(session_id, code, language or None, progress)
                if data:
                    st.session_state.review = data
                    st.session_state.active_tab = "📊 Review Results"
                    st.toast("✅ Review complete!")
                    st.rerun()

        elif input_method == "Upload File":
            uploaded = st.file_uploader(
                "Upload a code file",
                type=SUPPORTED_CODE_EXTENSIONS,
            )
            if uploaded and st.button("🚀 Run Review", type="primary"):
                with st.spinner("Agents analyzing your code..."):
                    data = api_post(
                        f"/sessions/{session_id}/review/upload",
                        files={"file": (uploaded.name, uploaded.getvalue(), "application/octet-stream")},
                    )
                    if data:
                        st.session_state.review = data
                        st.session_state.active_tab = "📊 Review Results"
                        st.toast("✅ Review complete!")
                        st.rerun()

        elif input_method == "Upload Zip":
            uploaded = st.file_uploader("Upload a zip file", type=["zip"])
            if uploaded and st.button("🚀 Run Review", type="primary"):
                with st.spinner("Extracting and analyzing files..."):
                    data = api_post(
                        f"/sessions/{session_id}/review/upload",
                        files={"file": (uploaded.name, uploaded.getvalue(), "application/zip")},
                    )
                    if data:
                        st.session_state.review = data
                        st.session_state.active_tab = "📊 Review Results"
                        st.toast("✅ Review complete!")
                        st.rerun()

        else:  # GitHub URL
            github_url = st.text_input(
                "GitHub URL",
                placeholder="https://github.com/owner/repo/blob/main/app.py  or  .../pull/42",
            )
            st.caption("Supports: file URLs, raw URLs, and PR URLs (public repos)")

            if st.button("🚀 Run Review", type="primary", disabled=not github_url):
                with st.spinner("Fetching from GitHub and analyzing..."):
                    data = api_post(
                        f"/sessions/{session_id}/review/github",
                        json={"github_url": github_url},
                    )
                    if data:
                        st.session_state.review = data
                        st.session_state.active_tab = "📊 Review Results"
                        st.toast("✅ Review complete!")
                        st.rerun()


# ── Section: Review Results ────────────────────────────────
elif active_tab == "📊 Review Results":
    review = st.session_state.review
    if not review:
        st.info("No review yet. Submit code in the first tab.")
    else:
        is_multi = "file_reviews" in review and review["file_reviews"]

        # Summary
        st.markdown(f"### {review['summary']}")
        if is_multi:
            st.caption(f"Files reviewed: **{', '.join(review.get('files_reviewed', []))}**")
        else:
            st.caption(f"Language: **{review.get('language', '?')}** • Reviewed at: {review.get('reviewed_at', 'N/A')}")

            with st.expander("📄 Submitted Code", expanded=False):
                st.code(review.get("code_snippet_preview", ""), language=review.get("language", ""))

        st.divider()

        # Filters
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            sev_filter = st.selectbox("Severity", ["all", "critical", "warning", "info"])
        with col2:
            cat_filter = st.selectbox("Category", ["all", "security", "architecture", "performance"])
        with col3:
            agent_filter = st.selectbox("Agent", ["all", "security_agent", "architecture_agent", "performance_agent", "cross_reference_agent"])
        with col4:
            if is_multi:
                file_options = ["all"] + review.get("files_reviewed", [])
                file_filter = st.selectbox("File", file_options)
            else:
                file_filter = "all"

        # Fetch filtered findings
        params = {}
        if sev_filter != "all":
            params["severity"] = sev_filter
        if cat_filter != "all":
            params["category"] = cat_filter
        if agent_filter != "all":
            params["agent"] = agent_filter
        if file_filter != "all":
            params["file_name"] = file_filter

        findings = api_get(f"/sessions/{session_id}/findings", params=params)
        if findings is None:
            # Fallback: gather from review data
            findings = review.get("findings", [])
            if is_multi:
                all_f = []
                for fr in review.get("file_reviews", {}).values():
                    all_f.extend(fr.get("findings", []))
                all_f.extend(review.get("cross_file_findings", []))
                findings = all_f

        # Cross-file findings section (multi-file only)
        if is_multi and review.get("cross_file_findings") and file_filter == "all" and agent_filter in ("all", "cross_reference_agent"):
            st.subheader("🔗 Cross-File Issues (Level 2)")
            cross = review["cross_file_findings"]
            if sev_filter != "all":
                cross = [f for f in cross if f["severity"] == sev_filter]
            if not cross:
                st.success("No cross-file issues found.")
            for f in cross:
                badge = SEVERITY_BADGES.get(f["severity"], "⚪")
                file_tag = f" [{f['file_name']}]" if f.get("file_name") else ""
                with st.expander(f"{badge} **{f['title']}**{file_tag} — _{f['category']}_"):
                    st.markdown(f"**Agent:** {f['agent_name']}  •  **Severity:** {f['severity']}")
                    st.markdown(f"**Description:** {f['description']}")
                    st.markdown("**Suggestion:**")
                    st.code(f["suggestion"])
            st.divider()
            # Remove cross-file findings from main list to avoid duplication
            findings = [f for f in findings if f.get("agent_name") != "cross_reference_agent"]

        # Per-file findings
        if is_multi and file_filter == "all":
            st.subheader("📁 Per-File Issues (Level 1)")
            for fname in review.get("files_reviewed", []):
                file_findings = [f for f in findings if f.get("file_name") == fname]
                if not file_findings:
                    continue
                st.markdown(f"#### 📄 {fname} ({len(file_findings)} issues)")
                for f in file_findings:
                    badge = SEVERITY_BADGES.get(f["severity"], "⚪")
                    line_info = f" (line {f['line_number']})" if f.get("line_number") else ""
                    with st.expander(f"{badge} **{f['title']}**{line_info} — _{f['category']}_"):
                        st.markdown(f"**Agent:** {f['agent_name']}  •  **Severity:** {f['severity']}")
                        st.markdown(f"**Description:** {f['description']}")
                        st.markdown("**Suggestion:**")
                        st.code(f["suggestion"])
                        if f.get("source_reference"):
                            st.caption(f"📚 Reference: {f['source_reference']}")
        else:
            # Single file or filtered view
            if not findings:
                st.success("No findings match the current filters.")
            else:
                for f in findings:
                    badge = SEVERITY_BADGES.get(f["severity"], "⚪")
                    line_info = f" (line {f['line_number']})" if f.get("line_number") else ""
                    file_tag = f" [{f['file_name']}]" if f.get("file_name") else ""

                    with st.expander(f"{badge} **{f['title']}**{line_info}{file_tag} — _{f['category']}_"):
                        st.markdown(f"**Agent:** {f['agent_name']}  •  **Severity:** {f['severity']}")
                        st.markdown(f"**Description:** {f['description']}")
                        st.markdown("**Suggestion:**")
                        st.code(f["suggestion"], language=review.get("language", ""))
                        if f.get("source_reference"):
                            st.caption(f"📚 Reference: {f['source_reference']}")


# ── Section: Chat ─────────────────────────────────────────────
else:  # Chat
    if not st.session_state.review:
        st.info("Submit code for review first, then chat about the findings.")
    else:
        # Load and display chat history
        history = api_get(f"/sessions/{session_id}/chat/history") or []

        for msg in history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Chat input
        if prompt := st.chat_input("Ask about the review findings..."):
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    r = requests.post(
                        f"{API_BASE}/sessions/{session_id}/chat/stream",
                        json={"message": prompt},
                        stream=True,
                        timeout=120,
                    )
                    r.raise_for_status()
                    placeholder = st.empty()
                    full_reply = []
                    for line in r.iter_lines(decode_unicode=True):
                        if not line:
                            continue
                        if line.startswith("event:"):
                            continue
                        if line.startswith("data:"):
                            token = line[len("data:"):].lstrip(" ")
                            if token:
                                full_reply.append(token)
                                placeholder.markdown("".join(full_reply) + "▌")
                    placeholder.markdown("\n\n".join(full_reply) if not full_reply else "".join(full_reply))
                    st.rerun()
                except Exception:
                    st.error("Failed to get a response.")

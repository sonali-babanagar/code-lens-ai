import re
import httpx
from src.config import settings
from src.utils.file_utils import detect_language_from_filename


def _get_headers() -> dict:
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = settings.GITHUB_TOKEN
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def parse_github_url(url: str) -> dict:
    """Parse a GitHub URL and return its type and components."""
    # PR URL: github.com/owner/repo/pull/123
    pr_match = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if pr_match:
        return {
            "type": "pr",
            "owner": pr_match.group(1),
            "repo": pr_match.group(2),
            "pr_number": int(pr_match.group(3)),
        }

    # Raw URL: raw.githubusercontent.com/owner/repo/branch/path
    raw_match = re.match(r"https?://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.*)", url)
    if raw_match:
        return {
            "type": "raw",
            "owner": raw_match.group(1),
            "repo": raw_match.group(2),
            "branch": raw_match.group(3),
            "path": raw_match.group(4),
            "raw_url": url,
        }

    # Blob URL: github.com/owner/repo/blob/branch/path
    blob_match = re.match(r"https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.*)", url)
    if blob_match:
        owner, repo, branch, path = blob_match.group(1), blob_match.group(2), blob_match.group(3), blob_match.group(4)
        return {
            "type": "file",
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "path": path,
            "raw_url": f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}",
        }

    raise ValueError(f"Unsupported GitHub URL format: {url}")


async def fetch_file_content(url: str) -> tuple[str, str, str]:
    """Fetch a single file from GitHub. Returns (filename, code, language)."""
    parsed = parse_github_url(url)
    if parsed["type"] == "pr":
        raise ValueError("Use fetch_pr_files() for PR URLs")

    raw_url = parsed["raw_url"]
    path = parsed["path"]
    filename = path.split("/")[-1]
    language = detect_language_from_filename(filename)

    async with httpx.AsyncClient() as client:
        r = await client.get(raw_url, headers=_get_headers(), follow_redirects=True)
        r.raise_for_status()
        return filename, r.text, language


async def fetch_pr_files(owner: str, repo: str, pr_number: int) -> list[tuple[str, str, str]]:
    """Fetch changed files from a PR. Returns list of (filename, code, language)."""
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"

    async with httpx.AsyncClient() as client:
        r = await client.get(api_url, headers=_get_headers())
        r.raise_for_status()
        pr_files = r.json()

    results = []
    async with httpx.AsyncClient() as client:
        for f in pr_files:
            filename = f["filename"]
            language = detect_language_from_filename(filename)
            if language == "unknown":
                continue
            if f.get("status") == "removed":
                continue

            raw_url = f.get("raw_url")
            if not raw_url:
                continue

            r = await client.get(raw_url, headers=_get_headers(), follow_redirects=True)
            if r.status_code == 200:
                results.append((filename, r.text, language))

    return results

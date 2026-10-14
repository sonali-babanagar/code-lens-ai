import os
import zipfile
import tempfile

CODE_EXTENSIONS = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".java": "java", ".go": "go", ".rb": "ruby", ".rs": "rust",
    ".cpp": "cpp", ".c": "c", ".cs": "csharp", ".php": "php",
    ".kt": "kotlin", ".swift": "swift", ".scala": "scala",
}

MAX_FILE_SIZE = 500_000  # 500KB per file


def detect_language_from_filename(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return CODE_EXTENSIONS.get(ext, "unknown")


def is_code_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in CODE_EXTENSIONS


def read_uploaded_file(content: bytes, filename: str) -> tuple[str, str]:
    """Returns (code_text, language) from an uploaded file."""
    if len(content) > MAX_FILE_SIZE:
        raise ValueError(f"File too large: {len(content)} bytes (max {MAX_FILE_SIZE})")
    language = detect_language_from_filename(filename)
    return content.decode("utf-8", errors="replace"), language


def read_uploaded_zip(content: bytes) -> list[tuple[str, str, str]]:
    """Returns list of (filename, code_text, language) from a zip file."""
    results = []
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        with zipfile.ZipFile(tmp_path, "r") as zf:
            for name in zf.namelist():
                if name.endswith("/") or not is_code_file(name):
                    continue
                data = zf.read(name)
                if len(data) > MAX_FILE_SIZE:
                    continue
                language = detect_language_from_filename(name)
                code = data.decode("utf-8", errors="replace")
                results.append((os.path.basename(name), code, language))
    finally:
        os.unlink(tmp_path)

    return results

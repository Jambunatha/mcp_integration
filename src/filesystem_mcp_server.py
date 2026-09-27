from pathlib import Path
from datetime import datetime
import os
import time

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIRECTORY = Path(
    os.getenv("MCP_ROOT_DIRECTORY", BASE_DIR / "data" / "files")
).resolve()
ROOT_DIRECTORY.mkdir(parents=True, exist_ok=True)

mcp = MCPServer(
    "Filesystem Server",
    instructions="Provides controlled file system operations.",
)


def get_safe_path(path: str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = BASE_DIR / candidate
    candidate = candidate.resolve()

    if candidate != ROOT_DIRECTORY and ROOT_DIRECTORY not in candidate.parents:
        raise ToolError("Path is outside the configured root directory.")
    return candidate


@mcp.tool()
def read_file(filepath: str) -> dict:
    """Read a text file and return its content and metadata."""
    path = get_safe_path(filepath)
    if not path.is_file():
        raise ToolError(f"File not found: {filepath}")
    try:
        content = path.read_text(encoding="utf-8")
        stat = path.stat()
        return {
            "success": True,
            "filename": path.name,
            "content": content,
            "metadata": {
                "size_bytes": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            },
        }
    except OSError as exc:
        raise ToolError(f"Unable to read file: {exc}") from exc


@mcp.tool()
def list_files(directory: str = "data/files", extension: str | None = None) -> list[dict]:
    """List files in a directory with optional extension filtering."""
    path = get_safe_path(directory)
    if not path.is_dir():
        raise ToolError(f"Directory not found: {directory}")

    result = []
    for item in sorted(path.iterdir()):
        if not item.is_file():
            continue
        if extension and item.suffix.lower() != extension.lower():
            continue
        stat = item.stat()
        result.append({
            "name": item.name,
            "size_bytes": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    return result


@mcp.tool()
def write_file(filepath: str, content: str) -> dict:
    """Write text content to a file."""
    path = get_safe_path(filepath)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {
            "success": True,
            "filename": path.name,
            "bytes_written": path.stat().st_size,
        }
    except OSError as exc:
        raise ToolError(f"Unable to write file: {exc}") from exc


@mcp.tool()
def search_in_file(filepath: str, keyword: str) -> dict:
    """Search a text file case-insensitively and return matching lines."""
    path = get_safe_path(filepath)
    if not path.is_file():
        raise ToolError(f"File not found: {filepath}")
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ToolError(f"Unable to read file: {exc}") from exc

    matches = [
        {"line": number, "text": line}
        for number, line in enumerate(lines, start=1)
        if keyword.lower() in line.lower()
    ]
    return {
        "success": True,
        "filename": path.name,
        "keyword": keyword,
        "match_count": len(matches),
        "matches": matches,
    }


@mcp.tool()
def watch_directory(directory: str = "data/files", seconds: int = 5) -> dict:
    """Watch a directory for newly created files for a short period."""
    path = get_safe_path(directory)
    if not path.is_dir():
        raise ToolError(f"Directory not found: {directory}")

    wait_seconds = max(1, min(seconds, 30))
    before = {item.name for item in path.iterdir() if item.is_file()}
    time.sleep(wait_seconds)
    after = {item.name for item in path.iterdir() if item.is_file()}

    return {
        "success": True,
        "directory": str(path),
        "new_files": sorted(after - before),
        "watched_seconds": wait_seconds,
    }


@mcp.tool()
def batch_process(directory: str = "data/files") -> dict:
    """Process all supported text files in a directory."""
    path = get_safe_path(directory)
    if not path.is_dir():
        raise ToolError(f"Directory not found: {directory}")

    results = []
    for item in sorted(path.iterdir()):
        if not item.is_file() or item.suffix.lower() not in {".txt", ".md", ".json"}:
            continue
        try:
            content = item.read_text(encoding="utf-8")
            results.append({
                "filename": item.name,
                "processed": True,
                "characters": len(content),
            })
        except OSError as exc:
            results.append({
                "filename": item.name,
                "processed": False,
                "error": str(exc),
            })

    return {
        "success": True,
        "directory": str(path),
        "total_files": len(results),
        "processed_files": sum(1 for item in results if item["processed"]),
        "results": results,
    }


@mcp.resource("filesystem://root")
def root_resource() -> str:
    """Return the configured root directory."""
    return str(ROOT_DIRECTORY)


@mcp.resource("filesystem://files")
def files_resource() -> str:
    """Return the current files under the configured root."""
    return "\n".join(
        item.name for item in sorted(ROOT_DIRECTORY.iterdir()) if item.is_file()
    )


if __name__ == "__main__":
    mcp.run()

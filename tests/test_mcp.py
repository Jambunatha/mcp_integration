import asyncio
import sys
from pathlib import Path

from mcp import Client
from mcp.client.stdio import StdioServerParameters

ROOT = Path(__file__).resolve().parents[1]
SERVER_FILE = ROOT / "src" / "filesystem_mcp_server.py"


async def main():
    server = StdioServerParameters(command=sys.executable, args=[str(SERVER_FILE)])

    async with Client(server) as client:
        tools = await client.list_tools()
        names = {tool.name for tool in tools.tools}
        expected = {
            "read_file", "list_files", "write_file", "search_in_file",
            "watch_directory", "batch_process",
        }
        assert expected.issubset(names)

        resources = await client.list_resources()
        resource_names = {str(resource.uri) for resource in resources.resources}
        assert "filesystem://root" in resource_names
        assert "filesystem://files" in resource_names

        result = await client.call_tool("list_files", {"directory": "data/files"})
        assert result.is_error is False

        result = await client.call_tool(
            "read_file", {"filepath": "data/files/sample1.txt"}
        )
        assert result.is_error is False

        result = await client.call_tool(
            "search_in_file",
            {"filepath": "data/files/sample1.txt", "keyword": "Python"},
        )
        assert result.is_error is False

        result = await client.call_tool("batch_process", {"directory": "data/files"})
        assert result.is_error is False

    print("MCP checks passed.")


if __name__ == "__main__":
    asyncio.run(main())

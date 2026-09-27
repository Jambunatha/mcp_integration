import asyncio
import sys
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from mcp import Client
from mcp.client.stdio import StdioServerParameters
from mcp.types import TextContent

BASE_DIR = Path(__file__).resolve().parent.parent
SERVER_FILE = BASE_DIR / "src" / "filesystem_mcp_server.py"


class AgentState(TypedDict, total=False):
    query: str
    tool_name: str
    arguments: dict[str, Any]
    result: str


def choose_operation(state: AgentState) -> AgentState:
    """Choose an MCP operation from the user's request."""
    query = state["query"].lower()

    if "watch" in query or "monitor" in query:
        return {"tool_name": "watch_directory", "arguments": {"directory": "data/files", "seconds": 3}}
    if "batch" in query:
        return {"tool_name": "batch_process", "arguments": {"directory": "data/files"}}
    if "search" in query or "find" in query:
        keyword = "Python" if "python" in query else "MCP"
        return {
            "tool_name": "search_in_file",
            "arguments": {"filepath": "data/files/sample1.txt", "keyword": keyword},
        }
    if "read" in query:
        return {"tool_name": "read_file", "arguments": {"filepath": "data/files/sample1.txt"}}
    return {"tool_name": "list_files", "arguments": {"directory": "data/files"}}


async def call_mcp(state: AgentState) -> AgentState:
    """Connect to the MCP server and call the selected tool."""
    server = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_FILE)],
    )

    async with Client(server) as client:
        result = await client.call_tool(state["tool_name"], state["arguments"])
        output = [item.text for item in result.content if isinstance(item, TextContent)]
        return {"result": "\n".join(output)}


def build_agent():
    workflow = StateGraph(AgentState)
    workflow.add_node("choose_operation", choose_operation)
    workflow.add_node("call_mcp", call_mcp)
    workflow.set_entry_point("choose_operation")
    workflow.add_edge("choose_operation", "call_mcp")
    workflow.add_edge("call_mcp", END)
    return workflow.compile()


async def run(query: str):
    agent = build_agent()
    result = await agent.ainvoke({"query": query})
    print(f"Tool: {result['tool_name']}")
    print("Result:")
    print(result["result"])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python src/matching_agent.py "List files"')
        raise SystemExit(1)
    asyncio.run(run(" ".join(sys.argv[1:])))

# MCP Integration

This project contains a filesystem MCP server and a LangGraph client that uses the server.

## Project structure

```text
mcp_integration/
├── src/
│   ├── filesystem_mcp_server.py
│   └── matching_agent.py
├── data/
│   └── files/
│       ├── sample1.txt
│       ├── sample2.txt
│       └── sample3.txt
├── tests/
│   └── test_mcp.py
├── docs/
│   └── workflow.md
├── requirements.txt
└── .env.example
```

## Setup

Use Python 3.10 or later.

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Install the packages:

```bash
pip install -r requirements.txt
```

## Run

The MCP server uses stdio, so the client starts it automatically.

List files:

```bash
python src/matching_agent.py "List files"
```

Read a file:

```bash
python src/matching_agent.py "Read the file"
```

Search a file:

```bash
python src/matching_agent.py "Find Python"
```

Batch process files:

```bash
python src/matching_agent.py "Batch process all files"
```

Watch the directory:

```bash
python src/matching_agent.py "Watch the directory"
```

## Test

```bash
python tests/test_mcp.py
```

Expected output:

```text
MCP checks passed.
```

The test checks tool discovery, resource discovery and tool execution.

## Configuration

The server reads `MCP_ROOT_DIRECTORY` when it starts. The default is `data/files`.

The server does not allow access outside this configured directory.

## Flow

```text
User
  |
  v
LangGraph Agent
  |
  v
MCP Client
  |
  | MCP / JSON-RPC 2.0 over stdio
  v
Filesystem MCP Server
  |
  +-- read_file
  +-- list_files
  +-- write_file
  +-- search_in_file
  +-- watch_directory
  +-- batch_process
  |
  v
File System
```

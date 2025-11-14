# CVE MCP Server

This is a Model Context Protocol (MCP) server that provides CVE database tools.

## Features

- CVE lookup by ID
- Search by exploit maturity
- Search by severity
- Search by keyword
- List recent CVEs

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file:

```env
MONGO_URI=mongodb://localhost:27017/
MONGO_DB=genai_kb
MONGO_COLLECTION=cve_details
MCP_SERVER_PORT=8001
```

## Running the Server

```bash
python server.py
```

Or use stdio mode for MCP clients:

```bash
python server.py --stdio
```

## API Endpoints

- `POST /mcp/tools` - Get available tools
- `POST /mcp/call` - Call a tool


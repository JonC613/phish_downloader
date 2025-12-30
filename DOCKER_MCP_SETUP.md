# MCP Server with Docker & Claude Desktop

## Quick Start

### 1. Build and Start Docker Container

```bash
docker-compose up -d mcp_server
```

Verify it's running:
```bash
docker ps | grep phish_mcp_server
```

### 2. Configure Claude Desktop

**Windows Path:** `%APPDATA%\Claude\claude_desktop_config.json`

Add this configuration:

```json
{
  "mcpServers": {
    "phish-shows": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "phish_mcp_server",
        "python",
        "mcp_server.py"
      ]
    }
  }
}
```

### 3. Restart Claude Desktop

Close and reopen Claude Desktop to load the MCP server.

### 4. Query in Claude

You can now ask Claude questions like:

- "What shows did Phish play in 1997?"
- "Show me the setlist for 12/31/1995"
- "How many times has Phish played You Enjoy Myself?"
- "What venues has Phish played in Colorado?"
- "Give me statistics on the Phish database"

---

## Alternative: Use Local Python (No Docker)

If you prefer running directly without Docker, use this config instead:

```json
{
  "mcpServers": {
    "phish-shows": {
      "command": "python",
      "args": [
        "c:\\dev\\phish_downloader\\mcp_server.py"
      ]
    }
  }
}
```

Then just restart Claude Desktop - no Docker needed.

---

## Testing

### Verify Container is Working

```bash
docker exec phish_mcp_server python test_mcp.py
```

### View Container Logs

```bash
docker logs phish_mcp_server
```

### Stop Container

```bash
docker-compose down mcp_server
```

---

## Architecture

- **Dockerfile.mcp**: Builds the MCP server image
- **docker-compose.yml**: Orchestrates all services (postgres, streamlit, mcp_server)
- **mcp.json**: Configuration for Claude Desktop (includes both local and Docker options)

## Troubleshooting

**Error: "phish_mcp_server is not running"**
```bash
docker-compose up -d mcp_server
```

**Error: "Cannot connect to Docker daemon"**
- Ensure Docker Desktop is running on Windows

**Claude Desktop not recognizing the server**
- Restart Claude Desktop completely
- Check that container name matches exactly in config

## File Structure

```
phish_downloader/
├── Dockerfile.mcp              (MCP server image)
├── docker-compose.yml          (Added mcp_server service)
├── mcp.json                    (Claude Desktop config)
├── mcp_server.py               (MCP server code)
└── normalized_shows/           (Show data - mounted read-only)
```

# Using Phish Shows MCP Server with Claude Desktop

## ✅ Docker Setup Complete

Your MCP server is running in Docker and ready to use with Claude Desktop!

## Step 1: Get the Config File

The `mcp.json` file in your project folder has both options configured.

## Step 2: Add to Claude Desktop Config

### Windows Users:

1. **Find the config file:**
   - Press `Win + R`
   - Type: `%APPDATA%\Claude`
   - Click OK

2. **Open `claude_desktop_config.json` in a text editor**

3. **Add this to the `mcpServers` section:**

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

**Full example file:**
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

4. **Save the file**

5. **Restart Claude Desktop completely** (close and reopen)

## Step 3: Use in Claude

Once configured, you'll see a "Tools" icon in Claude. The Phish Shows MCP tools are now available!

**Example queries:**
- "What shows did Phish play in 1997?"
- "Show me the setlist for 12/31/1995 at Madison Square Garden"
- "How many times have they played You Enjoy Myself?"
- "What venues has Phish played in Colorado?"
- "Give me some statistics about the Phish shows database"

## Verify It's Working

Run this to confirm the container is still running:

```bash
docker ps --filter "name=phish_mcp"
```

You should see:
```
phish_mcp_server    Up    phish_downloader-mcp_server
```

## Troubleshooting

### Error: "Tool not found" in Claude
- **Solution**: Make sure the container is running: `docker-compose up -d mcp_server`
- Restart Claude Desktop

### Error: "docker: command not found"
- **Solution**: Ensure Docker Desktop is installed and running on Windows

### Need to rebuild the container?
```bash
docker-compose down mcp_server
docker-compose build mcp_server
docker-compose up -d mcp_server
```

### Want to use local Python instead (no Docker)?
Change the config to:
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

## Running Services

### View running containers:
```bash
docker ps
```

### Check logs:
```bash
docker logs phish_mcp_server
```

### Restart container:
```bash
docker-compose restart mcp_server
```

### Stop everything:
```bash
docker-compose down
```

## Architecture

```
Claude Desktop
    ↓
mcp.json config
    ↓
Docker container (phish_mcp_server)
    ↓
mcp_server.py
    ↓
normalized_shows/ (2,202 shows)
```

## Quick Facts

- **2,202 shows** loaded (1983-2025)
- **841 unique venues**
- **1,217 unique songs**
- **631 performances** of "You Enjoy Myself"
- **93 shows** at Madison Square Garden

Happy querying! 🎵

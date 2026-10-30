# Open Food Facts folksonomy REST API MCP server

Open Food Facts folksonomy REST API is available as a hosted [Model Context Protocol](https://modelcontextprotocol.io) (MCP)
server, so AI agents such as Claude, ChatGPT, Cursor and VS Code can call it as tools.

| | |
| --- | --- |
| Server URL | `https://app.getelva.ai/mcp/elvademo/open-food-facts-folksonomy-rest-api` |
| Install page | https://app.getelva.ai/mcp/elvademo/open-food-facts-folksonomy-rest-api/install |
| Tools | 20, one per operation in [`openapi.json`](https://api.folksonomy.openfoodfacts.org/openapi.json) |
| Calls | `https://api.folksonomy.openfoodfacts.org` |
| Authentication | Your own API token, sent as a bearer token. Your MCP client asks for it when you connect. |

## Install

**[Open the install page](https://app.getelva.ai/mcp/elvademo/open-food-facts-folksonomy-rest-api/install)** for step-by-step setup in Claude, ChatGPT,
Cursor, VS Code and other clients, or use one of the options below.

[![Install in Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=Open%20Food%20Facts%20folksonomy%20REST%20API&config=eyJ1cmwiOiJodHRwczovL2FwcC5nZXRlbHZhLmFpL21jcC9lbHZhZGVtby9vcGVuLWZvb2QtZmFjdHMtZm9sa3Nvbm9teS1yZXN0LWFwaSJ9)
[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_MCP-0098FF?logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=open-food-facts-folksonomy-rest-api&config=%7B%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Fapp.getelva.ai%2Fmcp%2Felvademo%2Fopen-food-facts-folksonomy-rest-api%22%7D)

### Claude Code

```bash
claude mcp add --transport http open-food-facts-folksonomy-rest-api https://app.getelva.ai/mcp/elvademo/open-food-facts-folksonomy-rest-api
```

### Claude (claude.ai and Claude Desktop)

Settings → Connectors → **Add custom connector**, then paste the server URL.

### ChatGPT

Settings → Apps & Connectors → Advanced settings → turn on **Developer mode**, then
**Create** a connector and paste the server URL.

### Any other MCP client

```json
{
  "mcpServers": {
    "open-food-facts-folksonomy-rest-api": {
      "url": "https://app.getelva.ai/mcp/elvademo/open-food-facts-folksonomy-rest-api"
    }
  }
}
```

---

Generated from the API's published OpenAPI spec and hosted by [Elva](https://getelva.ai?utm_source=github&utm_medium=openfoodfacts/folksonomy_api&utm_campaign=githubprs).

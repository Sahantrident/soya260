# Soya · 260 Brands Copilot Playbook

The 260 Brands Microsoft 365 Copilot playbook and **Soya**, its Copilot coach agent.

| Path | What it is | Hosted on |
|---|---|---|
| `web/index.html` | The Copilot Playbook (Home, Demo Lab, Organisation, Departments, People) | GitHub Pages |
| `web/chat.html` | Chat with Soya, linked from the playbook's "Chat with Soya" button | GitHub Pages |
| `api/` | Azure Function (Python) that proxies chat to the `soya-260` Foundry agent | Azure Functions |

GitHub Pages only serves static files, so the agent call runs in the Azure Function.
The Function signs in with its managed identity, so no keys reach the browser.

Live site: `https://sahantrident.github.io/soya260/` · API: `https://soya260-chat.azurewebsites.net/api/chat` (Function App `soya260-chat`, resource group `COPILOT`, Flex Consumption, 512 MB, max 5 instances)

## 1. Deploy the API (Azure Function App)
1. Create a Function App: **Python 3.11**, Linux, Flex Consumption plan.
2. Identity → **System assigned: On**.
3. Foundry project `proj-copilot` → Access control (IAM) → Add role assignment →
   **Azure AI User** → the Function App's managed identity. (Allow ~5 min to apply.)
4. Environment variables: `SOYA_PROJECT_ENDPOINT`, `SOYA_AGENT_NAME`,
   `MAX_MESSAGES_PER_HOUR`, `MAX_INPUT_CHARS` (see `api/local.settings.example.json`).
5. **CORS** → add `https://sahantrident.github.io` only (no path, no trailing slash). Don't use `*`.
6. Deploy the `api` folder: VS Code Azure Functions extension → Deploy,
   or `func azure functionapp publish <app-name>` from inside `api/`.

## 2. Point the chat page at the API
Set `API_BASE` in `web/chat.html` to the Function App URL and push to `main`.
The `Deploy site to GitHub Pages` workflow publishes `web/` on every push.

## Troubleshooting (Function App → Log stream)
- 401/403 → role assignment missing or still applying.
- CORS error in the browser console → the origin in step 5 doesn't match exactly.
- "agent not found" → check `SOYA_AGENT_NAME` and the project endpoint.

## Before sharing publicly
- Azure budget alert on the resource group.
- Keep the rate limit at 30/hour and cap the agent's output tokens.
- Only public-safe knowledge in the agent.

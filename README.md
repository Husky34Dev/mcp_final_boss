# MCP Groq Conversational Platform (Development Preview)

> **Note:** This project is under active development and not intended for production use. All code, features, and documentation are subject to change.
> 
> **License:** Open Source (MIT). You are free to use, modify, and share this project, but it is provided as-is and without warranty. See the LICENSE file for details.

A robust, modular, and enterprise-ready multi-agent conversational platform powered by LLMs and OpenAPI tools. Designed for seamless integration with business processes, secure data handling, and advanced context management.

---

## Key Features (In Progress)

- **Multi-Agent Architecture:** Automatic routing of user queries to specialized agents (billing, incidents, general inquiries, etc.).
- **OpenAPI Tool Integration:** Dynamic invocation of backend endpoints based on user intent, ensuring real-time and accurate data retrieval.
- **Conversational Context Management:** Remembers key data (e.g., DNI, query type) across turns for natural, referential dialogue.
- **Response Validation:** Prevents hallucinated answers by enforcing API/tool usage for data-driven queries.
- **Scalable & Maintainable:** Easily extend with new agents, tools, context extractors, or validation rules.
- **Enterprise-Grade Security:** Designed for secure API access and data privacy (ready for further enterprise hardening).

---

## Project Structure

```bash
├── app/
│   ├── agent/           # Agent logic and multi-agent router
│   ├── api/             # FastAPI backend endpoints
│   ├── config/          # Global configuration (loads JSON into framework)
│   ├── framework/       # Core context & conversation framework (JSON-driven)
│   ├── db/              # Demo database (SQLite)
│   ├── tools/           # OpenAPI tool discovery and definitions
│   └── utils/           # Utilities: formatters, guards, other helpers
├── main.py              # CLI for testing
├── chat_api.py          # REST API for frontend/web chat
├── index.html           # Demo frontend (web chat)
├── app/config/query_config.json  # Main JSON config controlling context and queries
├── requirements.txt     # Dependencies
```

---

## Quick Start

1. **Clone the repository:**
   ```sh
   git clone <repo-url>
   cd mcp_groq
   ```
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
3. **Start the backend (FastAPI):**
   ```sh
   uvicorn app.api.server:app --reload --port 8000
   ```
4. **Start the chat API:**
   ```sh
   uvicorn chat_api:app --reload --port 8001
   ```
5. **Open the frontend:**
   - Open `index.html` in your browser.

---

## How It Works

- Users interact via chat or CLI.
- The multi-agent router selects the appropriate agent based on the message.
- The agent leverages conversational context to recall key data (DNI, query type, etc.).
- For data-driven queries, the LLM automatically invokes the relevant API/tool.
- The response validator ensures only factual, API-backed answers are returned.
- Results are formatted and delivered to the user.

---

## Extending the Platform

- **Add new agents:** Implement a class in `app/agent/agents/` and register it in the router.
- **Expose new tools:** Add endpoints to the backend; they are auto-discovered as tools.
- **Custom context extractors:** Add methods to `ConversationContext` and include them in the extractor list.
- **Advanced validation:** Add custom rules to `LLMResponseGuard` as needed.

---

## Example: Referential Dialogue

1. User: `Show me the details for subscriber with DNI 12345678A`
2. User: `Now show me their outstanding invoices`
   - The system remembers the DNI and responds correctly without the user repeating it.

---

## License & Contact

MIT License. See LICENSE file for details. For questions, contact the author.

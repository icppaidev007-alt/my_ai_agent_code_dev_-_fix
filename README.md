# Autonomous Code-Fixing & Debugging Agent (Agentic AI)

An autonomous, lightweight **ReAct-style debugging agent** built in Python with OpenAI/Mistral tool-calling integration. The agent autonomously navigates legacy codebases, inspects code files, isolates root causes from customer bug tickets, implements patches, and verifies fixes with automated test suites.

---

## 🌟 Key Features

* **Autonomous Tool-Calling Loop:** Implements deterministic functions (`list_directory`, `search_files`, `read_file_lines`, `edit_file`, and execution tools) giving LLMs safe, structured access to codebase operations.
* **Zero Heavy Framework Overhead:** Built purely on fundamental LLM orchestration patterns without bloated third-party abstractions (e.g., LangChain/CrewAI).
* **Multi-Turn Reasoning & Reflection:** Continuously evaluates tool outputs, tracks thought processes, and iteratively tests fixes.
* **Dynamic Model Fallback:** Built-in model rotation mechanism to seamlessly handle rate limits and token budgets during long multi-step debugging runs.
* **Live Step-by-Step Logging:** Records thoughts, tool calls, arguments, and intermediate results for complete transparency.

---

## 🏗️ Architecture Flow

```
+-------------------------------------------------------------+
|                     Customer Bug Ticket                     |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|              LLM Agent Controller (Mistral/Groq)             |
|                 Multi-turn ReAct Loop                       |
+-------------------------------------------------------------+
         |                     |                     |
         v                     v                     v
+------------------+  +------------------+  +------------------+
|  Code Search &   |  |   Patch & File   |  |   Build & Test   |
| Codebase Inspect |  |      Editing     |  |    Execution     |
+------------------+  +------------------+  +------------------+
         |                     |                     |
         +---------------------+---------------------+
                              |
                              v
+-------------------------------------------------------------+
|           Verified Patch & Root-Cause Fix Report            |
+-------------------------------------------------------------+
```

---

## 🛠️ Tool Definitions

| Tool | Description |
| :--- | :--- |
| `list_directory(path)` | Safely inspects directory hierarchy. |
| `search_files(dir, ext, pattern)` | Regex & substring search across targeted file types. |
| `read_file_lines(path, start, end)` | Token-efficient chunk reading with line numbers. |
| `edit_file(path, search, replace)` | Precision string-replacement patch engine. |
| `run_build()` / `run_tests()` | Triggers local build chains and test runners. |

---

## 🚀 Getting Started

### Prerequisites
* Python 3.10+
* Mistral / OpenAI / Groq API Key

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/code-fixing-agent.git
   cd code-fixing-agent
   ```
2. Install dependencies:
   ```bash
   pip install openai
   ```
3. Set your API Key:
   ```bash
   export MISTRAL_API_KEY="your_api_key_here"   # Linux/macOS
   $env:MISTRAL_API_KEY="your_api_key_here"      # Windows PowerShell
   ```
4. Run the agent:
   ```bash
   python agent.py
   ```

---

## 📜 Example Run (muParser Ticket-842)
The agent was benchmarked against a real-world mathematical expression parser bug (`muParser`), where power operators (`^`) evaluated incorrectly during constant folding. The agent autonomously located the operator precedence logic in the AST parser, replaced the faulty folding logic, ran the test suite, and generated a verified fix report.

---

## 📄 License
MIT License

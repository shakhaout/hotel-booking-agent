# 🏨 AI Hotel Booking Agent

A professional-grade AI agent capable of searching for hotels, checking availability, and assisting with bookings. Built with **LangGraph**, **FastMCP**, **Redis**, and **Google Gemini**.

## 🚀 Key Features

-   **Intelligent Conversation**: Powered by Google's **Gemini 2.0 Flash** for fast and accurate reasoning.
-   **Structured Workflow**: Uses **LangGraph** to manage conversation state and decision-making loops.
-   **Tool Integration**: Connects to external services via the **Model Context Protocol (MCP)** using `FastMCP`.
    -   **Search**: Real-time hotel data via `SerpApi`.
    -   **Booking**: Simulation of booking actions.
-   **Persistent Memory**: Uses **Redis** for storing conversation history and user preferences (Vector & Key-Value).
-   **Interactive CLI**: Easy-to-use command-line interface for testing and interaction.

## 🛠️ Architecture

The project follows a CLIENT-SERVER architecture:

1.  **MCP Server (`src/server.py`)**:
    -   Runs as a subprocess.
    -   Exposes `search_hotels` and `book_hotel` tools.
    -   Built with `FastMCP`.

2.  **AI Agent (`src/agent_graph.py`)**:
    -   The "Client" that connects to the MCP Server.
    -   Constructs a `LangGraph` workflow.
    -   Manages state, memory, and LLM interaction.

## 📋 Prerequisites

-   **Python 3.11**
-   **Redis Server** (required for memory)
    -   Install via Docker: `docker run -d -p 6379:6379 redis/redis-stack:latest`
    -   Or install locally via Homebrew/APT.
-   **API Keys**:
    -   `GOOGLE_API_KEY` (Get from [Google AI Studio](https://aistudio.google.com/))
    -   `SERPAPI_KEY` (Get from [SerpApi](https://serpapi.com/))

## 📦 Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/shakhaout/hotel-booking-agent.git
    cd hotel-booking-agent
    ```

2.  **Create and Activate Virtual Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment**:
    Create a `.env` file in the root directory:
    ```env
    GOOGLE_API_KEY=your_google_api_key
    SERPAPI_KEY=your_serpapi_key
    REDIS_URL=redis://localhost:6379
    ```

## 🏃‍♂️ Usage

### Interactive Chat
To start chatting with the agent:

```bash
./run_interactive.sh
```
*Or manually:*
```bash
python -m src.agent_graph
```

**Commands within chat:**
-   Type your request (e.g., *"Find a cheap hotel in Tokyo for next week"*).
-   Type `quit` or `exit` to close the session.

### Running Components Separately
If you want to debug the MCP server or run scripts individually:

**MCP Server:**
```bash
# Needs PYTHONPATH to check imports if running directly
export PYTHONPATH=$(pwd)
python src/server.py
```

## 🧪 Testing

Run strict tests for specific components:

-   **LLM Connection**: `python test_llm.py`
-   **MCP Bridge**: `python debug_mcp.py`
-   **Verification**: `python verify_graph.py`

## 📂 Project Structure

```
hotel-booking-agent/
├── src/
│   ├── agent_graph.py    # Main Entry Point: LangGraph logic
│   ├── mcp_bridge.py     # Bridges MCP tools to LangChain
│   ├── memory.py         # Redis memory implementation
│   ├── server.py         # FastMCP Server & Tool Definitions
│   └── tools/            # Individual tool implementations
├── scripts/             # Helper scripts
├── run_interactive.sh    # Helper script to run the agent
├── requirements.txt      # Python dependencies
└── README.md             # Documentation
```

## 📜 License

Apache License. See `LICENSE` for more details.
# CVE Intelligence Agent - Streamlit + MCP Architecture

🚀 **Complete refactor with Streamlit interface, MCP (Model Context Protocol) tools, and beautiful Jinja templates**

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Web Interface                   │
│              (Beautiful, Interactive Chat UI)                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      MCP Agent                               │
│        (Natural Language Query Processing)                   │
│  • Rule-based parsing (no LLM required)                     │
│  • LLM integration (OpenAI/Anthropic) - optional            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP Tools Layer                           │
│              (Tool Definitions & Execution)                  │
│  • get_cve_details                                          │
│  • search_cves_by_severity                                  │
│  • search_cves_by_score                                     │
│  • search_cves_by_keyword                                   │
│  • get_cve_statistics                                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Jinja Template Renderer                     │
│           (Beautiful HTML/Markdown Formatting)               │
│  • CVE Detailed View (rich HTML)                            │
│  • CVE Summary View (compact cards)                         │
│  • CVE List View (tables)                                   │
│  • JSON/Markdown formats                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   MongoDB Database                           │
│              (CVE Data Storage)                              │
└─────────────────────────────────────────────────────────────┘
```

## ✨ Key Features

### 🎨 **Beautiful Streamlit Interface**
- Modern gradient design (purple/blue theme)
- Real-time chat interface
- Connection status indicators
- Statistics dashboard with metrics
- Responsive layout

### 🛠️ **MCP Tools Integration**
- Standardized tool definitions for LLM function calling
- 5 core tools for CVE operations
- Clean separation of concerns
- Easy to extend with new tools

### 🤖 **Flexible LLM Integration**
- **Optional LLM**: Works without any LLM (rule-based parsing)
- **OpenAI Support**: Full function calling integration
- **Easy to extend**: Add Anthropic, Ollama, etc.

### 🎯 **Beautiful Jinja Templates**
- Rich HTML formatting with gradients and colors
- Responsive design
- Severity-based color coding
- Interactive elements (hover effects, animations)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Edit .env file
MONGO_URI=mongodb://localhost:27017/
MONGO_DB=cve_database
MONGO_COLLECTION=CVEDetails

# Optional: For LLM features
OPENAI_API_KEY=your_api_key_here
```

### 3. Run Streamlit App

```bash
# Option A: Using script
./run_streamlit.sh

# Option B: Direct command
streamlit run streamlit_app.py
```

Then open: **http://localhost:8501**

## 📁 Project Structure

```
LLM_Agent_Jinja/
├── streamlit_app.py              # 🌟 Main Streamlit interface
├── run_streamlit.sh              # Startup script
│
├── cve_agent_pkg/
│   ├── __init__.py              # Package exports
│   │
│   ├── mcp/                     # 🛠️ MCP Tools Layer
│   │   ├── __init__.py
│   │   ├── tools.py            # MCP tool definitions & execution
│   │   └── agent.py            # MCP agent (orchestrator)
│   │
│   ├── core/                    # Core functionality
│   │   ├── agent.py            # Original CVE agent
│   │   ├── database.py         # MongoDB connector
│   │   └── renderer.py         # Jinja template renderer
│   │
│   ├── templates/              # 🎨 Beautiful Jinja templates
│   │   ├── cve_detailed.jinja  # Rich HTML detailed view
│   │   ├── cve_summary.jinja   # Compact summary view
│   │   ├── cve_list.jinja      # Table list view
│   │   ├── cve_json.jinja      # JSON format
│   │   └── cve_markdown.jinja  # Markdown format
│   │
│   ├── static/                 # Static assets
│   │   ├── css/style.css
│   │   └── js/app.js
│   │
│   └── utils/
│       └── sample_data.py
│
├── run.py                       # Flask app (legacy)
├── requirements.txt
└── README.md
```

## 💻 Usage Examples

### Using Streamlit Interface

1. **Start the app**: `./run_streamlit.sh`
2. **Connect to database**: Click "Connect to Database"
3. **Ask natural language questions**:
   - "Show me CVE-1999-0095"
   - "Find high severity vulnerabilities"
   - "Search for SQL injection CVEs"
   - "Get critical vulnerabilities"

### Using as Python Package

```python
from cve_agent_pkg.mcp import MCPAgent

# Initialize agent
agent = MCPAgent()
agent.connect()

# Process natural language query
result = agent.process_query("Show me CVE-1999-0095")

print(result['rendered_output'])  # Beautiful HTML output
```

### Using MCP Tools Directly

```python
from cve_agent_pkg.mcp import CVEMCPTools

# Initialize tools
tools = CVEMCPTools()
tools.connect()

# Get tool definitions (for LLM)
tool_defs = tools.get_tool_definitions()

# Execute a tool
result = tools.execute_tool("get_cve_details", {
    "cve_id": "CVE-1999-0095",
    "format": "detailed"
})

# Access rendered output
html_output = result['data']['rendered_output']
```

### With OpenAI LLM

```python
from cve_agent_pkg.mcp import MCPAgent
from openai import OpenAI

agent = MCPAgent()
agent.connect()

llm = OpenAI(api_key="your-api-key")

# LLM will automatically call the right tool
result = agent.process_query(
    "What are the most critical vulnerabilities?",
    llm_client=llm
)
```

## 🎨 Template Formats

### 1. **Detailed Format** (HTML)
- Full CVE information with all fields
- Color-coded severity badges
- Circular CVSS score displays
- Visual impact bars for CIA triad
- Expandable sections
- Hover effects and animations

### 2. **Summary Format** (HTML)
- Compact card layout
- Key information only
- Quick overview badge
- Weakness tags

### 3. **List Format** (HTML)
- Table view for multiple CVEs
- Sortable columns
- Severity color coding
- Pagination support

### 4. **JSON Format**
- Structured data output
- Machine-readable
- All CVE fields included

### 5. **Markdown Format**
- Documentation-friendly
- Copy-paste ready
- Clean formatting

## 🛠️ MCP Tools Reference

### 1. `get_cve_details`
Get detailed information about a specific CVE.

**Parameters:**
- `cve_id` (string, required): CVE identifier
- `format` (string, optional): Output format (detailed/summary/json/markdown)

**Example:**
```python
tools.execute_tool("get_cve_details", {
    "cve_id": "CVE-1999-0095",
    "format": "detailed"
})
```

### 2. `search_cves_by_severity`
Search CVEs by severity level.

**Parameters:**
- `severity` (string, required): CRITICAL/HIGH/MEDIUM/LOW
- `limit` (integer, optional): Max results (default: 10)

### 3. `search_cves_by_score`
Search CVEs by CVSS score range.

**Parameters:**
- `min_score` (float, required): Minimum score (0.0-10.0)
- `max_score` (float, required): Maximum score (0.0-10.0)
- `limit` (integer, optional): Max results

### 4. `search_cves_by_keyword`
Search CVEs by keyword in descriptions.

**Parameters:**
- `keyword` (string, required): Search keyword
- `limit` (integer, optional): Max results

### 5. `get_cve_statistics`
Get database statistics.

**Parameters:** None

## 🎯 Streamlit Interface Features

### **Main Dashboard**
- 📊 Real-time statistics (Total CVEs, Critical, High, Medium counts)
- 🟢 Connection status indicator
- 💬 Chat-style conversation interface
- 🎨 Beautiful gradient background

### **Sidebar**
- 🔌 Database connection controls
- 🤖 LLM configuration (optional)
- 🛠️ Available tools viewer
- 🗑️ Clear conversation button

### **Chat Interface**
- Natural language input
- Message history with role indicators
- Tool call badges showing which MCP tool was used
- Beautiful rendered CVE data with Jinja templates
- Example query buttons for quick start

### **Styling**
- Purple/blue gradient theme
- Card-based layout
- Hover animations
- Responsive design
- Custom CSS for professional look

## 🔧 Configuration

### Environment Variables

```bash
# MongoDB Connection
MONGO_URI=mongodb://localhost:27017/
MONGO_DB=cve_database
MONGO_COLLECTION=CVEDetails

# Optional: OpenAI API
OPENAI_API_KEY=sk-...

# Optional: Streamlit Config
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
```

### Streamlit Config (`.streamlit/config.toml`)

```toml
[theme]
primaryColor = "#667eea"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f8f9fa"
textColor = "#2d3748"

[server]
port = 8501
address = "localhost"
```

## 🚀 Deployment

### Local Development
```bash
streamlit run streamlit_app.py
```

### Production (Streamlit Cloud)
1. Push to GitHub
2. Connect to Streamlit Cloud
3. Set environment variables in dashboard
4. Deploy

### Docker
```bash
docker build -t cve-agent .
docker run -p 8501:8501 cve-agent
```

## 🧪 Testing

```bash
# Test MCP tools
python -c "
from cve_agent_pkg.mcp import CVEMCPTools
tools = CVEMCPTools()
tools.connect()
result = tools.execute_tool('get_cve_details', {'cve_id': 'CVE-1999-0095'})
print(result['data']['rendered_output'])
"

# Test MCP agent
python -c "
from cve_agent_pkg.mcp import MCPAgent
agent = MCPAgent()
agent.connect()
result = agent.process_query('Show me CVE-1999-0095')
print(result['rendered_output'])
"
```

## 📚 Documentation

- [Quick Start Guide](QUICKSTART.md)
- [Package Structure](PACKAGE_STRUCTURE.md)
- [MCP Tools Reference](docs/MCP_TOOLS.md)
- [Jinja Templates Guide](docs/TEMPLATES.md)

## 🎉 What's New in v2.0

✅ **Streamlit Interface** - Modern, interactive web UI
✅ **MCP Tools Architecture** - Clean, standardized tool layer
✅ **No LLM Required** - Works with rule-based parsing
✅ **Beautiful Jinja Templates** - Rich HTML with gradients and animations
✅ **Chat Interface** - Conversational UX
✅ **Real-time Stats** - Dashboard with CVE metrics
✅ **Flexible Integration** - Easy to add new LLMs or tools

## 🤝 Integration with Your Codebase

This architecture is designed to match enterprise patterns:

1. **Streamlit Frontend** - Replace Flask with modern chat interface
2. **MCP Tools** - Standardized tools that LLMs can call
3. **Jinja Templates** - Beautiful response formatting
4. **Clean Separation** - Tools, Agent, Renderer are independent

Simply import and use:
```python
from cve_agent_pkg.mcp import MCPAgent

agent = MCPAgent()
result = agent.process_query("your query", your_llm_client)
```

---

**Made with ❤️ for the cybersecurity community**


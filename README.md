# CVE Agent - LLM-Powered Vulnerability Intelligence System

🔒 A modern, intelligent CVE (Common Vulnerabilities and Exposures) query system powered by LLMs, MCP Tools, and Jinja2 templates.

## ✨ Features

- 🤖 **Natural Language Interface**: Ask questions in plain English
- 🛠️ **MCP Tools Integration**: Structured tool calling for precise queries
- 🎨 **Beautiful Jinja2 Templates**: Multi-format CVE rendering (detailed, summary, JSON, markdown)
- 📊 **Interactive Streamlit UI**: Modern, responsive web interface
- 🗄️ **MongoDB Backend**: Efficient CVE data storage and retrieval
- ⚡ **Rule-Based Fallback**: Works without LLM (optional OpenAI integration)

## 🚀 Quick Start

### 1. Setup (First Time Only)
```bash
./setup.sh
```

### 2. Start the Application
```bash
./start_ui.sh
```

Or directly:
```bash
streamlit run app.py
```

### 3. Open Browser
Navigate to: http://localhost:8501

## 📁 Project Structure

Clean, professional package structure:

```
LLM_Agent_Jinja/
├── app.py                      # ✅ Clean entry point
├── cve_agent_pkg/             # Main package
│   ├── core/                  # Core business logic
│   ├── mcp/                   # MCP Tools & Agent
│   ├── templates/             # Jinja2 templates
│   └── ui/                    # Streamlit UI (NEW)
│       ├── streamlit_app.py   # Main UI
│       └── styles.py          # CSS styling
├── setup.sh
├── start_ui.sh
└── requirements.txt
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed structure documentation.

## 💬 Example Queries

- "Show me CVE-1999-0095"
- "Find high severity vulnerabilities"
- "Search for SQL injection CVEs"
- "Get critical vulnerabilities from 2023"
- "List Apache vulnerabilities"

## 🛠️ Technologies

- **Frontend**: Streamlit
- **Backend**: Python 3.12+
- **Database**: MongoDB
- **Templates**: Jinja2
- **LLM**: OpenAI GPT-4 (optional)
- **Architecture**: MCP Tools pattern

## 📖 Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed architecture and structure
- [PACKAGE_STRUCTURE.md](PACKAGE_STRUCTURE.md) - Package organization
- [WEB_UI_GUIDE.md](WEB_UI_GUIDE.md) - UI usage guide
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide

## 🔧 Configuration

Create a `.env` file:
```bash
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=cve_database
OPENAI_API_KEY=your_key_here  # Optional
```

## 📦 Installation

### Prerequisites
- Python 3.12+
- MongoDB 7.0+
- macOS/Linux

### Manual Installation
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start MongoDB
brew services start mongodb-community

# Run application
streamlit run app.py
```

## 🏗️ Architecture Highlights

✅ **Clean Root**: Only essential files at root level  
✅ **Modular UI**: All UI code in `cve_agent_pkg/ui/`  
✅ **Separated Concerns**: Logic, styling, and rendering are separate  
✅ **Professional**: Follows Python package best practices  

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines.

---

Built with ❤️ using Streamlit, MongoDB, and Jinja2

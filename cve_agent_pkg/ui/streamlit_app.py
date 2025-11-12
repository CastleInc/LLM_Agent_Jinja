"""
Streamlit Interface for CVE Agent with MCP Tools
Beautiful, interactive UI for querying CVE data using natural language
"""
import streamlit as st
import os
from cve_agent_pkg.mcp.agent import MCPAgent
from cve_agent_pkg.ui.styles import STREAMLIT_CSS


def init_page_config():
    """Initialize Streamlit page configuration"""
    st.set_page_config(
        page_title="CVE Intelligence Agent",
        page_icon="🔒",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def init_session_state():
    """Initialize session state variables"""
    if 'agent' not in st.session_state:
        st.session_state.agent = MCPAgent()
        st.session_state.connected = False
        st.session_state.conversation = []
        st.session_state.connection_attempted = False

    if 'show_tools' not in st.session_state:
        st.session_state.show_tools = False


def auto_connect():
    """Auto-connect to database on first load"""
    if not st.session_state.connection_attempted:
        with st.spinner("Connecting to database..."):
            st.session_state.connected = st.session_state.agent.connect()
            st.session_state.connection_attempted = True
        if st.session_state.connected:
            st.success("✅ Auto-connected to database successfully!")
        else:
            st.warning("⚠️ Could not connect to database. Please check your MongoDB connection.")


def render_sidebar():
    """Render sidebar with configuration options"""
    with st.sidebar:
        st.markdown("### 🔧 Configuration")

        # Connection status
        if not st.session_state.connected:
            st.markdown('<div class="status-badge status-disconnected">❌ Disconnected</div>',
                       unsafe_allow_html=True)
            if st.button("🔌 Connect to Database", use_container_width=True, key="connect_btn"):
                with st.spinner("Connecting..."):
                    st.session_state.connected = st.session_state.agent.connect()
                    if st.session_state.connected:
                        st.success("✅ Connected successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Connection failed. Check MongoDB is running and .env is configured correctly.")
        else:
            st.markdown('<div class="status-badge status-connected">✅ Connected</div>',
                       unsafe_allow_html=True)
            if st.button("🔌 Disconnect", use_container_width=True, key="disconnect_btn"):
                st.session_state.agent.disconnect()
                st.session_state.connected = False
                st.rerun()

        st.markdown("---")

        # LLM Configuration
        st.markdown("### 🤖 LLM Settings")
        use_llm = st.checkbox("Use LLM (OpenAI)", value=False)

        if use_llm:
            api_key = st.text_input("OpenAI API Key", type="password",
                                   value=os.getenv("OPENAI_API_KEY", ""))
            model = st.selectbox("Model", ["gpt-4", "gpt-3.5-turbo"], index=0)

            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key
        else:
            st.info("Using rule-based processing (no LLM required)")

        st.markdown("---")

        # Available Tools
        if st.button("🛠️ Show Available Tools", use_container_width=True, key="tools_btn"):
            st.session_state.show_tools = not st.session_state.show_tools

        if st.session_state.show_tools:
            tools = st.session_state.agent.get_available_tools()
            st.markdown("#### Available MCP Tools:")
            for tool in tools:
                with st.expander(f"📌 {tool['name']}"):
                    st.markdown(f"**Description:** {tool['description']}")
                    st.json(tool['input_schema'])

        st.markdown("---")

        # Clear conversation
        if st.button("🗑️ Clear Conversation", use_container_width=True, key="clear_btn"):
            st.session_state.conversation = []
            st.rerun()

    return use_llm


def render_header():
    """Render main header"""
    st.markdown('<h1 class="main-header">🔒 CVE Intelligence Agent</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: white; font-size: 1.2rem; margin-bottom: 2rem;">Natural Language Interface to CVE Database using MCP Tools</p>',
               unsafe_allow_html=True)


def render_stats():
    """Render quick statistics dashboard"""
    if st.session_state.connected:
        col1, col2, col3, col4 = st.columns(4)

        try:
            stats_result = st.session_state.agent.tools.execute_tool("get_cve_statistics", {})
            if stats_result["success"]:
                stats = stats_result["data"]

                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{stats['total_cves']}</div>
                        <div class="metric-label">Total CVEs</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color: #eb3349;">{stats['by_severity'].get('CRITICAL', 0)}</div>
                        <div class="metric-label">Critical</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color: #f5576c;">{stats['by_severity'].get('HIGH', 0)}</div>
                        <div class="metric-label">High</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col4:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color: #f093fb;">{stats['by_severity'].get('MEDIUM', 0)}</div>
                        <div class="metric-label">Medium</div>
                    </div>
                    """, unsafe_allow_html=True)
        except:
            pass


def render_chat_message(msg):
    """Render a single chat message"""
    if msg['role'] == 'user':
        st.markdown(f'<div class="user-message">👤 {msg["content"]}</div><div style="clear: both;"></div>',
                   unsafe_allow_html=True)
    elif msg['role'] == 'agent':
        if 'tool_called' in msg:
            st.markdown(f'<div class="agent-message">🤖 <span class="tool-badge">Tool: {msg["tool_called"]}</span></div><div style="clear: both;"></div>',
                       unsafe_allow_html=True)

        # Display rendered output from Jinja templates
        if 'rendered_output' in msg and msg['rendered_output']:
            import streamlit.components.v1 as components
            import os

            # Read the CSS file from templates directory
            template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
            css_path = os.path.join(template_dir, 'styles.css')

            try:
                with open(css_path, 'r') as f:
                    template_css = f.read()
            except:
                template_css = ""

            # Wrap the Jinja-rendered output with CSS and FontAwesome
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
                <style>
                    {template_css}
                </style>
            </head>
            <body>
                {msg['rendered_output']}
            </body>
            </html>
            """

            # Render with proper height
            components.html(full_html, height=800, scrolling=True)

        elif 'response' in msg:
            st.markdown(f'<div class="agent-message">🤖 {msg["response"]}</div><div style="clear: both;"></div>',
                       unsafe_allow_html=True)


def render_chat_interface():
    """Render chat interface"""
    st.markdown("### 💬 Chat with the Agent")

    # Display conversation history
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.conversation:
            render_chat_message(msg)


def process_user_query(user_input, use_llm):
    """Process user query and update conversation"""
    if not st.session_state.connected:
        st.error("⚠️ Please connect to the database first!")
        return

    # Add user message to conversation
    st.session_state.conversation.append({
        'role': 'user',
        'content': user_input
    })

    # Process with agent
    with st.spinner("🤔 Processing your query..."):
        llm_client = None
        if use_llm and 'OPENAI_API_KEY' in os.environ:
            try:
                from openai import OpenAI
                llm_client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
            except:
                st.warning("⚠️ OpenAI client not available, using rule-based processing")

        result = st.session_state.agent.process_query(user_input, llm_client)

        # Add agent response to conversation
        agent_msg = {'role': 'agent'}

        if 'tool_called' in result:
            agent_msg['tool_called'] = result['tool_called']
            agent_msg['tool_arguments'] = result['tool_arguments']

        if 'rendered_output' in result:
            agent_msg['rendered_output'] = result['rendered_output']
        elif 'response' in result:
            agent_msg['response'] = result['response']

        if not result.get('success', True):
            agent_msg['response'] = f"❌ Error: {result.get('error', 'Unknown error')}"

        st.session_state.conversation.append(agent_msg)

    st.rerun()


def render_input_area(use_llm):
    """Render input area"""
    col1, col2 = st.columns([5, 1])

    # Check if there's a pending query from example buttons
    pending_query = st.session_state.get('pending_query', '')

    with col1:
        user_input = st.text_input("Ask me anything about CVEs...",
                                   value=pending_query,
                                   placeholder="e.g., Show me CVE-1999-0095, Find high severity vulnerabilities, Search for SQL injection",
                                   key="user_input",
                                   label_visibility="collapsed")

    with col2:
        send_button = st.button("Send", use_container_width=True, type="primary")

    # Process the query when Send is clicked
    if send_button and user_input:
        # Clear pending query after processing
        if 'pending_query' in st.session_state:
            st.session_state.pending_query = ''
        process_user_query(user_input, use_llm)
    elif send_button and not user_input:
        st.warning("⚠️ Please enter a query first!")


def render_example_queries():
    """Render example query buttons"""
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("### 💡 Example Queries")

    example_col1, example_col2, example_col3 = st.columns(3)

    with example_col1:
        if st.button("🔍 Show me CVE-1999-0095", use_container_width=True, key="example1"):
            st.session_state.pending_query = "Show me CVE-1999-0095"
            st.rerun()

    with example_col2:
        if st.button("⚠️ Find high severity CVEs", use_container_width=True, key="example2"):
            st.session_state.pending_query = "Find high severity vulnerabilities"
            st.rerun()

    with example_col3:
        if st.button("🔎 Search for sendmail CVEs", use_container_width=True, key="example3"):
            st.session_state.pending_query = "Search for sendmail vulnerabilities"
            st.rerun()


def render_footer():
    """Render footer"""
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; color: white; opacity: 0.8; padding: 2rem;">
        <p>🔒 CVE Intelligence Agent • Built with Streamlit, MCP Tools & Jinja Templates</p>
        <p style="font-size: 0.85rem;">Ask natural language questions about CVE vulnerabilities</p>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main application entry point"""
    # Initialize
    init_page_config()
    st.markdown(STREAMLIT_CSS, unsafe_allow_html=True)
    init_session_state()
    auto_connect()

    # Render UI components
    use_llm = render_sidebar()
    render_header()
    render_stats()
    st.markdown("<br>", unsafe_allow_html=True)
    render_chat_interface()
    render_input_area(use_llm)
    render_example_queries()
    render_footer()


if __name__ == "__main__":
    main()

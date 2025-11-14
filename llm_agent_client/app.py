"""
LLM-Powered Streamlit Chat Interface for CVE Agent
Let the LLM decide which MCP tool to call based on natural language
"""
import asyncio
import os
from dataclasses import dataclass
from typing import Optional

import streamlit as st
from mcp_client import MCPClient


@dataclass
class Message:
    actor: str
    payload: str


USER = "user"
ASSISTANT = "ai"
MESSAGES = "messages"


async def run_streamlit_app() -> None:
    st.set_page_config(
        page_title="CVE Agent - AI Assistant",
        page_icon="🤖",
        layout="wide"
    )

    st.title("🤖 CVE Agent - AI Assistant")
    st.markdown("**Ask me anything about CVE vulnerabilities in natural language**")

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        mcp_url = st.text_input("MCP Server URL", value="http://localhost:8001")

        st.divider()

        st.header("💡 Example Queries")
        st.markdown("""
        **Specific CVEs:**
        - Show me CVE-2021-44228
        - What is CVE-2024-000123?
        - Tell me about the Log4j vulnerability
        
        **Search by Severity:**
        - Find critical vulnerabilities
        - Show me high severity CVEs
        - List all critical security issues
        
        **Search by Type:**
        - SQL injection vulnerabilities
        - Remote code execution CVEs
        - Buffer overflow issues
        
        **Search by Exploit Status:**
        - CVEs with functional exploits
        - Vulnerabilities with proof of concept
        
        **Recent & Trending:**
        - Show me the latest CVEs
        - What are the newest vulnerabilities?
        - Recent security issues
        
        **Combined Queries:**
        - Critical SQL injection CVEs
        - Recent remote code execution vulnerabilities
        - High severity authentication bypass issues
        """)

        st.divider()

        if st.button("🗑️ Clear Chat History"):
            st.session_state[MESSAGES] = [
                Message(actor=ASSISTANT, payload="Hello! I'm your CVE database assistant. Ask me anything about CVE vulnerabilities and I'll intelligently search the database for you.")
            ]
            st.rerun()

        st.divider()

        st.markdown("""
        <div style="font-size: 0.8em; color: #666;">
        <strong>How it works:</strong><br>
        🤖 Your query is analyzed by GPT-4<br>
        🎯 AI decides which tool to call<br>
        🔍 Query is executed on MCP server<br>
        📊 Results are formatted for you
        </div>
        """, unsafe_allow_html=True)

    # Initialize message history
    if MESSAGES not in st.session_state:
        st.session_state[MESSAGES] = [
            Message(
                actor=ASSISTANT,
                payload="Hello! I'm your CVE database assistant. Ask me anything about CVE vulnerabilities and I'll intelligently search the database for you."
            )
        ]

    # Initialize MCP client only once
    if "mcp_client" not in st.session_state:
        st.session_state.mcp_client = MCPClient(mcp_server_url=mcp_url)

        # Check connection
        if not st.session_state.mcp_client.check_connection():
            st.error("⚠️ Cannot connect to MCP server. Please start the server first.")
            st.info("Run: `./start_server_background.sh` or `cd mcp_server && python main.py`")
            st.stop()

    # Display message history
    for msg in st.session_state[MESSAGES]:
        with st.chat_message(msg.actor):
            st.markdown(msg.payload, unsafe_allow_html=True)

    # Chat input for user prompt
    prompt: Optional[str] = st.chat_input("Ask about CVE vulnerabilities...")

    if prompt:
        # Store and display user message
        st.session_state[MESSAGES].append(
            Message(actor=USER, payload=prompt)
        )

        with st.chat_message(USER):
            st.write(prompt)

        # Process query with loading indicator
        with st.chat_message(ASSISTANT):
            with st.spinner("🤔 Analyzing your query and searching the database..."):
                # Process query using LLM-powered client
                response: str = await st.session_state.mcp_client.process_query(prompt)

                # Display response
                st.markdown(response, unsafe_allow_html=True)

        # Store assistant response
        st.session_state[MESSAGES].append(
            Message(actor=ASSISTANT, payload=response)
        )


if __name__ == "__main__":
    # Handle Windows event loop policy
    if os.name == "nt" and hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Run the app
    asyncio.run(run_streamlit_app())


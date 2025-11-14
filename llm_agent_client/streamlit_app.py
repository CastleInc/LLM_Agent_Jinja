"""
Streamlit Chat Interface for CVE Agent - AI Assistant
Simple chat interface using MCPClient
"""
import asyncio
import os
from dataclasses import dataclass
from typing import Optional

import streamlit as st
import streamlit.components.v1 as components

from mcp_client import MCPClient


@dataclass
class Message:
    actor: str
    payload: str


USER = "user"
ASSISTANT = "ai"
MESSAGES = "messages"


def is_html(payload: str) -> bool:
    p = payload.lstrip().lower()
    return '<div' in p or '<section' in p or '<html' in p


def strip_indentation(html: str) -> str:
    lines = [ln.lstrip() for ln in html.splitlines()]
    return '\n'.join(lines)


def render_message(actor: str, payload: str):
    with st.chat_message(actor):
        if actor == ASSISTANT and is_html(payload):
            # Separate reasoning (markdown) before first html tag
            trimmed = payload.lstrip()
            first_tag = trimmed.lower().find('<div')
            if first_tag == -1:
                first_tag = trimmed.lower().find('<section')
            if first_tag == -1:
                first_tag = trimmed.lower().find('<html')
            reasoning = trimmed[:first_tag].strip()
            html_part = trimmed[first_tag:]
            if reasoning:
                st.markdown(reasoning, unsafe_allow_html=True)
            clean_html = strip_indentation(html_part)
            est_height = min(max(380, clean_html.count('\n') * 16), 1400)
            components.html(clean_html, height=est_height, scrolling=True)
        else:
            st.markdown(payload.lstrip(), unsafe_allow_html=True)


async def run_streamlit_app() -> None:
    st.set_page_config(page_title="CVE Agent - AI Assistant", page_icon="🤖", layout="wide")
    st.title("🤖 CVE Agent - AI Assistant")
    st.write("Type your query below and press Enter to get CVE information.")

    # Seed queries sidebar
    st.sidebar.header("🔖 Example Queries")
    seed_groups = {
        "Specific CVEs": [
            "Show me CVE-2021-44228",
            "Show me CVE-2020-000001",
            "What is CVE-2024-000123?",
            "Tell me about the Log4j vulnerability"
        ],
        "Search by Severity": [
            "Find critical vulnerabilities",
            "Show me high severity CVEs",
            "List all critical security issues"
        ],
        "Search by Type": [
            "SQL injection vulnerabilities",
            "Remote code execution CVEs",
            "Buffer overflow issues"
        ],
        "Search by Exploit Status": [
            "CVEs with functional exploits",
            "CVEs with proof of concept exploits",
            "Unproven exploit vulnerabilities"
        ],
        "Recency": [
            "Latest vulnerabilities",
            "Recent CVEs",
            "Newly published CVEs"
        ]
    }

    selected_seed: Optional[str] = None
    for group, queries in seed_groups.items():
        with st.sidebar.expander(group, expanded=False):
            for q in queries:
                if st.button(q, key=f"seed_{q}"):
                    selected_seed = q

    # Helper to process any user/seed query
    async def handle_query(query: str, actor: str = USER):
        st.session_state[MESSAGES].append(Message(actor=actor, payload=query))
        render_message(actor, query)
        response: str = await st.session_state.mcp_client.process_query(query)
        st.session_state[MESSAGES].append(Message(actor=ASSISTANT, payload=response))
        render_message(ASSISTANT, response)

    # Initialize session state and client
    if MESSAGES not in st.session_state:
        st.session_state[MESSAGES] = [
            Message(actor=ASSISTANT, payload="Hello! I'm your CVE database assistant. Ask me anything about CVE vulnerabilities and I'll search the database for you.")
        ]
    if "mcp_client" not in st.session_state:
        st.session_state.mcp_client = MCPClient()
        if not st.session_state.mcp_client.check_connection():
            st.error("⚠️ Cannot connect to MCP server at http://localhost:8001")
            st.info("Start server: `cd mcp_server && python main.py`")
            st.stop()

    # Display message history
    for msg in st.session_state[MESSAGES]:
        render_message(msg.actor, msg.payload)

    # Process seed query if selected
    if selected_seed:
        with st.spinner("Processing seed query..."):
            await handle_query(selected_seed)
        # Do not stop; allow the chat input to render below so it remains visible

    prompt: Optional[str] = st.chat_input("Enter your CVE query here...")
    if prompt:
        with st.spinner("Processing..."):
            await handle_query(prompt)


if __name__ == "__main__":
    if os.name == "nt" and hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_streamlit_app())

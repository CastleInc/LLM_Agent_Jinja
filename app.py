#!/usr/bin/env python3
"""
Entry point for CVE Agent Streamlit UI
Run this file to start the Streamlit application
"""
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cve_agent_pkg.ui.streamlit_app import main

if __name__ == "__main__":
    main()


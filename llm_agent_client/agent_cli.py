"""
CLI Interface for CVE Agent using MCP Server
"""
import sys
import asyncio
from mcp_client import MCPClient


def print_banner():
    """Print welcome banner."""
    print("=" * 70)
    print("CVE Agent - Command Line Interface")
    print("Connected to FastAPI MCP Server")
    print("=" * 70)
    print()


def print_help():
    """Print available commands."""
    print("\n📚 Available Commands:")
    print("  get <CVE-ID>              - Get CVE details (e.g., get CVE-2021-44228)")
    print("  severity <LEVEL> [limit]  - Search by severity (CRITICAL/HIGH/MEDIUM/LOW)")
    print("  exploit <MATURITY> [limit]- Search by exploit maturity")
    print("  keyword <TERM> [limit]    - Search by keyword")
    print("  recent [limit]            - List recent CVEs")
    print("  cvss <min> <max> [limit]  - Search by CVSS score range (premium)")
    print("  tools                     - List all available tools")
    print("  help                      - Show this help")
    print("  exit, quit                - Exit the program")
    print()


def format_cve_result(result):
    """Format CVE result for display."""
    if result.get('status') == 'error':
        return f"❌ Error: {result.get('error', 'Unknown error')}"

    tool_result = result.get('result', {})

    if tool_result.get('status') == 'error':
        return f"❌ {tool_result.get('message', 'Tool execution failed')}"

    if tool_result.get('status') == 'success':
        data = tool_result.get('data')
        count = tool_result.get('count')

        if isinstance(data, dict):
            # Single CVE result
            output = ["\n✅ CVE Details:"]
            output.append(f"  CVE ID: {data.get('cve_number') or data.get('cve_no') or data.get('id', 'N/A')}")
            title_val = data.get('cve_title') or data.get('title') or data.get('name')
            output.append(f"  Title: {title_val or 'N/A'}")
            output.append(f"  Severity: {data.get('severity', data.get('exploit_code_maturity', 'N/A'))}")
            output.append(f"  CVSS Score: {data.get('cvss_score', data.get('score', 'N/A'))}")
            output.append(f"  Exploit Maturity: {data.get('exploit_code_maturity', 'N/A')}")

            if data.get('description'):
                desc_raw = data.get('description', '')
                desc = desc_raw[:200] + ("..." if len(desc_raw) > 200 else "")
                output.append(f"  Description: {desc}")

            return "\n".join(output)

        elif isinstance(data, list):
            # Multiple CVE results
            output = [f"\n✅ Found {count} CVE(s):\n"]
            for i, cve in enumerate(data, 1):
                cve_id = cve.get('cve_number') or cve.get('cve_no') or 'N/A'
                title_val = cve.get('cve_title') or cve.get('title') or cve.get('name') or ''
                output.append(f"{i}. {cve_id}")
                output.append(f"   Title: {title_val[:60]}{'...' if len(title_val) > 60 else ''}")
                output.append(f"   Severity: {cve.get('severity', cve.get('exploit_code_maturity', 'N/A'))} | CVSS: {cve.get('cvss_score', cve.get('score', 'N/A'))}")
                output.append("")

            return "\n".join(output)

    return str(result)


def main():
    """Main CLI loop."""
    print_banner()

    # Initialize client
    print("🔄 Initializing MCP client...")
    client = MCPClient()

    if not client.setup_agent():
        print("\n❌ Failed to connect to MCP server.")
        print("Make sure the server is running:")
        print("  ./start_mcp_server_production.sh")
        sys.exit(1)

    print("\n✅ Agent ready! Type 'help' for available commands.")
    print_help()

    # Main loop
    try:
        while True:
            try:
                user_input = input("You> ").strip()

                if not user_input:
                    continue

                # Parse command
                parts = user_input.split()
                command = parts[0].lower()
                args = parts[1:] if len(parts) > 1 else []

                # Handle commands
                if command in ['exit', 'quit']:
                    print("\n👋 Goodbye!")
                    break

                elif command == 'help':
                    print_help()

                elif command == 'tools':
                    print("\n📋 Available Tools:")
                    for i, tool in enumerate(client.list_tools(), 1):
                        print(f"\n{i}. {tool['name']}")
                        print(f"   {tool['description']}")
                        print(f"   Profiles: {', '.join(tool.get('product_profiles', []))}")
                    print()

                elif command == 'get' and args:
                    cve_id = args[0]
                    result = client.call_tool("get_cve_details", {"cve_id": cve_id})
                    print(format_cve_result(result))

                elif command == 'severity' and args:
                    severity = args[0].upper()
                    limit = int(args[1]) if len(args) > 1 else 5
                    result = client.call_tool("search_cves_by_severity", {
                        "severity": severity,
                        "limit": limit
                    })
                    print(format_cve_result(result))

                elif command == 'exploit' and args:
                    maturity = " ".join(args[:-1]) if len(args) > 1 and args[-1].isdigit() else " ".join(args)
                    limit = int(args[-1]) if args[-1].isdigit() else 5
                    result = client.call_tool("search_cves_by_exploit_maturity", {
                        "maturity": maturity,
                        "limit": limit
                    })
                    print(format_cve_result(result))

                elif command == 'keyword' and args:
                    keyword = " ".join(args[:-1]) if len(args) > 1 and args[-1].isdigit() else " ".join(args)
                    limit = int(args[-1]) if args[-1].isdigit() else 5
                    result = client.call_tool("search_cves_by_keyword", {
                        "keyword": keyword,
                        "limit": limit
                    })
                    print(format_cve_result(result))

                elif command == 'recent':
                    limit = int(args[0]) if args and args[0].isdigit() else 5
                    result = client.call_tool("list_recent_cves", {"limit": limit})
                    print(format_cve_result(result))

                elif command == 'cvss' and len(args) >= 2:
                    min_score = float(args[0])
                    max_score = float(args[1])
                    limit = int(args[2]) if len(args) > 2 else 5
                    result = client.call_tool("search_cves_by_cvss_score", {
                        "min_score": min_score,
                        "max_score": max_score,
                        "limit": limit
                    }, product_profile="premium")
                    print(format_cve_result(result))

                else:
                    print("❌ Unknown command. Type 'help' for available commands.")

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Type 'help' for usage information.\n")

    finally:
        client.disconnect()


if __name__ == "__main__":
    main()

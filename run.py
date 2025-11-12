"""
Run the CVE Agent Web Application
"""
from cve_agent_pkg.app import create_app

if __name__ == '__main__':
    app = create_app()

    print("=" * 70)
    print("🌐 CVE Agent - Vulnerability Intelligence System")
    print("=" * 70)
    print()
    print("🚀 Starting Flask server...")
    print("📱 Open your browser to: http://localhost:5001")
    print("🛑 Press Ctrl+C to stop the server")
    print()
    print("=" * 70)

    app.run(debug=True, host='0.0.0.0', port=5001)


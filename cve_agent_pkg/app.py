"""
Flask Web Application for CVE Agent (Legacy - use Streamlit instead)
"""
from flask import Flask, render_template, request, jsonify
from cve_agent_pkg.core.agent import CVEAgent
from datetime import datetime
import os


def create_app():
    """Application factory"""
    package_dir = os.path.dirname(__file__)

    app = Flask(__name__,
                template_folder=os.path.join(package_dir, 'templates'),
                static_folder=os.path.join(package_dir, 'static'))

    agent = CVEAgent()

    # Connect on startup
    if agent.connect():
        print("✅ Connected to MongoDB")
    else:
        print("⚠️ MongoDB connection failed")

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/api/status')
    def status():
        return jsonify({'connected': agent.connected, 'timestamp': datetime.now().isoformat()})

    @app.route('/api/cve/<cve_id>')
    def get_cve(cve_id):
        if not agent.connected:
            return jsonify({'error': 'Not connected'}), 500

        format_type = request.args.get('format', 'detailed')
        result = agent.get_cve_details(cve_id, format_type)
        return result

    @app.route('/api/search/severity')
    def search_severity():
        if not agent.connected:
            return jsonify({'error': 'Not connected'}), 500

        severity = request.args.get('severity', 'HIGH')
        limit = int(request.args.get('limit', 10))
        return agent.search_cves_by_severity(severity, limit)

    @app.route('/api/functions')
    def get_functions():
        return jsonify(agent.get_function_definitions())

    return app


if __name__ == '__main__':
    app = create_app()

    print("=" * 70)
    print("🌐 CVE Agent Web UI")
    print("=" * 70)
    print()
    print("🚀 Starting Flask server...")
    print("📱 Open your browser to: http://localhost:5001")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 70)

    app.run(debug=True, host='0.0.0.0', port=5001)

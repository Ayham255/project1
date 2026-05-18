from flask import Flask, jsonify
from app import config

app = Flask(__name__)

# Very simple state representation for the dashboard
system_state = {
    "status": "running",
    "cameras_active": 0,
    "last_spoken_message": "None"
}

@app.route("/")
def index():
    html = f"""
    <html>
        <head>
            <title>Vision + Voice AI Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f9; color: #333; }}
                h1 {{ color: #2c3e50; }}
                .status-box {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                p {{ font-size: 1.2em; }}
                .value {{ font-weight: bold; color: #2980b9; }}
            </style>
        </head>
        <body>
            <h1>Vision + Voice AI Assistant Status</h1>
            <div class="status-box">
                <p>System Status: <span class="value">{system_state['status']}</span></p>
                <p>Cameras Active: <span class="value">{system_state['cameras_active']}</span></p>
                <p>Last Spoken Message: <span class="value">{system_state['last_spoken_message']}</span></p>
                <p>Configured Web Port: <span class="value">{config.WEB_PORT}</span></p>
            </div>
            <script>
                // Auto-refresh the page every 5 seconds to get updates
                setTimeout(function(){{
                   window.location.reload(1);
                }}, 5000);
            </script>
        </body>
    </html>
    """
    return html

@app.route("/api/status")
def status():
    return jsonify(system_state)

def run_server():
    app.run(host="0.0.0.0", port=config.WEB_PORT, debug=False, use_reloader=False)

if __name__ == "__main__":
    run_server()

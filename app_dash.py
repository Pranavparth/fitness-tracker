import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from flask import request, jsonify
import database as db
import logging
from datetime import datetime

# Configure logging for webhook
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Dash app with Pages support and a Bootstrap theme
# We add meta tags to make it look like a native iOS app when added to the home screen
app = dash.Dash(
    __name__, 
    use_pages=True, 
    external_stylesheets=[
        dbc.themes.DARKLY,
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap",
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css"
    ],
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0, viewport-fit=cover"},
        {"name": "apple-mobile-web-app-capable", "content": "yes"},
        {"name": "apple-mobile-web-app-status-bar-style", "content": "black-translucent"},
        {"name": "apple-mobile-web-app-title", "content": "Fitness"}
    ]
)

app.title = "Fitness Tracker"
server = app.server # Expose Flask server for Render deployment and Webhook

# --- WEBHOOK API FOR IOS SHORTCUTS ---
@server.route('/api/apple-health-sync', methods=['POST'])
def apple_health_sync():
    """
    Endpoint for iOS Shortcuts to post daily Apple Watch data.
    Expected JSON:
    {
        "date": "YYYY-MM-DD",
        "steps": 10000,
        "active_calories": 500,
        "exercise_minutes": 45,
        "avg_heart_rate": 65
    }
    """
    try:
        data = request.json
        logger.info(f"Received Apple Health Sync Payload: {data}")
        
        # Validate required fields
        required = ['date', 'steps', 'active_calories', 'exercise_minutes']
        if not all(k in data for k in required):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400
            
        date_str = data['date']
        
        # Insert into Supabase
        db.upsert_apple_watch_data(
            date=date_str,
            steps=int(data['steps']),
            active_calories=int(data['active_calories']),
            exercise_minutes=int(data['exercise_minutes']),
            avg_heart_rate=float(data.get('avg_heart_rate', 0.0))
        )
        
        return jsonify({"status": "success", "message": f"Successfully synced data for {date_str}"}), 200
        
    except Exception as e:
        logger.error(f"Webhook Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- MOBILE NAVIGATION ---
def create_bottom_nav():
    return html.Div(
        [
            dcc.Link(
                [html.I(className="bi bi-graph-up"), "Dashboard"],
                href="/",
                className="nav-link",
                id="nav-dashboard"
            ),
            dcc.Link(
                [html.I(className="bi bi-journal-text"), "Journal"],
                href="/logs",
                className="nav-link",
                id="nav-logs"
            )
        ],
        className="bottom-nav"
    )

# Define the main application layout
app.layout = html.Div(
    [
        dcc.Location(id='url', refresh=False),
        html.Div(
            [
                dash.page_container
            ],
            className="content"
        ),
        create_bottom_nav()
    ]
)

# Active state logic for bottom nav
@app.callback(
    [Output("nav-dashboard", "className"), Output("nav-logs", "className")],
    [Input("url", "pathname")]
)
def update_active_links(pathname):
    if pathname == "/logs":
        return "nav-link", "nav-link active"
    return "nav-link active", "nav-link"

if __name__ == "__main__":
    app.run(debug=True, port=8050, host='0.0.0.0')

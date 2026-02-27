import dash
from dash import dcc, html, Input, Output, State, ALL, ctx
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
            ),
            # Add a button for Settings instead of a link
            html.Div(
                [html.I(className="bi bi-gear"), "Settings"],
                className="nav-link",
                id="open-settings-modal",
                n_clicks=0,
                style={"cursor": "pointer"}
            ),
        ],
        className="bottom-nav"
    )

# --- SETTINGS MODAL ---
settings_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("User Settings")),
        dbc.ModalBody(
            [
                html.Label("Height (cm)"),
                dbc.Input(id="settings-height", type="number", className="mb-3"),
                
                html.Label("Maintenance Calories (Daily Goal)"),
                dbc.Input(id="settings-calories", type="number", className="mb-3"),
                
                html.Div(id="settings-msg", className="text-success mt-2", style={"display": "none"})
            ]
        ),
        dbc.ModalFooter(
            [
                dbc.Button("Close", id="close-settings-modal", className="ms-auto", n_clicks=0),
                dbc.Button("Save Changes", id="save-settings-btn", color="primary", n_clicks=0),
            ]
        ),
    ],
    id="modal",
    is_open=False,
    centered=True,
)

# Define the main application layout
app.layout = html.Div(
    [
        dcc.Location(id='url', refresh=False),
        settings_modal,
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

# Settings Modal Logic
@app.callback(
    Output("modal", "is_open"),
    Output("settings-height", "value"),
    Output("settings-calories", "value"),
    Output("settings-msg", "children"),
    Output("settings-msg", "style"),
    Input("open-settings-modal", "n_clicks"),
    Input("close-settings-modal", "n_clicks"),
    Input("save-settings-btn", "n_clicks"),
    State("modal", "is_open"),
    State("settings-height", "value"),
    State("settings-calories", "value")
)
def toggle_modal(n1, n2, n_save, is_open, height, calories):
    triggered_id = ctx.triggered_id
    
    # 1. Open the modal and load settings from DB
    if triggered_id == "open-settings-modal":
        user = db.get_user_settings()
        return True, user.get('height_cm'), user.get('maintenance_calories'), "", {"display": "none"}
        
    # 2. Save new settings to DB
    elif triggered_id == "save-settings-btn":
        if height and calories:
            db.update_user_settings(height_cm=float(height), maintenance_calories=int(calories))
            return True, height, calories, "Settings saved successfully! Refresh page to see changes.", {"display": "block", "color": "#4ECDC4"}
            
    # 3. Close modal
    elif triggered_id == "close-settings-modal":
        return False, dash.no_update, dash.no_update, "", {"display": "none"}
        
    return is_open, dash.no_update, dash.no_update, dash.no_update, dash.no_update

if __name__ == "__main__":
    app.run(debug=True, port=8050, host='0.0.0.0')

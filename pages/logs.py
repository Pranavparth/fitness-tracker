import dash
from dash import dcc, html, callback, Input, Output, State, ALL, ctx
import dash_bootstrap_components as dbc
from datetime import date
from database import log_daily_weight, log_food, save_workout, upsert_apple_watch_data
from utils import search_food_openfoodfacts, scale_nutrients
import json

dash.register_page(__name__, path='/logs', name="Log Data")

# Component definitions - Styled for Mobile
weight_card = dbc.Card(
    dbc.CardBody([
        html.H5([html.I(className="bi bi-scale pe-2"), "Daily Weight"], className="card-title premium-title mb-4", style={"textAlign": "left"}),
        dbc.Input(id="weight-date", type="date", value=date.today().isoformat(), className="mb-3"),
        dbc.InputGroup(
            [
                dbc.Input(id="weight-input", type="number", placeholder="Enter weight", step=0.1),
                dbc.InputGroupText("kg", style={"backgroundColor": "#2D313A", "border": "none", "color": "#A0AABF"})
            ],
            className="mb-4"
        ),
        dbc.Button("Save Weight", id="btn-save-weight", color="primary", className="w-100 btn-primary", n_clicks=0),
        html.Div(id="weight-msg", className="mt-3 text-center fw-bold")
    ]),
    className="mb-4 metric-card"
)

food_card = dbc.Card(
    dbc.CardBody([
        html.H5([html.I(className="bi bi-egg-fried pe-2"), "Log Food"], className="card-title premium-title mb-4", style={"textAlign": "left"}),
        dbc.Input(id="food-date", type="date", value=date.today().isoformat(), className="mb-3"),
        dbc.Select(id="food-meal", options=[
            {"label": "Breakfast", "value": "Breakfast"},
            {"label": "Lunch", "value": "Lunch"},
            {"label": "Dinner", "value": "Dinner"},
            {"label": "Snack", "value": "Snack"},
        ], value="Breakfast", className="mb-3"),
        
        dbc.InputGroup([
            dbc.Input(id="food-search", placeholder="Search food database...", type="text"),
            dbc.Button(html.I(className="bi bi-search"), id="btn-search-food", color="secondary", n_clicks=0),
        ], className="mb-3"),
        
        html.Div(id="food-search-results", className="mb-3"),
        dcc.Store(id="selected-food-store"),
        
        dbc.InputGroup(
            [
                dbc.Input(id="food-portion", type="number", placeholder="Portion size", value=100, step=10),
                dbc.InputGroupText("g", style={"backgroundColor": "#2D313A", "border": "none", "color": "#A0AABF"})
            ],
            className="mb-4"
        ),
        dbc.Button("Log Food", id="btn-log-food", color="primary", className="w-100 btn-primary", n_clicks=0),
        html.Div(id="food-msg", className="mt-3 text-center fw-bold")
    ]),
    className="mb-4 metric-card"
)

journal_card = dbc.Card(
    dbc.CardBody([
        html.H5([html.I(className="bi bi-journal-richtext pe-2"), "Daily Journal"], className="card-title premium-title mb-4", style={"textAlign": "left"}),
        dbc.Input(id="workout-date", type="date", value=date.today().isoformat(), className="mb-3"),
        dbc.InputGroup(
            [
                dbc.Input(id="workout-duration", type="number", placeholder="Workout Duration"),
                dbc.InputGroupText("mins", style={"backgroundColor": "#2D313A", "border": "none", "color": "#A0AABF"})
            ],
            className="mb-3"
        ),
        dbc.Textarea(id="workout-notes", placeholder="How are you feeling today? Any workout notes?", style={"minHeight": "120px"}, className="mb-4"),
        dbc.Button("Save Journal Entry", id="btn-save-workout", color="primary", className="w-100 btn-primary", n_clicks=0),
        html.Div(id="workout-msg", className="mt-3 text-center fw-bold")
    ]),
    className="mb-5 metric-card" # mb-5 to prevent cutoff from bottom nav
)

def layout():
    return html.Div([
        html.H3("Journal", className="mb-4 premium-title", style={"textAlign": "left"}),
        dbc.Row([
            dbc.Col(weight_card, width=12, md=6),
            dbc.Col(food_card, width=12, md=6),
        ]),
        dbc.Row([
            dbc.Col(journal_card, width=12),
        ])
    ])

# ---------------- CALLBACKS ----------------

@callback(
    Output("weight-msg", "children"),
    Output("weight-msg", "className"),
    Input("btn-save-weight", "n_clicks"),
    State("weight-date", "value"),
    State("weight-input", "value"),
    prevent_initial_call=True
)
def save_weight_cb(n_clicks, date_val, weight_val):
    if not weight_val:
        return "Please enter a weight.", "mt-3 text-center fw-bold text-danger"
    try:
        log_daily_weight(date_val, weight_val)
        return f"Logged {weight_val}kg for {date_val}!", "mt-3 text-center fw-bold text-success"
    except Exception as e:
         return f"Error: {e}", "mt-3 text-center fw-bold text-danger"

@callback(
    Output("food-search-results", "children"),
    Output("selected-food-store", "data"),
    Input("btn-search-food", "n_clicks"),
    State("food-search", "value"),
    prevent_initial_call=True
)
def search_food_cb(n_clicks, query):
    if not query:
        return html.Div("Please enter a search term.", className="text-danger"), None
    
    results = search_food_openfoodfacts(query)
    if not results:
        return html.Div("No results found.", className="text-warning"), None
    
    # Auto-select the first result for simplicity in this MVP
    best_match = results[0]
    result_text = f"Selected: {best_match['name']} ({best_match['calories_100g']} kcal/100g)"
    return html.Div([html.I(className="bi bi-check-circle-fill text-success pe-2"), result_text], className="text-info"), best_match

@callback(
    Output("food-msg", "children"),
    Output("food-msg", "className"),
    Input("btn-log-food", "n_clicks"),
    State("food-date", "value"),
    State("food-meal", "value"),
    State("food-portion", "value"),
    State("selected-food-store", "data"),
    prevent_initial_call=True
)
def log_food_cb(n_clicks, date_val, meal_val, portion_val, food_data):
    if not food_data:
        return "Please search and select a food first.", "mt-3 text-center fw-bold text-danger"
    if not portion_val:
        return "Please enter a portion size.", "mt-3 text-center fw-bold text-danger"
        
    scaled = scale_nutrients(food_data, portion_val)
    try:
        log_food(
            date_val, meal_val, scaled['name'], f"{portion_val}g",
            scaled['calories'], scaled['protein_g'], scaled['carbs_g'], scaled['fats_g']
        )
        return f"Logged {scaled['name']} ({scaled['calories']:.0f} kcal)!", "mt-3 text-center fw-bold text-success"
    except Exception as e:
        return f"Error: {e}", "mt-3 text-center fw-bold text-danger"

@callback(
    Output("workout-msg", "children"),
    Output("workout-msg", "className"),
    Input("btn-save-workout", "n_clicks"),
    State("workout-date", "value"),
    State("workout-duration", "value"),
    State("workout-notes", "value"),
    prevent_initial_call=True
)
def save_workout_cb(n_clicks, date_val, duration_val, notes_val):
    if not notes_val and not duration_val:
        return "Please enter notes or a workout duration.", "mt-3 text-center fw-bold text-warning"
    
    # We simplified the workout logging for the mobile MVP to just notes and duration
    try:
        save_workout(date_val, duration_val or 0, notes_val or "", [])
        return "Journal entry saved!", "mt-3 text-center fw-bold text-success"
    except Exception as e:
        return f"Error: {e}", "mt-3 text-center fw-bold text-danger"

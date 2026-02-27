import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from database import get_daily_logs_df, get_daily_calories_df, get_apple_watch_df, get_user_settings

dash.register_page(__name__, path='/', name="Dashboard")

def layout():
    daily_df = get_daily_logs_df()
    food_df = get_daily_calories_df()
    apple_df = get_apple_watch_df()
    user = get_user_settings()

    if daily_df.empty and food_df.empty and apple_df.empty:
        return html.Div(
            [
                html.H3("Welcome to FitnessTracker!", className="text-center mt-5 mb-3"),
                html.P("Your database is connected but empty. Tap Journal below to log your first weight entry, or sync your Apple Watch data.", className="text-center text-muted"),
            ],
            className="p-4"
        )

    # Helper to merge everything on 'date'
    master_df = daily_df.copy() if not daily_df.empty else pd.DataFrame(columns=['date', 'weight_kg', 'bmi'])

    if not food_df.empty:
        if master_df.empty:
            master_df = food_df
        else:
            master_df = pd.merge(master_df, food_df, on='date', how='outer')

    if not apple_df.empty:
        if master_df.empty:
            master_df = apple_df
        else:
            master_df = pd.merge(master_df, apple_df, on='date', how='outer')

    master_df['date'] = pd.to_datetime(master_df['date'])
    master_df = master_df.sort_values('date')

    maint_cals = user.get('maintenance_calories', 2500)

    # ----------------- TOP METRICS ROW -----------------
    latest_weight = master_df['weight_kg'].dropna().iloc[-1] if 'weight_kg' in master_df.columns and not master_df['weight_kg'].dropna().empty else "N/A"
    latest_bmi = master_df['bmi'].dropna().iloc[-1] if 'bmi' in master_df.columns and not master_df['bmi'].dropna().empty else "N/A"
    latest_cals = master_df['consumed'].dropna().iloc[-1] if 'consumed' in master_df.columns and not master_df['consumed'].dropna().empty else "N/A"
    
    # Safely calculate deficit
    latest_deficit = "N/A"
    if latest_cals != "N/A":
        try:
           latest_deficit = maint_cals - float(latest_cals)
        except (ValueError, TypeError):
           latest_deficit = "N/A"

    def make_card(title, value, sub="", positive=None):
        sub_class = "metric-sub"
        if positive is True:
            sub_class += " metric-positive"
        elif positive is False:
            sub_class += " metric-negative"
        
        return html.Div(
            [
                html.Div(title, className="metric-title"),
                html.Div(str(value), className="metric-value"),
                html.Div(sub, className=sub_class)
            ],
            className="metric-card"
        )

    # Mobile optimized cards (2x2 grid instead of 4x1)
    cards = dbc.Row(
        [
            dbc.Col(make_card("Weight", f"{latest_weight} kg" if latest_weight != "N/A" else "--"), width=6, className="mb-3"),
            dbc.Col(make_card("BMI", f"{latest_bmi:.1f}" if latest_bmi != "N/A" else "--"), width=6, className="mb-3"),
            dbc.Col(make_card("Intake", f"{latest_cals:.0f}" if latest_cals != "N/A" else "--", sub="kcal today"), width=6),
            dbc.Col(make_card(
                "Deficit", 
                f"{latest_deficit:.0f}" if latest_deficit != "N/A" else "--",
                sub="kcal target",
                positive=True if (latest_deficit != "N/A" and float(latest_deficit) > 0) else False if latest_deficit != "N/A" else None
            ), width=6),
        ],
        className="mb-4 gx-3" # gx-3 reduces gutter width on mobile
    )

    # ----------------- CHARTS (Mobile Optimized) -----------------
    
    # Trend line styling
    chart_margins = dict(l=0, r=0, t=20, b=0)
    bg_color = "rgba(0,0,0,0)"

    # 1. Weight Progress (Line Chart)
    if 'weight_kg' in master_df.columns and not master_df['weight_kg'].dropna().empty:
        w_df = master_df.dropna(subset=['weight_kg'])
        fig1 = px.line(w_df, x='date', y='weight_kg', template="plotly_dark")
        fig1.update_traces(line_color='#4ECDC4', line_width=3, mode='lines+markers', marker=dict(size=6, color='#FF6B6B'))
        fig1.update_layout(
            margin=chart_margins, paper_bgcolor=bg_color, plot_bgcolor=bg_color,
            xaxis=dict(showgrid=False, title="", tickformat="%b %d"),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title=""),
            height=250 # Smaller height for mobile
        )
        chart1 = dcc.Graph(figure=fig1, config={'displayModeBar': False})
    else:
        chart1 = html.Div("No weight logs yet.", className="text-muted p-3 text-center")

    # 2. Calories
    if 'consumed' in master_df.columns and not master_df['consumed'].dropna().empty:
        c_df = master_df.dropna(subset=['consumed'])
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=c_df['date'], y=c_df['consumed'], name="Consumed", marker_color='rgba(255, 107, 107, 0.8)', marker_line_color='#FF6B6B', marker_line_width=1.5))
        fig2.add_hline(y=maint_cals, line_dash="dash", line_color="#4ECDC4", annotation_text="Goal")
        fig2.update_layout(
            template="plotly_dark", margin=chart_margins, barmode='group', paper_bgcolor=bg_color, plot_bgcolor=bg_color,
            xaxis=dict(showgrid=False, title="", tickformat="%b %d"),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title=""),
            height=200, showlegend=False
        )
        chart2 = dcc.Graph(figure=fig2, config={'displayModeBar': False})
    else:
        chart2 = html.Div("No food logged yet.", className="text-muted p-3 text-center")
        
    # 3. Apple Watch Activity (Steps / Active Cals)
    if 'steps' in master_df.columns and not master_df['steps'].dropna().empty:
        a_df = master_df.dropna(subset=['steps'])
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=a_df['date'], y=a_df['steps'], name="Steps", marker_color='#4ECDC4'))
        fig3.update_layout(
            template="plotly_dark", margin=chart_margins, paper_bgcolor=bg_color, plot_bgcolor=bg_color,
            xaxis=dict(showgrid=False, title="", tickformat="%b %d"),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title=""),
            height=200, showlegend=False
        )
        chart3 = dcc.Graph(figure=fig3, config={'displayModeBar': False})
    else:
        chart3 = html.Div("Sync Apple Watch data via iOS Shortcuts.", className="text-muted p-3 text-center")

    return html.Div([
        html.H3("Overview", className="mb-4 premium-title", style={"textAlign": "left"}),
        cards,
        
        # Stack charts vertically to fit phone screens better instead of side-by-side
        html.Div([
            html.Div("Weight Progress", className="metric-title mb-2"), 
            chart1
        ], className="graph-container"),
        
        html.Div([
            html.Div("Calorie Intake", className="metric-title mb-2"), 
            chart2
        ], className="graph-container"),
        
        html.Div([
             html.Div("Daily Steps", className="metric-title mb-2"), 
             chart3
        ], className="graph-container mb-5") # Extra mb-5 so bottom nav doesn't cover it
    ])

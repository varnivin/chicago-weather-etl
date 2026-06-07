# =============================================================================
# dashboard_v3.py
# Chicago Weather Intelligence Dashboard
# Developer: Nivin Varghese | MSBA 2026
# Run: python dashboard_v3.py
# Open: http://127.0.0.1:8050
# =============================================================================

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
from sqlalchemy import create_engine, text
import warnings
warnings.filterwarnings("ignore")

# =============================================================================
# SECTION 1 — LOAD DATA
# =============================================================================

SUPABASE_URL = "postgresql://postgres.mimtgltdqiequdyptkey:Chicagodatabase2026@aws-1-us-east-2.pooler.supabase.com:5432/postgres"

def load_data():
    try:
        engine = create_engine(SUPABASE_URL)
        with engine.connect() as conn:
            df = pd.read_sql(text("SELECT * FROM weather_data ORDER BY forecast_date"), conn)
        print("Connected to Supabase PostgreSQL")
    except Exception:
        engine = create_engine("sqlite:///chicago_weather.db")
        with engine.connect() as conn:
            df = pd.read_sql(text("SELECT * FROM weather_data ORDER BY forecast_date"), conn)
        print("Connected to SQLite fallback")
    df["forecast_date"] = pd.to_datetime(df["forecast_date"])
    return df

df = load_data()
today = pd.Timestamp.today().normalize()
date_range_str = df["forecast_date"].min().strftime("%b %d") + " — " + df["forecast_date"].max().strftime("%b %d, %Y")

# =============================================================================
# SECTION 2 — INSIGHT LOGIC
# =============================================================================

def get_traffic_insights(data):
    high_risk = data[data["precipitation_probability"] >= 50]
    best_days = data[(data["precipitation_probability"] < 20) & (data["temperature_max"] < 90)]
    wet_roads = data[data["precipitation_total"] > 0.1]
    insights = []
    if len(high_risk) > 0:
        days = ", ".join(high_risk["forecast_date"].dt.strftime("%b %d").tolist()[:3])
        insights.append(("High traffic risk days", days, "#FF7043"))
    if len(best_days) > 0:
        days = ", ".join(best_days["forecast_date"].dt.strftime("%b %d").tolist()[:3])
        insights.append(("Best commute days", days, "#0F6E56"))
    if len(wet_roads) > 0:
        days = ", ".join(wet_roads["forecast_date"].dt.strftime("%b %d").tolist()[:3])
        insights.append(("Wet roads — allow extra time", days, "#185FA5"))
    heat = data[data["temperature_max"] > 88]
    if len(heat) > 0:
        insights.append(("Heat advisory days", str(len(heat)) + " days — check tire pressure", "#BA7517"))
    return insights

def get_agriculture_insights(data):
    frost = data[data["temperature_min"] < 32]
    no_irrigation = data[data["precipitation_total"] > 0.5]
    optimal = data[(data["temperature_max"] >= 50) & (data["temperature_max"] <= 85) & (data["precipitation_probability"] < 40)]
    insights = []
    if len(frost) > 0:
        days = ", ".join(frost["forecast_date"].dt.strftime("%b %d").tolist())
        insights.append(("Frost risk — protect crops", days, "#7B5EA7"))
    else:
        insights.append(("No frost risk detected", "All temps above 32F this period", "#0F6E56"))
    total_rain = round(data["precipitation_total"].sum(), 2)
    if total_rain > 1.0:
        insights.append(("Good rainfall this period", str(total_rain) + " inches total — irrigation may not be needed", "#185FA5"))
    else:
        insights.append(("Low rainfall — irrigation recommended", str(total_rain) + " inches total this period", "#FF7043"))
    if len(optimal) > 0:
        days = ", ".join(optimal["forecast_date"].dt.strftime("%b %d").tolist()[:4])
        insights.append(("Optimal planting window", days, "#0F6E56"))
    return insights

def get_tourism_insights(data):
    def outdoor_score(row):
        score = 100
        score -= row["precipitation_probability"] * 0.6
        if row["temperature_max"] < 45:
            score -= 30
        elif row["temperature_max"] > 92:
            score -= 20
        elif row["temperature_max"] >= 65 and row["temperature_max"] <= 85:
            score += 10
        return max(0, min(100, round(score)))
    data = data.copy()
    data["outdoor_score"] = data.apply(outdoor_score, axis=1)
    perfect = data[data["outdoor_score"] >= 80].sort_values("outdoor_score", ascending=False)
    avoid = data[data["outdoor_score"] < 40]
    insights = []
    if len(perfect) > 0:
        days = ", ".join(perfect["forecast_date"].dt.strftime("%b %d").tolist()[:3])
        insights.append(("Best days — Downtown & Navy Pier", days + " (score 80+)", "#185FA5"))
        insights.append(("Millennium Park & Bean", days + " — ideal outdoor conditions", "#0F6E56"))
        insights.append(("O'Hare & Midway airports", "Low weather delays expected on best days", "#0F6E56"))
    if len(avoid) > 0:
        days = ", ".join(avoid["forecast_date"].dt.strftime("%b %d").tolist()[:2])
        insights.append(("Avoid outdoor visits", days + " — indoor activities recommended", "#FF7043"))
    streak = 0
    max_streak = 0
    for score in data["outdoor_score"]:
        if score >= 70:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    if max_streak > 0:
        insights.append(("Longest good weather streak", str(max_streak) + " consecutive days with score 70+", "#BA7517"))
    return insights

# =============================================================================
# SECTION 3 — APP SETUP
# =============================================================================

app = Dash(__name__)
app.title = "Chicago Weather Intelligence"

SKY_TOP    = "#4FC3F7"
SKY_MID    = "#87CEEB"
SKY_LIGHT  = "#E1F5FE"
SUN        = "#FFD54F"
WHITE      = "#FFFFFF"
CARD_BG    = "#FFFFFF"
PAGE_BG    = "#F0F8FF"
ORANGE     = "#FF7043"
TEAL       = "#0F6E56"
BLUE       = "#185FA5"
AMBER      = "#BA7517"
PURPLE     = "#7B5EA7"
TEXT_DARK  = "#1A2744"
TEXT_MID   = "#4A5568"
TEXT_LIGHT = "#718096"

CATEGORY_COLORS = {
    "Hot":      ORANGE,
    "Mild":     TEAL,
    "Rainy":    BLUE,
    "Freezing": PURPLE
}

# Precompute KPI values
max_temp   = round(df["temperature_max"].max(), 1)
min_temp   = round(df["temperature_min"].min(), 1)
avg_precip = round(df["precipitation_total"].mean(), 2)
hot_days   = int((df["weather_category"] == "Hot").sum())
rainy_days = int((df["weather_category"] == "Rainy").sum())
mild_days  = int((df["weather_category"] == "Mild").sum())

# Today's weather category
today_row = df[df["forecast_date"] == today]
today_category = today_row["weather_category"].values[0] if len(today_row) > 0 else "Mild"
today_icons = {"Hot": "☀️", "Mild": "⛅", "Rainy": "🌧️", "Freezing": "❄️"}
today_icon = today_icons.get(today_category, "⛅")

# =============================================================================
# SECTION 4 — LAYOUT
# =============================================================================

def insight_row(label, value, color):
    return html.Div([
        html.Div([
            html.Div(style={
                "width": "8px", "height": "8px", "borderRadius": "50%",
                "background": color, "marginTop": "5px", "flexShrink": "0"
            }),
            html.Div([
                html.P(label, style={"margin": "0", "fontSize": "12px", "fontWeight": "500", "color": TEXT_DARK}),
                html.P(value, style={"margin": "2px 0 0 0", "fontSize": "11px", "color": TEXT_MID})
            ])
        ], style={"display": "flex", "gap": "10px", "alignItems": "flex-start"})
    ], style={
        "padding": "8px 0",
        "borderBottom": "0.5px solid #EDF2F7"
    })

def audience_panel(icon, title, subtitle, insights, accent_color, bg_color):
    return html.Div([
        html.Div([
            html.Div(icon, style={"fontSize": "28px", "marginBottom": "6px"}),
            html.H3(title, style={
                "margin": "0 0 2px 0", "fontSize": "15px",
                "fontWeight": "600", "color": accent_color
            }),
            html.P(subtitle, style={
                "margin": "0 0 12px 0", "fontSize": "11px", "color": TEXT_LIGHT
            }),
            html.Div([
                insight_row(label, value, color)
                for label, value, color in insights
            ])
        ])
    ], style={
        "background": CARD_BG,
        "borderRadius": "16px",
        "padding": "20px",
        "flex": "1",
        "border": "0.5px solid #E2E8F0",
        "borderTop": "3px solid " + accent_color,
        "boxShadow": "0 2px 8px rgba(0,0,0,0.06)"
    })

def kpi_card(icon, label, value, unit, color):
    return html.Div([
        html.Div(icon, style={"fontSize": "22px", "marginBottom": "6px"}),
        html.P(label, style={
            "margin": "0 0 4px 0", "fontSize": "11px",
            "color": TEXT_LIGHT, "textTransform": "uppercase",
            "letterSpacing": "0.06em", "fontWeight": "500"
        }),
        html.Div([
            html.Span(id="kpi-" + label.lower().replace(" ", "-"), children=str(value), style={
                "fontSize": "26px", "fontWeight": "700", "color": color
            }),
            html.Span(unit, style={"fontSize": "13px", "color": TEXT_LIGHT, "marginLeft": "3px"})
        ])
    ], style={
        "background": CARD_BG,
        "borderRadius": "14px",
        "padding": "16px 18px",
        "flex": "1",
        "border": "0.5px solid #E2E8F0",
        "borderTop": "3px solid " + color,
        "boxShadow": "0 2px 8px rgba(0,0,0,0.05)",
        "textAlign": "center"
    })

# CSS animations injected as a style tag via dangerouslySetInnerHTML
ANIMATION_CSS = """
@keyframes drift1 {
    0%   { transform: translateX(-120px); opacity: 0.7; }
    100% { transform: translateX(110vw);  opacity: 0.7; }
}
@keyframes drift2 {
    0%   { transform: translateX(-80px);  opacity: 0.5; }
    100% { transform: translateX(110vw);  opacity: 0.5; }
}
@keyframes pulse-sun {
    0%, 100% { box-shadow: 0 0 0 0px rgba(255,213,79,0.4); }
    50%       { box-shadow: 0 0 0 18px rgba(255,213,79,0); }
}
.cloud1 {
    position: absolute; top: 22px; left: 0;
    font-size: 48px; line-height: 1;
    animation: drift1 40s linear infinite;
}
.cloud2 {
    position: absolute; top: 44px; left: 0;
    font-size: 32px; line-height: 1;
    animation: drift2 25s linear infinite;
    animation-delay: -12s;
}
.sun-orb {
    position: absolute; top: 14px; right: 40px;
    width: 52px; height: 52px; border-radius: 50%;
    background: #FFD54F;
    animation: pulse-sun 3s ease-in-out infinite;
}
"""
# Write CSS to assets folder — Dash auto-loads all files from assets/
import os
os.makedirs("assets", exist_ok=True)
with open("assets/animations.css", "w") as f:
    f.write(ANIMATION_CSS)
animation_css = html.Div()  # empty placeholder

traffic_insights    = get_traffic_insights(df)
agriculture_insights = get_agriculture_insights(df)
tourism_insights    = get_tourism_insights(df)

app.layout = html.Div([

    animation_css,

    # ── ANIMATED SKY HEADER ───────────────────────────────────────────────────
    html.Div([
        html.Div(className="sun-orb"),
        html.Div("☁️", className="cloud1"),
        html.Div("⛅", className="cloud2"),

        # Chicago skyline using inline SVG string
        html.Div([
            html.Img(
                src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 100'%3E%3Crect x='0' y='60' width='30' height='40' fill='rgba(255,255,255,0.15)'/%3E%3Crect x='35' y='40' width='20' height='60' fill='rgba(255,255,255,0.15)'/%3E%3Crect x='60' y='20' width='25' height='80' fill='rgba(255,255,255,0.18)'/%3E%3Crect x='90' y='45' width='15' height='55' fill='rgba(255,255,255,0.15)'/%3E%3Crect x='110' y='30' width='35' height='70' fill='rgba(255,255,255,0.18)'/%3E%3Crect x='150' y='50' width='20' height='50' fill='rgba(255,255,255,0.15)'/%3E%3Crect x='175' y='35' width='18' height='65' fill='rgba(255,255,255,0.15)'/%3E%3Crect x='198' y='55' width='25' height='45' fill='rgba(255,255,255,0.12)'/%3E%3C/svg%3E",
                style={"width": "300px", "height": "100px", "position": "absolute", "bottom": "0", "left": "32px"}
            )
        ]),

        # Header text
        html.Div([
            html.Div([
                html.H1("Chicago Weather Intelligence", style={
                    "margin": "0", "fontSize": "26px", "fontWeight": "700",
                    "color": "#0D47A1", "textShadow": "0 1px 2px rgba(255,255,255,0.8)"
                }),
                html.P("Real-time insights for residents, tourists, commuters and farmers", style={
                    "margin": "4px 0 0 0", "fontSize": "13px", "color": "#1565C0"
                })
            ]),
            html.Div([
                html.Div([
                    html.Span(today_icon + " Today: ", style={"fontSize": "14px", "color": "#0D47A1"}),
                    html.Span(today_category, style={
                        "fontSize": "14px", "fontWeight": "600",
                        "color": CATEGORY_COLORS.get(today_category, BLUE)
                    })
                ]),
                html.Div(date_range_str, style={"fontSize": "12px", "color": "#1565C0", "marginTop": "4px"}),
                html.Div("Chicago, IL — 41.85°N 87.65°W", style={"fontSize": "11px", "color": "#1976D2", "marginTop": "2px"})
            ], style={"textAlign": "right"})
        ], style={
            "display": "flex", "justifyContent": "space-between",
            "alignItems": "center", "position": "relative", "zIndex": "2"
        })

    ], style={
        "background": "linear-gradient(180deg, #4FC3F7 0%, #87CEEB 60%, #E1F5FE 100%)",
        "padding": "24px 32px 28px",
        "position": "relative",
        "overflow": "hidden",
        "minHeight": "110px"
    }),

    # ── MAIN CONTENT ──────────────────────────────────────────────────────────
    html.Div([

        # KPI Cards
        html.Div([
            kpi_card("🌡️", "Peak Temp",   max_temp,   "F",    ORANGE),
            kpi_card("❄️",  "Lowest Temp", min_temp,   "F",    BLUE),
            kpi_card("🌧️", "Avg Precip",  avg_precip, "in",   TEAL),
            kpi_card("☀️",  "Hot Days",    hot_days,   "days", ORANGE),
            kpi_card("🌂",  "Rainy Days",  rainy_days, "days", BLUE),
            kpi_card("⛅",  "Mild Days",   mild_days,  "days", TEAL),
        ], style={
            "display": "flex", "gap": "14px",
            "marginBottom": "20px", "flexWrap": "wrap"
        }),

        # Filter bar
        html.Div([
            html.Div([
                html.Label("Filter by category:", style={
                    "fontSize": "13px", "fontWeight": "500",
                    "color": TEXT_MID, "marginRight": "10px"
                }),
                dcc.Dropdown(
                    id="category-filter",
                    options=[{"label": "All categories", "value": "All"}] +
                            [{"label": c, "value": c} for c in ["Hot", "Mild", "Rainy", "Freezing"]],
                    value="All", clearable=False,
                    style={"width": "200px", "fontSize": "13px"}
                )
            ], style={"display": "flex", "alignItems": "center"}),
            html.Div([
                html.Span("📍 ", style={"fontSize": "14px"}),
                html.Span("Downtown  •  Navy Pier  •  Millennium Park  •  O'Hare Airport  •  Midway Airport",
                    style={"fontSize": "12px", "color": TEXT_LIGHT})
            ])
        ], style={
            "display": "flex", "justifyContent": "space-between",
            "alignItems": "center", "background": CARD_BG,
            "padding": "12px 20px", "borderRadius": "12px",
            "marginBottom": "20px", "border": "0.5px solid #E2E8F0",
            "boxShadow": "0 1px 4px rgba(0,0,0,0.05)"
        }),

        # Temperature chart
        html.Div([
            html.Div([
                html.H3("Daily Temperature Trend", style={
                    "margin": "0", "fontSize": "15px",
                    "fontWeight": "600", "color": TEXT_DARK
                }),
                html.P("Max and min temperatures across 28 days — shaded area shows daily range",
                    style={"margin": "2px 0 0 0", "fontSize": "12px", "color": TEXT_LIGHT})
            ], style={"marginBottom": "12px"}),
            dcc.Graph(id="temp-chart", config={"displayModeBar": False})
        ], style={
            "background": CARD_BG, "borderRadius": "16px",
            "padding": "20px 24px", "marginBottom": "20px",
            "border": "0.5px solid #E2E8F0",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.05)"
        }),

        # Three audience panels
        html.Div([
            html.H3("Smart Insights by Audience", style={
                "margin": "0 0 14px 0", "fontSize": "16px",
                "fontWeight": "600", "color": TEXT_DARK
            }),
            html.Div([
                audience_panel("🚗", "Traffic & Commute",
                    "Plan your drive around Chicago weather",
                    traffic_insights, ORANGE, "#FFF8F6"),
                audience_panel("🌾", "Agriculture & Farming",
                    "Frost alerts, irrigation and planting windows",
                    agriculture_insights, TEAL, "#F0FAF6"),
                audience_panel("🏛️", "Tourism & Outdoors",
                    "Downtown, Navy Pier, Millennium Park & airports",
                    tourism_insights, BLUE, "#F0F8FF"),
            ], style={"display": "flex", "gap": "16px"})
        ], style={"marginBottom": "20px"}),

        # Bottom row — Precipitation + Donut
        html.Div([
            html.Div([
                html.H3("Daily Precipitation", style={
                    "margin": "0 0 4px 0", "fontSize": "15px",
                    "fontWeight": "600", "color": TEXT_DARK
                }),
                html.P("Total inches per day — blue bars indicate rainfall",
                    style={"margin": "0 0 12px 0", "fontSize": "12px", "color": TEXT_LIGHT}),
                dcc.Graph(id="precip-chart", config={"displayModeBar": False})
            ], style={
                "background": CARD_BG, "borderRadius": "16px",
                "padding": "20px 24px", "flex": "1.6",
                "border": "0.5px solid #E2E8F0",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.05)"
            }),

            html.Div([
                html.H3("Weather Category Mix", style={
                    "margin": "0 0 4px 0", "fontSize": "15px",
                    "fontWeight": "600", "color": TEXT_DARK
                }),
                html.P("Distribution across the 28-day window",
                    style={"margin": "0 0 12px 0", "fontSize": "12px", "color": TEXT_LIGHT}),
                dcc.Graph(id="category-chart", config={"displayModeBar": False})
            ], style={
                "background": CARD_BG, "borderRadius": "16px",
                "padding": "20px 24px", "flex": "1",
                "border": "0.5px solid #E2E8F0",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.05)"
            }),
        ], style={"display": "flex", "gap": "16px", "marginBottom": "20px"}),

        # Footer
        html.Div([
            html.Span("Chicago Weather Intelligence Dashboard  •  "),
            html.Span("Nivin Varghese | MSBA 2026  •  "),
            html.Span("Data: Open-Meteo REST API  •  "),
            html.Span("Database: Supabase PostgreSQL  •  "),
            html.Span("Updated: " + today.strftime("%B %d, %Y"))
        ], style={
            "textAlign": "center", "fontSize": "11px",
            "color": TEXT_LIGHT, "paddingBottom": "16px"
        })

    ], style={"padding": "24px 32px", "background": PAGE_BG, "minHeight": "100vh"})

], style={"fontFamily": "'Segoe UI', Inter, -apple-system, sans-serif", "margin": "0"})


# =============================================================================
# SECTION 5 — CALLBACKS
# =============================================================================

@app.callback(
    Output("temp-chart",     "figure"),
    Output("precip-chart",   "figure"),
    Output("category-chart", "figure"),
    Input("category-filter", "value")
)
def update_charts(selected_category):

    filtered = df if selected_category == "All" else df[df["weather_category"] == selected_category]

    base_layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=8, b=0),
        height=280,
        font=dict(family="Segoe UI, Inter, sans-serif", size=12, color=TEXT_MID),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, font=dict(size=11)),
        xaxis=dict(showgrid=False, showline=False, color=TEXT_LIGHT),
        yaxis=dict(showgrid=True, gridcolor="#EDF2F7", showline=False, color=TEXT_LIGHT)
    )

    # Temperature chart
    temp_fig = go.Figure()
    temp_fig.add_trace(go.Scatter(
        x=list(filtered["forecast_date"]) + list(filtered["forecast_date"])[::-1],
        y=list(filtered["temperature_max"]) + list(filtered["temperature_min"])[::-1],
        fill="toself", fillcolor="rgba(24,95,165,0.08)",
        line=dict(color="rgba(0,0,0,0)"),
        name="Temp range", showlegend=True
    ))
    temp_fig.add_trace(go.Scatter(
        x=filtered["forecast_date"], y=filtered["temperature_max"],
        mode="lines+markers", name="Max temp",
        line=dict(color=ORANGE, width=2.5),
        marker=dict(size=5, color=ORANGE),
        hovertemplate="%{x|%b %d}: %{y}F<extra>Max</extra>"
    ))
    temp_fig.add_trace(go.Scatter(
        x=filtered["forecast_date"], y=filtered["temperature_min"],
        mode="lines+markers", name="Min temp",
        line=dict(color=BLUE, width=2.5),
        marker=dict(size=5, color=BLUE),
        hovertemplate="%{x|%b %d}: %{y}F<extra>Min</extra>"
    ))
    temp_fig.add_vline(
        x=today.timestamp() * 1000,
        line_dash="dash", line_color="#CBD5E0", line_width=1.5,
        annotation_text="Today",
        annotation_font_size=11, annotation_font_color=TEXT_LIGHT
    )
    temp_fig.update_layout(**base_layout)
    temp_fig.update_yaxes(ticksuffix="F")

    # Precipitation chart
    precip_colors = [BLUE if v > 0 else "#EDF2F7" for v in filtered["precipitation_total"]]
    precip_fig = go.Figure(go.Bar(
        x=filtered["forecast_date"],
        y=filtered["precipitation_total"],
        marker_color=precip_colors,
        hovertemplate="%{x|%b %d}: %{y:.2f} in<extra></extra>"
    ))
    precip_fig.update_layout(**base_layout)
    precip_fig.update_yaxes(ticksuffix=" in")

    # Category donut
    cat_counts = df["weather_category"].value_counts().reset_index()
    cat_counts.columns = ["category", "count"]
    total_days = len(df)

    category_fig = go.Figure(go.Pie(
        labels=cat_counts["category"],
        values=cat_counts["count"],
        hole=0.58,
        marker_colors=[CATEGORY_COLORS.get(c, TEXT_LIGHT) for c in cat_counts["category"]],
        textinfo="label+percent",
        textfont=dict(size=12),
        hovertemplate="%{label}: %{value} days (%{percent})<extra></extra>"
    ))
    category_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=60, t=8, b=0),
        height=280,
        font=dict(family="Segoe UI, Inter, sans-serif", size=12, color=TEXT_MID),
        showlegend=False,
        annotations=[dict(
            text=str(total_days) + "<br>days",
            x=0.5, y=0.5,
            font=dict(size=14, color=TEXT_DARK),
            showarrow=False
        )]
    )

    return temp_fig, precip_fig, category_fig


# =============================================================================
# SECTION 6 — RUN
# =============================================================================

if __name__ == "__main__":
    print("Starting Chicago Weather Intelligence Dashboard v3...")
    print("Open your browser: http://127.0.0.1:8050")
    app.run(debug=True)
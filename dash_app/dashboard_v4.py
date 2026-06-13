# =============================================================================
# dashboard_v4.py
# Chicago Weather Intelligence Dashboard — v4
# Developer: Nivin Varghese | MSBA 2026
# Run: python dashboard_v4.py
# Open: http://127.0.0.1:8050
# =============================================================================

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
from sqlalchemy import create_engine, text
import os
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
date_start = df["forecast_date"].min().strftime("%b %d")
date_end   = df["forecast_date"].max().strftime("%b %d, %Y")

today_row = df[df["forecast_date"] == today]
today_category = today_row["weather_category"].values[0] if len(today_row) > 0 else "Mild"

# =============================================================================
# SECTION 2 — COLOURS
# =============================================================================

ORANGE  = "#FF7043"
TEAL    = "#0F6E56"
BLUE    = "#185FA5"
PURPLE  = "#7B5EA7"
DARK    = "#1A2744"
TEXT    = "#1A2744"
SUBTEXT = "#1565C0"
MUTED   = "#4A5568"
LIGHT   = "#718096"
PAGE_BG = "#EBF5FF"
CARD_BG = "#FFFFFF"

CATEGORY_COLORS = {
    "Hot":      ORANGE,
    "Mild":     TEAL,
    "Rainy":    BLUE,
    "Freezing": PURPLE
}

CAT_GRAD = {
    ORANGE: ("linear-gradient(145deg,#FFDDD0,#FFBFA8)", "#7B3010", "#CC4A1A"),
    BLUE:   ("linear-gradient(145deg,#D6EAFF,#AACFFF)", "#0A3A6E", "#0C4A8A"),
    TEAL:   ("linear-gradient(145deg,#C8F0E0,#96E0C4)", "#064030", "#0A5A42"),
    PURPLE: ("linear-gradient(145deg,#EDE0FF,#D4B8FF)", "#3A1A6E", "#5A2A9A"),
}

# =============================================================================
# SECTION 3 — INSIGHT LOGIC
# =============================================================================

def get_traffic_insights(data):
    insights = []
    high_risk = data[data["precipitation_probability"] >= 50]
    best_days = data[(data["precipitation_probability"] < 20) & (data["temperature_max"] < 90)]
    wet_roads = data[data["precipitation_total"] > 0.1]
    heat      = data[data["temperature_max"] > 88]
    if len(high_risk) > 0:
        days = ", ".join(high_risk["forecast_date"].dt.strftime("%b %d").tolist()[:3])
        insights.append(("High traffic risk days", days, ORANGE))
    if len(best_days) > 0:
        days = ", ".join(best_days["forecast_date"].dt.strftime("%b %d").tolist()[:3])
        insights.append(("Best commute days", days, TEAL))
    if len(wet_roads) > 0:
        days = ", ".join(wet_roads["forecast_date"].dt.strftime("%b %d").tolist()[:3])
        insights.append(("Wet roads : allow extra time", days, BLUE))
    if len(heat) > 0:
        insights.append(("Heat advisory", str(len(heat)) + " days : check tire pressure", ORANGE))
    return insights

def get_agriculture_insights(data):
    insights = []
    frost   = data[data["temperature_min"] < 32]
    optimal = data[(data["temperature_max"] >= 50) & (data["temperature_max"] <= 85) & (data["precipitation_probability"] < 40)]
    total_rain = round(data["precipitation_total"].sum(), 2)
    if len(frost) > 0:
        days = ", ".join(frost["forecast_date"].dt.strftime("%b %d").tolist())
        insights.append(("Frost risk : protect crops", days, PURPLE))
    else:
        insights.append(("No frost risk detected", "All temps above 32F this period", TEAL))
    if total_rain > 1.0:
        insights.append(("Good rainfall this period", str(total_rain) + " inches total", BLUE))
    else:
        insights.append(("Low rainfall : irrigation recommended", str(total_rain) + " inches total", ORANGE))
    if len(optimal) > 0:
        days = ", ".join(optimal["forecast_date"].dt.strftime("%b %d").tolist()[:4])
        insights.append(("Optimal planting window", days, TEAL))
    return insights

def get_tourism_insights(data):
    def outdoor_score(row):
        score = 100
        score -= row["precipitation_probability"] * 0.6
        if row["temperature_max"] < 45:   score -= 30
        elif row["temperature_max"] > 92: score -= 20
        elif 65 <= row["temperature_max"] <= 85: score += 10
        return max(0, min(100, round(score)))
    data = data.copy()
    data["outdoor_score"] = data.apply(outdoor_score, axis=1)
    perfect = data[data["outdoor_score"] >= 80].sort_values("outdoor_score", ascending=False)
    avoid   = data[data["outdoor_score"] < 40]
    streak = max_streak = 0
    for s in data["outdoor_score"]:
        streak = streak + 1 if s >= 70 else 0
        max_streak = max(max_streak, streak)
    insights = []
    if len(perfect) > 0:
        days = ", ".join(perfect["forecast_date"].dt.strftime("%b %d").tolist()[:3])
        insights.append(("Best days : Downtown and Navy Pier", days + " (score 80+)", BLUE))
        insights.append(("Millennium Park and The Bean", days + " : ideal outdoor conditions", TEAL))
        insights.append(("O'Hare and Midway airports", "Low weather delays on best days", TEAL))
    if len(avoid) > 0:
        days = ", ".join(avoid["forecast_date"].dt.strftime("%b %d").tolist()[:2])
        insights.append(("Avoid outdoor visits", days + " : indoor activities recommended", ORANGE))
    if max_streak > 0:
        insights.append(("Longest good weather streak", str(max_streak) + " consecutive days with score 70+", BLUE))
    return insights

# =============================================================================
# SECTION 4 — CSS ANIMATIONS
# =============================================================================

ANIMATION_CSS = """
@keyframes pulse-sun {
    0%,100% { box-shadow: 0 0 0 0px rgba(255,213,79,0.4); }
    50%      { box-shadow: 0 0 0 18px rgba(255,213,79,0); }
}
@keyframes spin-slow {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
}
@keyframes pulse-rays {
    0%,100% { opacity:0.6; transform:scale(1); }
    50%     { opacity:1;   transform:scale(1.2); }
}
@keyframes rain-fall {
    0%   { transform:translateY(-8px); opacity:0; }
    40%  { opacity:1; }
    100% { transform:translateY(24px); opacity:0; }
}
@keyframes snow-fall {
    0%   { transform:translateY(-8px) rotate(0deg);   opacity:0; }
    40%  { opacity:1; }
    100% { transform:translateY(24px) rotate(180deg); opacity:0; }
}
@keyframes cloud-sway {
    0%,100% { transform:translateX(0px); }
    50%     { transform:translateX(10px); }
}
.hot-sun   { font-size:42px; animation:spin-slow 8s linear infinite; display:inline-block; }
.hot-rays  { font-size:13px; animation:pulse-rays 2s ease-in-out infinite; letter-spacing:3px; }
.rain-cloud{ font-size:32px; }
.rain-drop { font-size:15px; animation:rain-fall 1.1s ease-in infinite; }
.rain-drop:nth-child(1){ animation-delay:0s; }
.rain-drop:nth-child(2){ animation-delay:0.25s; }
.rain-drop:nth-child(3){ animation-delay:0.5s; }
.rain-drop:nth-child(4){ animation-delay:0.75s; }
.mild-cloud{ font-size:42px; animation:cloud-sway 3s ease-in-out infinite; display:inline-block; }
.freeze-cloud{ font-size:32px; }
.snow-flake { font-size:14px; animation:snow-fall 1.8s ease-in infinite; }
.snow-flake:nth-child(1){ animation-delay:0s; }
.snow-flake:nth-child(2){ animation-delay:0.55s; }
.snow-flake:nth-child(3){ animation-delay:1.1s; }
.kpi-circle {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
/* Date range slider styling */
.rc-slider-track {
    background: linear-gradient(90deg, #185FA5, #4FC3F7) !important;
}
.rc-slider-handle {
    border-color: #185FA5 !important;
    background: #185FA5 !important;
    box-shadow: 0 2px 6px rgba(24,95,165,0.4) !important;
    width: 16px !important;
    height: 16px !important;
    margin-top: -6px !important;
}
.rc-slider-handle:hover, .rc-slider-handle:active {
    border-color: #0C447C !important;
    box-shadow: 0 0 0 5px rgba(24,95,165,0.15) !important;
}
.rc-slider-rail {
    background: #E2E8F0 !important;
    height: 4px !important;
}
.rc-slider-track {
    height: 4px !important;
}
"""

os.makedirs("assets", exist_ok=True)
with open("assets/animations.css", "w") as f:
    f.write(ANIMATION_CSS)

# =============================================================================
# SECTION 5 — HELPERS
# =============================================================================

def kpi_card(icon, label, value, unit, color):
    grad, label_color, val_color = CAT_GRAD.get(color, CAT_GRAD[BLUE])
    return html.Div([
        html.Div(icon, style={"fontSize":"22px","marginBottom":"4px"}),
        html.P(label, style={
            "margin":"0 0 3px 0","fontSize":"9px","color":label_color,
            "textTransform":"uppercase","letterSpacing":"0.07em","fontWeight":"500"
        }),
        html.Div([
            html.Span(str(value), style={"fontSize":"22px","fontWeight":"700","color":val_color}),
            html.Span(unit, style={"fontSize":"11px","color":label_color,"marginLeft":"2px"})
        ])
    ], className="kpi-circle", style={
        "background":grad,"borderRadius":"50%",
        "width":"115px","height":"115px",
        "display":"flex","flexDirection":"column",
        "alignItems":"center","justifyContent":"center",
        "border":"2.5px solid "+color,
        "boxShadow":"0 4px 14px rgba(0,0,0,0.12)",
        "flexShrink":"0","cursor":"default","textAlign":"center"
    })

def insight_row(label, value, color):
    return html.Div([
        html.Div(style={
            "width":"8px","height":"8px","borderRadius":"50%",
            "background":color,"marginTop":"5px","flexShrink":"0"
        }),
        html.Div([
            html.P(label, style={"margin":"0","fontSize":"12px","fontWeight":"500","color":TEXT}),
            html.P(value, style={"margin":"2px 0 0 0","fontSize":"11px","color":MUTED})
        ])
    ], style={"display":"flex","gap":"10px","alignItems":"flex-start",
              "padding":"8px 0","borderBottom":"0.5px solid #EDF2F7"})

def audience_panel(icon, title, subtitle, insights, accent):
    return html.Div([
        html.Div(icon, style={"fontSize":"26px","marginBottom":"6px"}),
        html.H3(title, style={"margin":"0 0 2px","fontSize":"14px","fontWeight":"600","color":accent}),
        html.P(subtitle, style={"margin":"0 0 10px","fontSize":"11px","color":LIGHT}),
        html.Div([insight_row(l,v,c) for l,v,c in insights])
    ], style={
        "background":CARD_BG,"borderRadius":"16px","padding":"18px 20px",
        "flex":"1","border":"0.5px solid #E2E8F0",
        "borderTop":"3px solid "+accent,
        "boxShadow":"0 2px 8px rgba(0,0,0,0.05)"
    })

# Precompute KPIs
max_temp   = round(df["temperature_max"].max(), 1)
min_temp   = round(df["temperature_min"].min(), 1)
avg_precip = round(df["precipitation_total"].mean(), 2)
hot_days   = int((df["weather_category"] == "Hot").sum())
rainy_days = int((df["weather_category"] == "Rainy").sum())
mild_days  = int((df["weather_category"] == "Mild").sum())

traffic_insights     = get_traffic_insights(df)
agriculture_insights = get_agriculture_insights(df)
tourism_insights     = get_tourism_insights(df)

# =============================================================================
# SECTION 6 — APP + LAYOUT
# =============================================================================

app = Dash(__name__)
app.title = "Chicago Weather Intelligence"

app.layout = html.Div([

    # ── HEADER ────────────────────────────────────────────────────────────────
    html.Div([

        # Left — title
        html.Div([
            html.H1("Chicago Weather Intelligence", style={
                "margin":"0","fontSize":"22px","fontWeight":"800",
                "color":"#0D47A1","letterSpacing":"-0.3px"
            }),
            html.P("Real-time insights for residents, tourists, commuters and farmers", style={
                "margin":"4px 0 0","fontSize":"12px","color":SUBTEXT,"fontWeight":"400"
            })
        ]),

        # Right — dynamic weather animation + info
        html.Div([
            html.Div(id="weather-anim-box", children=[], style={
                "display":"flex","flexDirection":"column",
                "alignItems":"center","gap":"3px"
            }),
            html.Div([
                html.Div("Today: " + today_category, style={
                    "fontSize":"13px","fontWeight":"700","color":"#0D47A1","textAlign":"right"
                }),
                html.Div(date_start + " : " + date_end, style={
                    "fontSize":"11px","color":SUBTEXT,"textAlign":"right"
                }),
                html.Div([
                    html.Span("Chicago, IL", style={"fontWeight":"700","color":"#0D47A1"}),
                    html.Span(" : 41.85°N 87.65°W", style={"color":SUBTEXT})
                ], style={"fontSize":"11px","textAlign":"right"})
            ])
        ], style={"display":"flex","alignItems":"center","gap":"14px"})

    ], style={
        "background":"linear-gradient(180deg,#4FC3F7 0%,#87CEEB 60%,#E1F5FE 100%)",
        "padding":"20px 32px","display":"flex",
        "justifyContent":"space-between","alignItems":"center",
        "position":"relative","overflow":"hidden","minHeight":"100px",
        "clipPath":"inset(0)"
    }),

    # ── MAIN CONTENT ──────────────────────────────────────────────────────────
    html.Div([

        # KPI circles
        html.Div([
            kpi_card("🌡️","Peak Temp",  max_temp,   "F",   ORANGE),
            kpi_card("❄️", "Lowest Temp",min_temp,   "F",   BLUE),
            kpi_card("🌧️","Avg Precip", avg_precip, "in",  TEAL),
            kpi_card("☀️", "Hot Days",   hot_days,   "days",ORANGE),
            kpi_card("🌂", "Rainy Days", rainy_days, "days",BLUE),
            kpi_card("⛅", "Mild Days",  mild_days,  "days",TEAL),
        ], style={
            "display":"flex","gap":"20px","flexWrap":"wrap",
            "marginBottom":"24px","justifyContent":"center","alignItems":"center"
        }),

        # ── SEGMENTED TAB FILTER ──────────────────────────────────────────────
        html.Div([
            html.Div("Filter by weather category:", style={
                "fontSize":"12px","fontWeight":"600","color":MUTED,
                "marginRight":"14px","whiteSpace":"nowrap"
            }),
            html.Div([
                html.Div([
                    html.Button(
                        ["🌍 All"],
                        id="tab-all", n_clicks=0,
                        style={
                            "padding":"9px 18px","fontSize":"12px","fontWeight":"500",
                            "border":"none","borderRight":"1px solid #E2E8F0",
                            "background":DARK,"color":"#fff","cursor":"pointer",
                            "borderRadius":"10px 0 0 10px","outline":"none"
                        }
                    ),
                    html.Button(
                        ["☀️ Hot"],
                        id="tab-hot", n_clicks=0,
                        style={
                            "padding":"9px 18px","fontSize":"12px","fontWeight":"500",
                            "border":"none","borderRight":"1px solid #E2E8F0",
                            "background":CARD_BG,"color":MUTED,"cursor":"pointer","outline":"none"
                        }
                    ),
                    html.Button(
                        ["⛅ Mild"],
                        id="tab-mild", n_clicks=0,
                        style={
                            "padding":"9px 18px","fontSize":"12px","fontWeight":"500",
                            "border":"none","borderRight":"1px solid #E2E8F0",
                            "background":CARD_BG,"color":MUTED,"cursor":"pointer","outline":"none"
                        }
                    ),
                    html.Button(
                        ["🌧️ Rainy"],
                        id="tab-rainy", n_clicks=0,
                        style={
                            "padding":"9px 18px","fontSize":"12px","fontWeight":"500",
                            "border":"none","borderRight":"1px solid #E2E8F0",
                            "background":CARD_BG,"color":MUTED,"cursor":"pointer","outline":"none"
                        }
                    ),
                    html.Button(
                        ["❄️ Freezing"],
                        id="tab-freezing", n_clicks=0,
                        style={
                            "padding":"9px 18px","fontSize":"12px","fontWeight":"500",
                            "border":"none",
                            "background":CARD_BG,"color":MUTED,"cursor":"pointer",
                            "borderRadius":"0 10px 10px 0","outline":"none"
                        }
                    ),
                ], style={
                    "display":"flex","border":"1.5px solid #E2E8F0",
                    "borderRadius":"10px","overflow":"hidden",
                    "boxShadow":"0 2px 8px rgba(0,0,0,0.06)"
                })
            ]),
            # Vertical divider
            html.Div(style={
                "width":"1px","height":"36px","background":"#E2E8F0","flexShrink":"0"
            }),

            # Date range slider
            html.Div([
                html.Div("📅 Date Range:", style={
                    "fontSize":"11px","fontWeight":"600","color":MUTED,"marginBottom":"6px"
                }),
                dcc.RangeSlider(
                    id="date-slider",
                    min=0, max=len(df)-1,
                    value=[0, len(df)-1],
                    marks={
                        0:           {"label": df["forecast_date"].iloc[0].strftime("%b %d"),
                                      "style": {"fontSize":"10px","color":BLUE,"fontWeight":"600"}},
                        len(df)//2:  {"label": df["forecast_date"].iloc[len(df)//2].strftime("%b %d"),
                                      "style": {"fontSize":"10px","color":LIGHT}},
                        len(df)-1:   {"label": df["forecast_date"].iloc[-1].strftime("%b %d"),
                                      "style": {"fontSize":"10px","color":BLUE,"fontWeight":"600"}},
                    },
                    tooltip={"placement":"bottom","always_visible":False},
                    allowCross=False,
                )
            ], style={"flex":"1","minWidth":"220px","maxWidth":"340px"}),

            # Location strip
            html.Div([
                html.Span("📍 ", style={"fontSize":"13px"}),
                html.Span("Downtown : Navy Pier : Millennium Park : O'Hare : Midway",
                    style={"fontSize":"11px","color":LIGHT})
            ], style={"marginLeft":"auto","whiteSpace":"nowrap"})
        ], style={
            "display":"flex","alignItems":"center","background":CARD_BG,
            "padding":"12px 20px","borderRadius":"12px","marginBottom":"20px",
            "border":"0.5px solid #E2E8F0","boxShadow":"0 1px 4px rgba(0,0,0,0.05)",
            "gap":"14px","flexWrap":"wrap"
        }),

        # Hidden store for selected category + date range
        dcc.Store(id="selected-category", data="All"),
        dcc.Store(id="date-range", data=[0, len(df)-1]),

        # Temperature chart
        html.Div([
            html.H3("Daily Temperature Trend", style={
                "margin":"0 0 2px","fontSize":"15px","fontWeight":"600","color":TEXT
            }),
            html.P("Max and min temperatures across 28 days : shaded area shows daily range",
                style={"margin":"0 0 12px","fontSize":"12px","color":LIGHT}),
            dcc.Graph(id="temp-chart", config={"displayModeBar":False})
        ], style={
            "background":CARD_BG,"borderRadius":"16px","padding":"20px 24px",
            "marginBottom":"20px","border":"0.5px solid #E2E8F0",
            "boxShadow":"0 2px 8px rgba(0,0,0,0.05)"
        }),

        # Audience panels
        html.Div([
            html.H3("Smart Insights by Audience", style={
                "margin":"0 0 14px","fontSize":"16px","fontWeight":"600","color":TEXT
            }),
            html.Div([
                audience_panel("🚗","Traffic and Commute",
                    "Plan your drive around Chicago weather",
                    traffic_insights, ORANGE),
                audience_panel("🌾","Agriculture and Farming",
                    "Frost alerts, irrigation and planting windows",
                    agriculture_insights, TEAL),
                audience_panel("🏛️","Tourism and Outdoors",
                    "Downtown, Navy Pier, Millennium Park and airports",
                    tourism_insights, BLUE),
            ], style={"display":"flex","gap":"16px"})
        ], style={"marginBottom":"20px"}),

        # Bottom row
        html.Div([
            html.Div([
                html.H3("Daily Precipitation", style={
                    "margin":"0 0 4px","fontSize":"15px","fontWeight":"600","color":TEXT
                }),
                html.P("Total inches per day",
                    style={"margin":"0 0 12px","fontSize":"12px","color":LIGHT}),
                dcc.Graph(id="precip-chart", config={"displayModeBar":False})
            ], style={
                "background":CARD_BG,"borderRadius":"16px","padding":"20px 24px",
                "flex":"1.6","border":"0.5px solid #E2E8F0",
                "boxShadow":"0 2px 8px rgba(0,0,0,0.05)"
            }),
            html.Div([
                html.H3("Weather Category Mix", style={
                    "margin":"0 0 4px","fontSize":"15px","fontWeight":"600","color":TEXT
                }),
                html.P("Distribution across 28 days",
                    style={"margin":"0 0 12px","fontSize":"12px","color":LIGHT}),
                dcc.Graph(id="category-chart", config={"displayModeBar":False})
            ], style={
                "background":CARD_BG,"borderRadius":"16px","padding":"20px 24px",
                "flex":"1","border":"0.5px solid #E2E8F0",
                "boxShadow":"0 2px 8px rgba(0,0,0,0.05)"
            }),
        ], style={"display":"flex","gap":"16px","marginBottom":"20px"}),

        # Hidden hover trigger
        html.Div(id="hover-trigger", n_clicks=0, style={"display":"none"}),

        # Footer
        html.Div([
            html.Span("Chicago Weather Intelligence Dashboard  :  "),
            html.Span("Nivin Varghese : MSBA 2026  :  "),
            html.Span("Data: Open-Meteo REST API  :  "),
            html.Span("Database: Supabase PostgreSQL  :  "),
            html.Span("Updated: " + today.strftime("%B %d, %Y"))
        ], style={
            "textAlign":"center","fontSize":"11px",
            "color":LIGHT,"paddingBottom":"16px"
        })

    ], style={"padding":"24px 32px","background":PAGE_BG,"minHeight":"100vh"})

], style={"fontFamily":"'Segoe UI', Inter, -apple-system, sans-serif","margin":"0"})


# =============================================================================
# SECTION 7 — CALLBACKS
# =============================================================================

# Weather animation
@app.callback(
    Output("weather-anim-box","children"),
    Input("selected-category","data")
)
def update_weather_animation(_):
    if today_category == "Hot":
        return [
            html.Div("☀️", className="hot-sun"),
            html.Div("✨✨✨", className="hot-rays"),
        ]
    elif today_category == "Rainy":
        return [
            html.Div("🌧️", className="rain-cloud"),
            html.Div([
                html.Span("💧", className="rain-drop"),
                html.Span("💧", className="rain-drop"),
                html.Span("💧", className="rain-drop"),
                html.Span("💧", className="rain-drop"),
            ], style={"display":"flex","gap":"5px"}),
        ]
    elif today_category == "Freezing":
        return [
            html.Div("🌨️", className="freeze-cloud"),
            html.Div([
                html.Span("❄️", className="snow-flake"),
                html.Span("❄️", className="snow-flake"),
                html.Span("❄️", className="snow-flake"),
            ], style={"display":"flex","gap":"6px"}),
        ]
    else:
        return [html.Div("⛅", className="mild-cloud")]


# Tab selection — update store + button styles
@app.callback(
    Output("selected-category","data"),
    Output("tab-all",      "style"),
    Output("tab-hot",      "style"),
    Output("tab-mild",     "style"),
    Output("tab-rainy",    "style"),
    Output("tab-freezing", "style"),
    Input("tab-all",      "n_clicks"),
    Input("tab-hot",      "n_clicks"),
    Input("tab-mild",     "n_clicks"),
    Input("tab-rainy",    "n_clicks"),
    Input("tab-freezing", "n_clicks"),
)
def update_tabs(n_all, n_hot, n_mild, n_rainy, n_freeze):
    # Note: date-slider has its own callback below
    from dash import ctx
    triggered = ctx.triggered_id or "tab-all"

    tab_map = {
        "tab-all":      ("All",      DARK,   "#fff"),
        "tab-hot":      ("Hot",      ORANGE, "#fff"),
        "tab-mild":     ("Mild",     TEAL,   "#fff"),
        "tab-rainy":    ("Rainy",    BLUE,   "#fff"),
        "tab-freezing": ("Freezing", PURPLE, "#fff"),
    }

    selected = tab_map[triggered][0]

    def tab_style(tab_id, is_first=False, is_last=False):
        active = triggered == tab_id
        bg   = tab_map[tab_id][1] if active else CARD_BG
        col  = tab_map[tab_id][2] if active else MUTED
        base = {
            "padding":"9px 18px","fontSize":"12px","fontWeight":"500",
            "border":"none","background":bg,"color":col,
            "cursor":"pointer","outline":"none",
            "borderRight":"1px solid #E2E8F0" if not is_last else "none"
        }
        if is_first:
            base["borderRadius"] = "10px 0 0 10px"
        if is_last:
            base["borderRadius"] = "0 10px 10px 0"
        return base

    return (
        selected,
        tab_style("tab-all",      is_first=True),
        tab_style("tab-hot"),
        tab_style("tab-mild"),
        tab_style("tab-rainy"),
        tab_style("tab-freezing", is_last=True),
    )


# Charts
@app.callback(
    Output("temp-chart",     "figure"),
    Output("precip-chart",   "figure"),
    Output("category-chart", "figure"),
    Input("selected-category","data"),
    Input("date-slider",     "value")
)
def update_charts(selected_category, date_range):
    start_idx = date_range[0] if date_range else 0
    end_idx   = date_range[1] if date_range else len(df)-1
    date_filtered = df.iloc[start_idx:end_idx+1]
    filtered = date_filtered if selected_category == "All" else date_filtered[date_filtered["weather_category"] == selected_category]

    base = dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0,r=0,t=8,b=0), height=280,
        font=dict(family="Segoe UI, Inter, sans-serif", size=12, color=MUTED),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1,font=dict(size=11)),
        xaxis=dict(showgrid=False,showline=False,color=LIGHT),
        yaxis=dict(showgrid=True,gridcolor="#EDF2F7",showline=False,color=LIGHT)
    )

    # Temperature
    temp_fig = go.Figure()
    temp_fig.add_trace(go.Scatter(
        x=list(filtered["forecast_date"]) + list(filtered["forecast_date"])[::-1],
        y=list(filtered["temperature_max"]) + list(filtered["temperature_min"])[::-1],
        fill="toself", fillcolor="rgba(24,95,165,0.08)",
        line=dict(color="rgba(0,0,0,0)"), name="Temp range", showlegend=True
    ))
    temp_fig.add_trace(go.Scatter(
        x=filtered["forecast_date"], y=filtered["temperature_max"],
        mode="lines+markers", name="Max temp",
        line=dict(color=ORANGE, width=2.5), marker=dict(size=5, color=ORANGE),
        hovertemplate="%{x|%b %d}: %{y}F<extra>Max</extra>"
    ))
    temp_fig.add_trace(go.Scatter(
        x=filtered["forecast_date"], y=filtered["temperature_min"],
        mode="lines+markers", name="Min temp",
        line=dict(color=BLUE, width=2.5), marker=dict(size=5, color=BLUE),
        hovertemplate="%{x|%b %d}: %{y}F<extra>Min</extra>"
    ))
    temp_fig.add_vline(
        x=today.timestamp()*1000, line_dash="dash",
        line_color="#CBD5E0", line_width=1.5,
        annotation_text="Today", annotation_font_size=11,
        annotation_font_color=LIGHT
    )
    temp_fig.update_layout(**base)
    temp_fig.update_yaxes(ticksuffix="F")

    # Precipitation
    precip_colors = [BLUE if v > 0 else "#EDF2F7" for v in filtered["precipitation_total"]]
    precip_fig = go.Figure(go.Bar(
        x=filtered["forecast_date"], y=filtered["precipitation_total"],
        marker_color=precip_colors,
        hovertemplate="%{x|%b %d}: %{y:.2f} in<extra></extra>"
    ))
    precip_fig.update_layout(**base)
    precip_fig.update_yaxes(ticksuffix=" in")

    # Donut
    cat_counts = df["weather_category"].value_counts().reset_index()
    cat_counts.columns = ["category","count"]
    category_fig = go.Figure(go.Pie(
        labels=cat_counts["category"], values=cat_counts["count"],
        hole=0.58,
        marker_colors=[CATEGORY_COLORS.get(c, LIGHT) for c in cat_counts["category"]],
        textinfo="label+percent", textfont=dict(size=12),
        hovertemplate="%{label}: %{value} days (%{percent})<extra></extra>"
    ))
    category_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0,r=60,t=8,b=0), height=280,
        font=dict(family="Segoe UI, Inter, sans-serif", size=12, color=MUTED),
        showlegend=False,
        annotations=[dict(
            text=str(len(df))+"<br>days", x=0.5, y=0.5,
            font=dict(size=14, color=TEXT), showarrow=False
        )]
    )

    return temp_fig, precip_fig, category_fig


# Hover JS
app.clientside_callback(
    """
    function(n) {
        setTimeout(function() {
            var cards = document.querySelectorAll('.kpi-circle');
            cards.forEach(function(card) {
                card.addEventListener('mouseenter', function() {
                    this.style.transform = 'scale(1.13)';
                    this.style.boxShadow = '0 10px 28px rgba(0,0,0,0.20)';
                });
                card.addEventListener('mouseleave', function() {
                    this.style.transform = 'scale(1.0)';
                    this.style.boxShadow = '0 4px 14px rgba(0,0,0,0.12)';
                });
            });
        }, 800);
        return n;
    }
    """,
    Output("hover-trigger","data-value"),
    Input("hover-trigger","n_clicks"),
    prevent_initial_call=False
)


# =============================================================================
# SECTION 8 — RUN
# =============================================================================

if __name__ == "__main__":
    print("Starting Chicago Weather Intelligence Dashboard v4...")
    print("Open your browser: http://127.0.0.1:8050")
    app.run(debug=True)
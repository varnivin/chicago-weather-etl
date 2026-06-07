# =============================================================================
# dashboard.py
# Chicago Weather Trend Analytics — Interactive Dashboard
# Developer: Nivin Varghese | MSBA 2026
# Run: python dashboard.py
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

def load_data():
    #engine = create_engine("sqlite:///chicago_weather.db")
    engine = create_engine("postgresql://postgres.mimtgltdqiequdyptkey:Chicagodatabase2026@aws-1-us-east-2.pooler.supabase.com:5432/postgres")
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM weather_data ORDER BY forecast_date"), conn)
    df["forecast_date"] = pd.to_datetime(df["forecast_date"])
    return df

df = load_data()
today = pd.Timestamp.today().normalize()

# =============================================================================
# SECTION 2 — APP SETUP
# =============================================================================

app = Dash(__name__)
app.title = "Chicago Weather Analytics"

BLUE   = "#185FA5"
AMBER  = "#BA7517"
TEAL   = "#0F6E56"
CORAL  = "#993C1D"
PURPLE = "#534AB7"
LIGHT  = "#F4F6FA"
WHITE  = "#FFFFFF"

CATEGORY_COLORS = {
    "Hot":      CORAL,
    "Mild":     TEAL,
    "Rainy":    BLUE,
    "Freezing": PURPLE
}

# =============================================================================
# SECTION 3 — LAYOUT HELPERS
# =============================================================================

def kpi_card(title, value, unit="", color=BLUE):
    return html.Div([
        html.P(title, style={
            "fontSize": "13px", "color": "#6B7280",
            "margin": "0 0 6px 0", "fontWeight": "500"
        }),
        html.Div([
            html.Span(str(value), style={
                "fontSize": "28px", "fontWeight": "600", "color": color
            }),
            html.Span(unit, style={
                "fontSize": "14px", "color": "#6B7280", "marginLeft": "4px"
            })
        ])
    ], style={
        "background": WHITE, "borderRadius": "12px",
        "padding": "16px 20px", "flex": "1",
        "boxShadow": "0 1px 4px rgba(0,0,0,0.08)",
        "borderTop": "3px solid " + color
    })

# KPI values
max_temp   = round(df["temperature_max"].max(), 1)
min_temp   = round(df["temperature_min"].min(), 1)
avg_precip = round(df["precipitation_total"].mean(), 2)
rainy_days = int((df["weather_category"] == "Rainy").sum())
hot_days   = int((df["weather_category"] == "Hot").sum())
date_range = df["forecast_date"].min().strftime("%b %d") + " — " + df["forecast_date"].max().strftime("%b %d, %Y")

# =============================================================================
# SECTION 4 — APP LAYOUT
# =============================================================================

app.layout = html.Div([

    # Header
    html.Div([
        html.Div([
            html.H1("Chicago Weather Analytics", style={
                "margin": "0", "fontSize": "24px",
                "fontWeight": "700", "color": WHITE
            }),
            html.P(
                "Nivin Varghese | MSBA 2026 | Open-Meteo API | Chicago, IL (41.85N, -87.65W)",
                style={"margin": "4px 0 0 0", "fontSize": "13px", "color": "#B5D4F4"}
            )
        ]),
        html.Div(
            "Data range: " + date_range,
            style={"fontSize": "13px", "color": "#B5D4F4", "alignSelf": "center"}
        )
    ], style={
        "background": "#0C447C",
        "padding": "20px 32px",
        "display": "flex",
        "justifyContent": "space-between",
        "alignItems": "center"
    }),

    # Main content
    html.Div([

        # KPI Cards
        html.Div([
            kpi_card("Highest Temperature", max_temp,   "F",    CORAL),
            kpi_card("Lowest Temperature",  min_temp,   "F",    BLUE),
            kpi_card("Avg Precipitation",   avg_precip, "in",   TEAL),
            kpi_card("Rainy Days",          rainy_days, "days", BLUE),
            kpi_card("Hot Days",            hot_days,   "days", CORAL),
        ], style={
            "display": "flex", "gap": "16px",
            "marginBottom": "24px", "flexWrap": "wrap"
        }),

        # Filter
        html.Div([
            html.Label("Filter by weather category:", style={
                "fontSize": "13px", "fontWeight": "500",
                "color": "#374151", "marginRight": "12px"
            }),
            dcc.Dropdown(
                id="category-filter",
                options=[{"label": "All categories", "value": "All"}] +
                        [{"label": c, "value": c} for c in ["Hot", "Mild", "Rainy", "Freezing"]],
                value="All",
                clearable=False,
                style={"width": "220px", "fontSize": "13px"}
            )
        ], style={
            "display": "flex", "alignItems": "center",
            "marginBottom": "20px", "background": WHITE,
            "padding": "12px 20px", "borderRadius": "10px",
            "boxShadow": "0 1px 4px rgba(0,0,0,0.06)"
        }),

        # Temperature Chart
        html.Div([
            html.H3("Daily Temperature Trend (F)", style={
                "fontSize": "15px", "fontWeight": "600",
                "color": "#111827", "margin": "0 0 4px 0"
            }),
            html.P(
                "Shaded area shows daily temperature range. Dashed line marks today.",
                style={"fontSize": "12px", "color": "#6B7280", "margin": "0 0 12px 0"}
            ),
            dcc.Graph(id="temp-chart", config={"displayModeBar": False})
        ], style={
            "background": WHITE, "borderRadius": "12px",
            "padding": "20px 24px", "marginBottom": "20px",
            "boxShadow": "0 1px 4px rgba(0,0,0,0.06)"
        }),

        # Bottom row
        html.Div([

            # Precipitation
            html.Div([
                html.H3("Daily Precipitation (inches)", style={
                    "fontSize": "15px", "fontWeight": "600",
                    "color": "#111827", "margin": "0 0 4px 0"
                }),
                html.P(
                    "Total daily precipitation in inches.",
                    style={"fontSize": "12px", "color": "#6B7280", "margin": "0 0 12px 0"}
                ),
                dcc.Graph(id="precip-chart", config={"displayModeBar": False})
            ], style={
                "background": WHITE, "borderRadius": "12px",
                "padding": "20px 24px", "flex": "1.6",
                "boxShadow": "0 1px 4px rgba(0,0,0,0.06)"
            }),

            # Category Donut
            html.Div([
                html.H3("Weather Category Breakdown", style={
                    "fontSize": "15px", "fontWeight": "600",
                    "color": "#111827", "margin": "0 0 4px 0"
                }),
                html.P(
                    "Distribution of weather types across 28 days.",
                    style={"fontSize": "12px", "color": "#6B7280", "margin": "0 0 12px 0"}
                ),
                dcc.Graph(id="category-chart", config={"displayModeBar": False})
            ], style={
                "background": WHITE, "borderRadius": "12px",
                "padding": "20px 24px", "flex": "1",
                "boxShadow": "0 1px 4px rgba(0,0,0,0.06)"
            }),

        ], style={"display": "flex", "gap": "20px"}),

        # Footer
        html.Div(
            "Chicago Weather Trend Analytics | Nivin Varghese MSBA 2026 | Data: Open-Meteo REST API | Updated: " + today.strftime("%B %d, %Y"),
            style={
                "textAlign": "center", "fontSize": "12px",
                "color": "#9CA3AF", "marginTop": "24px",
                "paddingBottom": "16px"
            }
        )

    ], style={"padding": "24px 32px", "background": LIGHT, "minHeight": "100vh"})

], style={"fontFamily": "Inter, -apple-system, sans-serif", "margin": "0"})


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

    chart_layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=8, b=0),
        height=300,
        font=dict(family="Inter, sans-serif", size=12, color="#374151"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # Chart 1 — Temperature Trend
    temp_fig = go.Figure()

    temp_fig.add_trace(go.Scatter(
        x=list(filtered["forecast_date"]) + list(filtered["forecast_date"])[::-1],
        y=list(filtered["temperature_max"]) + list(filtered["temperature_min"])[::-1],
        fill="toself",
        fillcolor="rgba(24,95,165,0.1)",
        line=dict(color="rgba(255,255,255,0)"),
        name="Temperature range",
        showlegend=True
    ))

    temp_fig.add_trace(go.Scatter(
        x=filtered["forecast_date"],
        y=filtered["temperature_max"],
        mode="lines+markers",
        name="Max temp",
        line=dict(color=CORAL, width=2.5),
        marker=dict(size=5, color=CORAL)
    ))

    temp_fig.add_trace(go.Scatter(
        x=filtered["forecast_date"],
        y=filtered["temperature_min"],
        mode="lines+markers",
        name="Min temp",
        line=dict(color=BLUE, width=2.5),
        marker=dict(size=5, color=BLUE)
    ))

    temp_fig.add_vline(
        x=today.timestamp() * 1000,
        line_dash="dash",
        line_color="#9CA3AF",
        line_width=1.5,
        annotation_text="Today",
        annotation_font_size=11
    )

    temp_fig.update_layout(**chart_layout)
    temp_fig.update_xaxes(showgrid=False, showline=False)
    temp_fig.update_yaxes(showgrid=True, gridcolor="#F3F4F6", ticksuffix="F", showline=False)

    # Chart 2 — Precipitation
    precip_colors = [BLUE if v > 0 else "#E5E7EB" for v in filtered["precipitation_total"]]

    precip_fig = go.Figure(go.Bar(
        x=filtered["forecast_date"],
        y=filtered["precipitation_total"],
        marker_color=precip_colors,
        name="Precipitation",
        hovertemplate="%{x|%b %d}: %{y:.2f} in<extra></extra>"
    ))
    precip_fig.update_layout(**chart_layout)
    precip_fig.update_xaxes(showgrid=False, showline=False)
    precip_fig.update_yaxes(showgrid=True, gridcolor="#F3F4F6", ticksuffix=" in", showline=False)

    # Chart 3 — Category Donut
    cat_counts = df["weather_category"].value_counts().reset_index()
    cat_counts.columns = ["category", "count"]

    donut_annotation = dict(
        text="28 days",
        x=0.5,
        y=0.5,
        font_size=13,
        showarrow=False
    )

    category_fig = go.Figure(go.Pie(
        labels=cat_counts["category"],
        values=cat_counts["count"],
        hole=0.55,
        marker_colors=[CATEGORY_COLORS.get(c, "#9CA3AF") for c in cat_counts["category"]],
        textinfo="label+percent",
        textfont_size=12,
        hovertemplate="%{label}: %{value} days<extra></extra>"
    ))

    category_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=8, b=0),
        height=300,
        font=dict(family="Inter, sans-serif", size=12, color="#374151"),
        showlegend=True,
        legend=dict(orientation="v", x=0.85, y=0.5),
        annotations=[donut_annotation]
    )

    return temp_fig, precip_fig, category_fig


# =============================================================================
# SECTION 6 — RUN
# =============================================================================

if __name__ == "__main__":
    print("Starting Chicago Weather Dashboard...")
    print("Open your browser and go to: http://127.0.0.1:8050")
    app.run(debug=True)
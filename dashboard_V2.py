# =============================================================================
# dashboard_v2.py
# Chicago Weather Analytics — Enhanced Dashboard v2
# Developer: Nivin Varghese | MSBA 2026
# Run: python dashboard_v2.py
# Open: http://127.0.0.1:8050
# =============================================================================

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
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
    except Exception:
        engine = create_engine("sqlite:///chicago_weather.db")
        with engine.connect() as conn:
            df = pd.read_sql(text("SELECT * FROM weather_data ORDER BY forecast_date"), conn)
    df["forecast_date"] = pd.to_datetime(df["forecast_date"])
    return df

df = load_data()
today = pd.Timestamp.today().normalize()
min_date = df["forecast_date"].min()
max_date = df["forecast_date"].max()

# =============================================================================
# SECTION 2 — APP + THEME
# =============================================================================

app = Dash(__name__)
app.title = "Chicago Weather Analytics v2"

DARK_BG      = "#0F1117"
DARK_SURFACE = "#1A1D2E"
DARK_CARD    = "#21253A"
DARK_BORDER  = "#2E3250"
BLUE         = "#4F8EF7"
TEAL         = "#00C9A7"
CORAL        = "#FF6B6B"
AMBER        = "#FFD166"
PURPLE       = "#A78BFA"
TEXT_PRIMARY = "#F1F5F9"
TEXT_MUTED   = "#8892A4"

CATEGORY_COLORS = {
    "Hot":      CORAL,
    "Mild":     TEAL,
    "Rainy":    BLUE,
    "Freezing": PURPLE
}

# =============================================================================
# SECTION 3 — LAYOUT HELPERS
# =============================================================================

def kpi_card(title, value, unit="", color=BLUE, icon=""):
    return html.Div([
        html.Div(icon, style={"fontSize": "24px", "marginBottom": "8px"}),
        html.P(title, style={
            "fontSize": "11px", "color": TEXT_MUTED, "margin": "0 0 4px 0",
            "textTransform": "uppercase", "letterSpacing": "0.08em", "fontWeight": "500"
        }),
        html.Div([
            html.Span(str(value), style={
                "fontSize": "32px", "fontWeight": "700", "color": color
            }),
            html.Span(unit, style={
                "fontSize": "14px", "color": TEXT_MUTED, "marginLeft": "4px"
            })
        ])
    ], style={
        "background": DARK_CARD,
        "borderRadius": "16px",
        "padding": "20px 24px",
        "flex": "1",
        "border": "1px solid " + DARK_BORDER,
        "borderTop": "3px solid " + color
    })

# KPI values
max_temp   = round(df["temperature_max"].max(), 1)
min_temp   = round(df["temperature_min"].min(), 1)
avg_precip = round(df["precipitation_total"].mean(), 2)
avg_range  = round(df["temp_range"].mean(), 1)
rainy_days = int((df["weather_category"] == "Rainy").sum())
hot_days   = int((df["weather_category"] == "Hot").sum())

# =============================================================================
# SECTION 4 — LAYOUT
# =============================================================================

app.layout = html.Div([

    # Sidebar
    html.Div([
        html.Div([
            html.Div("🌤", style={"fontSize": "32px", "marginBottom": "8px"}),
            html.H2("Chicago", style={"margin": "0", "fontSize": "18px", "fontWeight": "700", "color": TEXT_PRIMARY}),
            html.P("Weather Analytics", style={"margin": "0", "fontSize": "12px", "color": TEXT_MUTED}),
        ], style={"padding": "24px 20px 20px", "borderBottom": "1px solid " + DARK_BORDER}),

        html.Div([
            html.P("FILTERS", style={"fontSize": "10px", "color": TEXT_MUTED, "letterSpacing": "0.1em", "margin": "0 0 12px 0", "fontWeight": "500"}),

            html.Label("Weather Category", style={"fontSize": "12px", "color": TEXT_MUTED, "marginBottom": "6px", "display": "block"}),
            dcc.Dropdown(
                id="category-filter",
                options=[{"label": "All categories", "value": "All"}] +
                        [{"label": c, "value": c} for c in ["Hot", "Mild", "Rainy", "Freezing"]],
                value="All",
                clearable=False,
                style={"fontSize": "13px", "marginBottom": "20px"},
            ),

            html.Label("Date Range", style={"fontSize": "12px", "color": TEXT_MUTED, "marginBottom": "10px", "display": "block"}),
            dcc.RangeSlider(
                id="date-slider",
                min=0,
                max=len(df) - 1,
                value=[0, len(df) - 1],
                marks={
                    0: {"label": min_date.strftime("%b %d"), "style": {"color": TEXT_MUTED, "fontSize": "10px"}},
                    len(df) // 2: {"label": df["forecast_date"].iloc[len(df) // 2].strftime("%b %d"), "style": {"color": TEXT_MUTED, "fontSize": "10px"}},
                    len(df) - 1: {"label": max_date.strftime("%b %d"), "style": {"color": TEXT_MUTED, "fontSize": "10px"}}
                },
                tooltip={"placement": "bottom", "always_visible": False}
            ),

        ], style={"padding": "24px 20px"}),

        # Sidebar footer
        html.Div([
            html.P("Data source", style={"fontSize": "10px", "color": TEXT_MUTED, "margin": "0", "letterSpacing": "0.05em"}),
            html.P("Open-Meteo API", style={"fontSize": "12px", "color": BLUE, "margin": "2px 0 0 0"}),
            html.P("Nivin Varghese", style={"fontSize": "11px", "color": TEXT_MUTED, "margin": "12px 0 0 0"}),
            html.P("MSBA 2026", style={"fontSize": "11px", "color": TEXT_MUTED, "margin": "2px 0 0 0"}),
        ], style={
            "position": "absolute", "bottom": "24px", "left": "20px", "right": "20px",
            "borderTop": "1px solid " + DARK_BORDER, "paddingTop": "16px"
        })

    ], style={
        "width": "220px", "minHeight": "100vh", "background": DARK_SURFACE,
        "borderRight": "1px solid " + DARK_BORDER, "position": "fixed",
        "top": "0", "left": "0", "bottom": "0", "overflowY": "auto",
        "position": "relative", "flexShrink": "0"
    }),

    # Main content
    html.Div([

        # Top bar
        html.Div([
            html.H1("Weather Dashboard", style={
                "margin": "0", "fontSize": "20px", "fontWeight": "700", "color": TEXT_PRIMARY
            }),
            html.Div(
                "Chicago, IL | " + min_date.strftime("%b %d") + " — " + max_date.strftime("%b %d, %Y"),
                style={"fontSize": "13px", "color": TEXT_MUTED}
            )
        ], style={
            "display": "flex", "justifyContent": "space-between", "alignItems": "center",
            "padding": "20px 28px", "borderBottom": "1px solid " + DARK_BORDER,
            "background": DARK_SURFACE
        }),

        html.Div([

            # KPI row
            html.Div([
                kpi_card("Peak Temperature",  max_temp,   "F",    CORAL,   "🌡"),
                kpi_card("Lowest Temperature", min_temp,  "F",    BLUE,    "❄"),
                kpi_card("Avg Precipitation",  avg_precip,"in",   TEAL,    "🌧"),
                kpi_card("Avg Temp Swing",     avg_range, "F",    AMBER,   "📊"),
                kpi_card("Hot Days",           hot_days,  "days", CORAL,   "☀"),
                kpi_card("Rainy Days",         rainy_days,"days", BLUE,    "🌂"),
            ], style={"display": "flex", "gap": "14px", "marginBottom": "20px", "flexWrap": "wrap"}),

            # Temperature trend
            html.Div([
                html.Div([
                    html.H3("Temperature Trend", style={"margin": "0", "fontSize": "15px", "fontWeight": "600", "color": TEXT_PRIMARY}),
                    html.P("Daily max and min temperatures with range area", style={"margin": "2px 0 0 0", "fontSize": "12px", "color": TEXT_MUTED})
                ]),
                dcc.Graph(id="temp-chart", config={"displayModeBar": False})
            ], style={
                "background": DARK_CARD, "borderRadius": "16px",
                "padding": "20px 24px", "marginBottom": "16px",
                "border": "1px solid " + DARK_BORDER
            }),

            # Middle row — Precipitation + Scatter
            html.Div([

                html.Div([
                    html.H3("Precipitation", style={"margin": "0", "fontSize": "15px", "fontWeight": "600", "color": TEXT_PRIMARY}),
                    html.P("Daily total in inches", style={"margin": "2px 0 12px 0", "fontSize": "12px", "color": TEXT_MUTED}),
                    dcc.Graph(id="precip-chart", config={"displayModeBar": False})
                ], style={
                    "background": DARK_CARD, "borderRadius": "16px",
                    "padding": "20px 24px", "flex": "1",
                    "border": "1px solid " + DARK_BORDER
                }),

                html.Div([
                    html.H3("Temp vs Precipitation", style={"margin": "0", "fontSize": "15px", "fontWeight": "600", "color": TEXT_PRIMARY}),
                    html.P("Max temperature vs precipitation probability", style={"margin": "2px 0 12px 0", "fontSize": "12px", "color": TEXT_MUTED}),
                    dcc.Graph(id="scatter-chart", config={"displayModeBar": False})
                ], style={
                    "background": DARK_CARD, "borderRadius": "16px",
                    "padding": "20px 24px", "flex": "1",
                    "border": "1px solid " + DARK_BORDER
                }),

            ], style={"display": "flex", "gap": "16px", "marginBottom": "16px"}),

            # Bottom row — Heatmap + Donut
            html.Div([

                html.Div([
                    html.H3("Temperature Heatmap", style={"margin": "0", "fontSize": "15px", "fontWeight": "600", "color": TEXT_PRIMARY}),
                    html.P("Daily temperature range intensity", style={"margin": "2px 0 12px 0", "fontSize": "12px", "color": TEXT_MUTED}),
                    dcc.Graph(id="heatmap-chart", config={"displayModeBar": False})
                ], style={
                    "background": DARK_CARD, "borderRadius": "16px",
                    "padding": "20px 24px", "flex": "1.6",
                    "border": "1px solid " + DARK_BORDER
                }),

                html.Div([
                    html.H3("Category Breakdown", style={"margin": "0", "fontSize": "15px", "fontWeight": "600", "color": TEXT_PRIMARY}),
                    html.P("Weather type distribution", style={"margin": "2px 0 12px 0", "fontSize": "12px", "color": TEXT_MUTED}),
                    dcc.Graph(id="category-chart", config={"displayModeBar": False})
                ], style={
                    "background": DARK_CARD, "borderRadius": "16px",
                    "padding": "20px 24px", "flex": "1",
                    "border": "1px solid " + DARK_BORDER
                }),

            ], style={"display": "flex", "gap": "16px"}),

        ], style={"padding": "24px 28px"})

    ], style={"flex": "1", "minWidth": "0", "background": DARK_BG})

], style={
    "display": "flex", "fontFamily": "Inter, -apple-system, sans-serif",
    "margin": "0", "background": DARK_BG, "minHeight": "100vh"
})


# =============================================================================
# SECTION 5 — CALLBACKS
# =============================================================================

@app.callback(
    Output("temp-chart",     "figure"),
    Output("precip-chart",   "figure"),
    Output("scatter-chart",  "figure"),
    Output("heatmap-chart",  "figure"),
    Output("category-chart", "figure"),
    Input("category-filter", "value"),
    Input("date-slider",     "value")
)
def update_charts(selected_category, date_range):

    start_idx = date_range[0]
    end_idx   = date_range[1]
    date_filtered = df.iloc[start_idx:end_idx + 1]
    filtered = date_filtered if selected_category == "All" else date_filtered[date_filtered["weather_category"] == selected_category]

    dark_layout = dict(
        paper_bgcolor=DARK_CARD,
        plot_bgcolor=DARK_CARD,
        margin=dict(l=0, r=0, t=8, b=0),
        height=260,
        font=dict(family="Inter, sans-serif", size=12, color=TEXT_PRIMARY),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(color=TEXT_MUTED, size=11)),
        xaxis=dict(showgrid=False, showline=False, color=TEXT_MUTED),
        yaxis=dict(showgrid=True, gridcolor=DARK_BORDER, showline=False, color=TEXT_MUTED)
    )

    # Chart 1 — Temperature Trend
    temp_fig = go.Figure()
    temp_fig.add_trace(go.Scatter(
        x=list(filtered["forecast_date"]) + list(filtered["forecast_date"])[::-1],
        y=list(filtered["temperature_max"]) + list(filtered["temperature_min"])[::-1],
        fill="toself", fillcolor="rgba(79,142,247,0.12)",
        line=dict(color="rgba(0,0,0,0)"),
        name="Temp range", showlegend=True
    ))
    temp_fig.add_trace(go.Scatter(
        x=filtered["forecast_date"], y=filtered["temperature_max"],
        mode="lines+markers", name="Max",
        line=dict(color=CORAL, width=2.5),
        marker=dict(size=5, color=CORAL)
    ))
    temp_fig.add_trace(go.Scatter(
        x=filtered["forecast_date"], y=filtered["temperature_min"],
        mode="lines+markers", name="Min",
        line=dict(color=BLUE, width=2.5),
        marker=dict(size=5, color=BLUE)
    ))
    temp_fig.add_vline(
        x=today.timestamp() * 1000,
        line_dash="dash", line_color=TEXT_MUTED, line_width=1.5,
        annotation_text="Today", annotation_font_size=11,
        annotation_font_color=TEXT_MUTED
    )
    temp_fig.update_layout(**{**dark_layout, "height": 280})
    temp_fig.update_yaxes(ticksuffix="F")

    # Chart 2 — Precipitation
    precip_colors = [TEAL if v > 0 else DARK_BORDER for v in filtered["precipitation_total"]]
    precip_fig = go.Figure(go.Bar(
        x=filtered["forecast_date"],
        y=filtered["precipitation_total"],
        marker_color=precip_colors,
        hovertemplate="%{x|%b %d}: %{y:.2f} in<extra></extra>"
    ))
    precip_fig.update_layout(**dark_layout)
    precip_fig.update_yaxes(ticksuffix=" in")

    # Chart 3 — Scatter
    scatter_colors = [CATEGORY_COLORS.get(c, TEXT_MUTED) for c in filtered["weather_category"]]
    scatter_fig = go.Figure(go.Scatter(
        x=filtered["temperature_max"],
        y=filtered["precipitation_probability"],
        mode="markers",
        marker=dict(
            size=10, color=scatter_colors,
            line=dict(width=1, color=DARK_BG)
        ),
        text=filtered["forecast_date"].dt.strftime("%b %d") + " - " + filtered["weather_category"],
        hovertemplate="%{text}<br>Max: %{x}F | Precip prob: %{y}%<extra></extra>"
    ))
    scatter_fig.update_layout(**dark_layout)
    scatter_fig.update_xaxes(ticksuffix="F", title=dict(text="Max Temperature", font=dict(size=11, color=TEXT_MUTED)))
    scatter_fig.update_yaxes(ticksuffix="%", title=dict(text="Precip Probability", font=dict(size=11, color=TEXT_MUTED)))

    # Chart 4 — Heatmap
    heatmap_data = filtered[["forecast_date", "temperature_max", "temperature_min", "temp_range"]].copy()
    heatmap_data["week"]    = heatmap_data["forecast_date"].dt.isocalendar().week.astype(str)
    heatmap_data["weekday"] = heatmap_data["forecast_date"].dt.strftime("%a")

    heatmap_fig = go.Figure(go.Bar(
        x=filtered["forecast_date"],
        y=filtered["temp_range"],
        marker=dict(
            color=filtered["temperature_max"],
            colorscale=[[0, BLUE], [0.5, AMBER], [1, CORAL]],
            showscale=True,
            colorbar=dict(
                title=dict(text="Max F", font=dict(color=TEXT_MUTED, size=11)),
                tickfont=dict(color=TEXT_MUTED, size=10),
                thickness=12, len=0.8
            )
        ),
        hovertemplate="%{x|%b %d}<br>Range: %{y}F<extra></extra>"
    ))
    heatmap_fig.update_layout(**dark_layout)
    heatmap_fig.update_yaxes(ticksuffix="F", title=dict(text="Temp Range", font=dict(size=11, color=TEXT_MUTED)))

    # Chart 5 — Donut
    cat_counts = df["weather_category"].value_counts().reset_index()
    cat_counts.columns = ["category", "count"]

    category_fig = go.Figure(go.Pie(
        labels=cat_counts["category"],
        values=cat_counts["count"],
        hole=0.6,
        marker_colors=[CATEGORY_COLORS.get(c, TEXT_MUTED) for c in cat_counts["category"]],
        textinfo="label+percent",
        textfont=dict(size=11, color=TEXT_PRIMARY),
        hovertemplate="%{label}: %{value} days<extra></extra>"
    ))
    category_fig.update_layout(
        paper_bgcolor=DARK_CARD, plot_bgcolor=DARK_CARD,
        margin=dict(l=0, r=60, t=8, b=0), height=260,
        font=dict(family="Inter, sans-serif", size=12, color=TEXT_PRIMARY),
        showlegend=False,
        annotations=[dict(
            text=str(len(df)) + "<br>days",
            x=0.5, y=0.5, font_size=14,
            font_color=TEXT_PRIMARY, showarrow=False
        )]
    )

    return temp_fig, precip_fig, scatter_fig, heatmap_fig, category_fig


# =============================================================================
# SECTION 6 — RUN
# =============================================================================

if __name__ == "__main__":
    print("Starting Chicago Weather Dashboard v2...")
    print("Open your browser and go to: http://127.0.0.1:8050")
    app.run(debug=True)
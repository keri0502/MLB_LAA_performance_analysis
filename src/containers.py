from dash import Dash, dcc, html, Input, Output, State, callback
import plotly.express as px
import plotly.graph_objects as go

from charts import (
    plot_contribution_salary_scatter,
    plot_laa_batter_radar,
    plot_laa_pitcher_radar,
    plot_overview_breakdown,
    TEAM_ID
)

#--------------------------------------------------------------#
# Radar Chart                                                  #
#--------------------------------------------------------------#

def radar_container():
    """雷達圖區塊：只放圖，不放控制元件。"""
    return html.Div([
        html.H3(
            "Team Radar (PR values)",
            style={"textAlign": "center"}
        ),
        html.Div(
            id="radar-grid",
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(3, minmax(0, 1fr))",
                "gap": "16px",
                "alignItems": "start",
            }
        )
    ])

@callback(
    Output("radar-grid", "children"),
    Input("apply-button", "n_clicks"),
    State("player-type-radio", "value"),
    State("sub-type-dropdown", "value"),
)
def update_radar_grid(n_clicks, player_type, sub_type):
    if n_clicks == 0 or not sub_type:
        return []

    # sub_type 因為 multi=True，會是 list
    selected = sub_type if isinstance(sub_type, list) else [sub_type]

    cards = []
    for group_value in selected:
        if player_type == "batter":
            fig = plot_laa_batter_radar(group_code=group_value)
            title = f"{group_value} Radar"
        else:
            group_code = group_value.replace(" ", "_")
            fig = plot_laa_pitcher_radar(group_code=group_code)
            title = f"{group_value} Radar"

        fig.update_layout(height=320, margin=dict(l=40, r=40, t=50, b=40))

        cards.append(
            html.Div(
                [
                    html.H4(title, style={"textAlign": "center", "margin": "8px 0"}),
                    dcc.Graph(
                        figure=fig,
                        config={"displayModeBar": False},
                        style={"height": "320px"},
                    ),
                ],
                style={
                    "border": "1px solid #ddd",
                    "borderRadius": "12px",
                    "padding": "8px",
                    "backgroundColor": "white",
                    "overflow": "hidden",
                },
            )
        )

    return cards

#--------------------------------------------------------------#
# Contribution vs. Salary Scatter Plot                         #
#--------------------------------------------------------------#

def contribution_salary_container():
    container = html.Div([
        # 建立 checkbox
        dcc.RadioItems(
            id="player-type-radio",
            options=[
                {"label": "batter", "value": "batter"},
                {"label": "pitcher", "value": "pitcher"},
            ],
            value="batter",   # 預設選項
            inline=True       # 兩個選項排成一列
        ),
        # 建立 dropdown，會根據 checkbox 的值而改變
        dcc.Dropdown(
            id="sub-type-dropdown",
            value=None,
            placeholder="please choose",
            multi=True
        ),
        html.Button("Apply", id="apply-button", n_clicks=0),
        # 取得 scatter plot，根據 checkbox 跟 dropdown 所選的值而變化
        html.H3(
            "Salary vs. Player Contribution",
            style={"textAlign": "center"}
        ),
        dcc.Graph(id="player-scatter-graph")
    ])
    return container


@callback(
    Output("sub-type-dropdown", "options"),
    Output("sub-type-dropdown", "value"),
    Input("player-type-radio", "value")
)
def update_dropdown(player_type):
    if player_type == "batter":
        options = [
            {"label": "1B", "value": "1B"},
            {"label": "2B", "value": "2B"},
            {"label": "3B", "value": "3B"},
            {"label": "SS", "value": "SS"},
            {"label": "C", "value": "C"},
            {"label": "OF", "value": "OF"},
            {"label": "DH", "value": "DH"},
        ]
        default_value = None
    else:
        options = [
            {"label": "SP R", "value": "SP R"},
            {"label": "SP L", "value": "SP L"},
            {"label": "RP R", "value": "RP R"},
            {"label": "RP L", "value": "RP L"},
        ]
        default_value = None

    return options, default_value


@callback(
    Output("player-scatter-graph", "figure"),
    Input("apply-button", "n_clicks"),
    State("player-type-radio", "value"),
    State("sub-type-dropdown", "value")
)
def update_scatter(n_clicks, player_type, sub_type):
    if n_clicks == 0 or sub_type is None:
        return px.scatter()
    return plot_contribution_salary_scatter(
        player_type=player_type,
        roles=sub_type
    )

#--------------------------------------------------------------#
# Overview Container                                           #
#--------------------------------------------------------------#

def overview_container():
    return html.Div(
        [
            html.H2("Team Overview – LAA"),

            # tiles placeholder
            html.Div(
                [
                    html.Div(["SP tile"], style={"border": "1px solid #999", "padding": "8px", "width": "90px"}),
                    html.Div(["RP tile"], style={"border": "1px solid #999", "padding": "8px", "width": "90px"}),
                    html.Div(["H tile"],  style={"border": "1px solid #999", "padding": "8px", "width": "90px"}),
                    html.Div(["W/L + Standing"], style={"marginLeft": "40px"}),
                ],
                style={"display": "flex", "alignItems": "center", "marginBottom": "20px"},
            ),

            # dropdown
            html.Div(
                [
                    html.Label("Select group:"),
                    dcc.Dropdown(
                        id="overview-group-dropdown",
                        options=[
                            {"label": "Starting Pitcher (SP)", "value": "SP"},
                            {"label": "Relief Pitcher (RP)", "value": "RP"},
                            {"label": "Hitters (H)", "value": "H"},
                        ],
                        value="SP",
                        clearable=False,
                        style={"width": "320px"},
                    ),
                ],
                style={"marginBottom": "10px"},
            ),

            # placeholder graph
            dcc.Graph(id="overview-breakdown-chart"),
        ],
        style={"padding": "20px"},
    )

@callback(
    Output("overview-breakdown-chart", "figure"),
    Input("overview-group-dropdown", "value")
)
def overview_breakdown_real(group):
    return plot_overview_breakdown(team_id=TEAM_ID, group=group)
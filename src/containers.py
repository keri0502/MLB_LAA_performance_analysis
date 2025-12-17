import plotly.express as px
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc

from src.charts import (
    plot_contribution_salary_scatter,
    plot_laa_batter_radar,
    plot_laa_hitter_team_radar,
    plot_laa_pitcher_radar,
    plot_overview_breakdown,
    plot_performance_radar,
    plot_performance_bar,
    get_overview_tiles,
    get_team_record,
    get_player_list
)
from src.constant import TEAM_ID, TEAM_COLOR


def radar_container():
    """
    雷達圖區塊：只放圖，不放控制元件。
    """
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


def contribution_salary_container():
    """
    Contribution vs. Salary 區塊 - 美化版
    內含 scatter plot + dropdown + data table
    """
    return html.Div([
        # Scatter Plot 圖表容器
        html.Div(
            [
                dcc.Graph(id="player-scatter-graph")
            ],
            style={
                "background": "white",
                "borderRadius": "12px",
                "boxShadow": "0 4px 12px rgba(0,0,0,0.1)",
                "border": "1px solid #e3e6f0",
                "padding": "20px",
                "marginBottom": "20px"
            }
        ),
        
        # Action Selection + Player Recommendations 合併容器
        html.Div(
            [
                html.H5("Player Analysis & Recommendations", style={
                    "color": "#2c3e50",
                    "fontWeight": "600",
                    "marginBottom": "20px",
                    "fontSize": "18px",
                    "textAlign": "center"
                }),
                
                # Action Selection 區域
                html.Div([
                    html.Label("Action Selection:", style={
                        "color": "#2c3e50",
                        "fontWeight": "600",
                        "marginBottom": "8px",
                        "fontSize": "14px",
                        "display": "block"
                    }),
                    dcc.Dropdown(
                        id="action-dropdown",
                        options=[
                            {"label": "Retain", "value": "retain"},
                            {"label": "Trade", "value": "trade"},
                            {"label": "Extend", "value": "extend"},
                            {"label": "Option", "value": "option"},
                        ],
                        value="retain",
                        placeholder="Please choose an action",
                        style={"marginBottom": "20px"}
                    )
                ]),
                
                # Data Table
                dash_table.DataTable(
                    id="player-list",
                    data=[],
                    page_size=10,
                    sort_action="native",
                    style_as_list_view=True,
                    style_cell={
                        "fontFamily": "Roboto, sans-serif",
                        "fontSize": "16px",
                        "textAlign": "center",
                        "padding": "12px 15px",
                        "backgroundColor": "white",
                        "color": "#333333",
                    },
                    style_header={
                        "backgroundColor": TEAM_COLOR,
                        "color": "white",
                        "fontWeight": "bold",
                        "fontSize": "18px",
                        "border": "none",
                    },
                    style_data={
                        "borderBottom": "1px solid #E0E0E0",
                    },
                    style_data_conditional=[
                        {
                            "if": {"row_index": "odd"},
                            "backgroundColor": "#F9F9F9"
                        },
                        {
                            "if": {"state": "active"},
                            "backgroundColor": "rgba(186, 0, 33, 0.1)",
                            "border": "1px solid #BA0021",
                        }
                    ]
                )
            ],
            style={
                "background": "white",
                "borderRadius": "12px",
                "boxShadow": "0 4px 12px rgba(0,0,0,0.1)",
                "border": "1px solid #e3e6f0",
                "padding": "20px"
            }
        )
    ])


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


@callback(
    Output("player-list", "data"),
    Output("player-list", "columns"),
    Input("apply-button", "n_clicks"),
    Input("action-dropdown", "value"),
    State("player-type-radio", "value"),
    State("sub-type-dropdown", "value"),
    prevent_initial_call=True
)
def update_player_list(n_clicks, action, player_type, sub_type):
    if n_clicks == 0 or sub_type is None:
        return [], []
    players = get_player_list(
        player_type=player_type,
        roles=sub_type,
        action=action
    )
    return players.to_dict("records"), [{"name": col.upper(), "id": col} for col in players.columns]


def trend_symbol(diff):
    if diff is None:
        return "–"
    return "▲" if diff >= 0 else "▼"


def summary_row(label, diff):
    diff_color = "#28a745" if diff is None or diff >= 0 else "#dc3545"  # 綠色為正，紅色為負
    bg_gradient = "linear-gradient(135deg, #ffffff 0%, #f8f9fb 100%)"
    
    return html.Div(
        children=[
            html.Div(
                [
                    html.H5(label, style={
                        "textAlign": "center",
                        "color": "#2c3e50",
                        "fontSize": "20px",
                        "fontWeight": "600",
                        "marginBottom": "8px",
                        "lineHeight": "1.2"
                    }),
                    html.Span(
                        "N/A" if diff is None else f"{trend_symbol(diff)} {diff:+.1f}%",
                        style={
                            "fontWeight": "900",
                            "color": diff_color,
                            "fontSize": "24px",
                            "textShadow": "0 1px 2px rgba(0,0,0,0.1)"
                        }
                    )
                ],
                style={
                    "textAlign": "center",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "center",
                    "height": "100%",
                    "padding": "15px"
                }
            )
        ],
        style={
            "height": "140px",
            "background": bg_gradient,
            "border": "1px solid #e3e6f0",
            "borderRadius": "12px",
            "boxShadow": "0 4px 12px rgba(0,0,0,0.1)",
            "transition": "all 0.3s ease",
            "position": "relative",
            "overflow": "hidden"
        }
    )


def overview_container():
    """
    Overview page 主要區塊 - 美化版
    包含戰績卡 + 概覽卡 + 三張雷達圖"""
    tiles = get_overview_tiles(TEAM_ID)
    record = get_team_record(TEAM_ID)

    sp_radar = plot_laa_pitcher_radar("SP")
    rp_radar = plot_laa_pitcher_radar("RP")
    h_radar = plot_laa_hitter_team_radar()

    # 戰績數據
    win = record["W"]
    loss = record["L"]
    rank = record["Rank"]

    return html.Div(
        [
            # 主要數據卡片區域
            dbc.Container([
                dbc.Row(
                    [
                        # Record 卡片
                        dbc.Col(
                            html.Div(
                                [
                                    html.H5("Team Record", style={
                                        "textAlign": "center",
                                        "color": "#2c3e50",
                                        "fontSize": "20px",
                                        "fontWeight": "600",
                                        "marginBottom": "8px"
                                    }),
                                    html.Div([
                                        html.Span(
                                            f"{win}-{loss}" if win is not None and loss is not None else "N/A",
                                            style={
                                                "fontSize": "24px",
                                                "fontWeight": "900",
                                                "color": "#2c3e50",
                                                "textShadow": "0 1px 2px rgba(0,0,0,0.1)"
                                            }
                                        )
                                    ], style={"textAlign": "center"})
                                ],
                                style={
                                    "textAlign": "center",
                                    "display": "flex",
                                    "flexDirection": "column",
                                    "justifyContent": "center",
                                    "height": "140px",
                                    "background": "linear-gradient(135deg, #ffffff 0%, #f8f9fb 100%)",
                                    "borderRadius": "12px",
                                    "boxShadow": "0 4px 12px rgba(0,0,0,0.1)",
                                    "border": "1px solid #e3e6f0",
                                    "padding": "15px"
                                }
                            ),
                            width=12, md=3, className="mb-3"
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    html.H5("Division Rank", style={
                                        "textAlign": "center",
                                        "color": "#2c3e50",
                                        "fontSize": "20px",
                                        "fontWeight": "600",
                                        "marginBottom": "8px"
                                    }),
                                    html.Div(
                                        f"{rank}th" if rank is not None else "N/A",
                                        style={
                                            "textAlign": "center",
                                            "fontSize": "24px",
                                            "fontWeight": "900",
                                            "color": "#2c3e50",
                                            "textShadow": "0 1px 2px rgba(0,0,0,0.1)"
                                        }
                                    )
                                ],
                                style={
                                    "textAlign": "center",
                                    "display": "flex",
                                    "flexDirection": "column",
                                    "justifyContent": "center",
                                    "height": "140px",
                                    "background": "linear-gradient(135deg, #ffffff 0%, #f8f9fb 100%)",
                                    "borderRadius": "12px",
                                    "boxShadow": "0 4px 12px rgba(0,0,0,0.1)",
                                    "border": "1px solid #e3e6f0",
                                    "padding": "15px"
                                }
                            ),
                            width=12, md=3, className="mb-3"
                        ),
                        dbc.Col(
                            summary_row("Starting Pitcher", tiles["SP"]["diff"]),
                            width=12, md=2, className="mb-3"
                        ),
                        dbc.Col(
                            summary_row("Relief Pitcher", tiles["RP"]["diff"]),
                            width=12, md=2, className="mb-3"
                        ),
                        dbc.Col(
                            summary_row("Batters", tiles["H"]["diff"]),
                            width=12, md=2, className="mb-3"
                        ),
                    ],
                    className="g-3 mb-4"
                )
            ], fluid=True),
            dbc.Container([
                dbc.Row(
                    [
                        dbc.Col([
                            html.Div(
                                [
                                    html.H5("Starting Pitcher Radar", style={
                                        "textAlign": "center",
                                        "color": "#2c3e50",
                                        "fontWeight": "600",
                                        "marginBottom": "15px"
                                    }),
                                    dcc.Graph(
                                        figure=sp_radar,
                                        config={"displayModeBar": False},
                                        style={"height": "360px"}
                                    )
                                ],
                                style={
                                    "background": "white",
                                    "borderRadius": "12px",
                                    "boxShadow": "0 4px 12px rgba(0,0,0,0.1)",
                                    "border": "1px solid #e3e6f0",
                                    "padding": "20px"
                                }
                            )
                        ], width=12, md=4, className="mb-3"),
                        dbc.Col([
                            html.Div(
                                [
                                    html.H5("Relief Pitcher Radar", style={
                                        "textAlign": "center",
                                        "color": "#2c3e50",
                                        "fontWeight": "600",
                                        "marginBottom": "15px"
                                    }),
                                    dcc.Graph(
                                        figure=rp_radar,
                                        config={"displayModeBar": False},
                                        style={"height": "360px"}
                                    )
                                ],
                                style={
                                    "background": "white",
                                    "borderRadius": "12px",
                                    "boxShadow": "0 4px 12px rgba(0,0,0,0.1)",
                                    "border": "1px solid #e3e6f0",
                                    "padding": "20px"
                                }
                            )
                        ], width=12, md=4, className="mb-3"),
                        dbc.Col([
                            html.Div(
                                [
                                    html.H5("Batter Radar", style={
                                        "textAlign": "center",
                                        "color": "#2c3e50",
                                        "fontWeight": "600",
                                        "marginBottom": "15px"
                                    }),
                                    dcc.Graph(
                                        figure=h_radar,
                                        config={"displayModeBar": False},
                                        style={"height": "360px"}
                                    )
                                ],
                                style={
                                    "background": "white",
                                    "borderRadius": "12px",
                                    "boxShadow": "0 4px 12px rgba(0,0,0,0.1)",
                                    "border": "1px solid #e3e6f0",
                                    "padding": "20px"
                                }
                            )
                        ], width=12, md=4, className="mb-3"),
                    ],
                    className="g-3"
                )
            ], fluid=True)
        ],
        style={
            "padding": "25px",
            "minHeight": "100vh"
        },
    )


@callback(
    Output("overview-breakdown-chart", "figure"),
    Input("overview-group-dropdown", "value")
)
def overview_breakdown_real(group):
    return plot_overview_breakdown(team_id=TEAM_ID, group=group)


def card(children, title: str | None = None, className: str = ""):
    return html.Div(
        [
            html.Div(title, style={
                "textAlign": "center",
                "color": "#2c3e50",
                "fontWeight": "600",
                "marginBottom": "15px",
                "fontSize": "16px"
            }) if title else None,
            html.Div(children, className="card-body"),
        ],
        style={
            "background": "white",
            "borderRadius": "12px",
            "boxShadow": "0 4px 12px rgba(0,0,0,0.1)",
            "border": "1px solid #e3e6f0",
            "padding": "20px",
            "margin": "10px 0"
        },
        className=f"card {className}".strip(),
    )


def filter_bar(radio_id: str, dropdown_id: str, button_id: str, default_player_type: str = "batter"):
    """
    共用的篩選列：RadioItems + Dropdown + Apply（同一行）
    - 選項內容由 callback 決定（你要用 Contribution 的那套）
    """
    return html.Div(
        [
            dcc.RadioItems(
                id=radio_id,
                options=[
                    {"label": "Batter", "value": "batter"},
                    {"label": "Pitcher", "value": "pitcher"},
                ],
                value=default_player_type,
                inline=True,
            ),
            dcc.Dropdown(
                id=dropdown_id,
                value=None,
                placeholder="please choose",
                multi=True,
                style={"width": "420px"},
            ),
            html.Button(
                "Apply",
                id=button_id,
                n_clicks=0,
                style={"height": "30px"},
            ),
        ],
        style={
            "display": "flex",
            "alignItems": "center",
            "gap": "12px",
            "marginBottom": "12px",
        },
    )


@callback(
    Output("sub-type-dropdown", "options"),
    Output("sub-type-dropdown", "value"),
    Input("player-type-radio", "value"),
)
def perf_update_dropdown(player_type):
    """
    Batter: defensive positions
    Pitcher: SP/RP
    """
    if player_type == "batter":
        options = [
            {"label": "C", "value": "C"},
            {"label": "1B", "value": "1B"},
            {"label": "2B", "value": "2B"},
            {"label": "3B", "value": "3B"},
            {"label": "SS", "value": "SS"},
            {"label": "OF", "value": "OF"},
            {"label": "DH", "value": "DH"},
        ]
    else:
        options = [
            {"label": "SP R", "value": "SP R"},
            {"label": "SP L", "value": "SP L"},
            {"label": "RP R", "value": "RP R"},
            {"label": "RP L", "value": "RP L"},
        ]

    return options, None


@callback(
    Output("perf-bar-chart", "figure"),
    Output("perf-radar-grid", "children"),
    Input("apply-button", "n_clicks"),
    State("player-type-radio", "value"),
    State("sub-type-dropdown", "value"),
)
def perf_update_charts(n_clicks, player_type, sub_types):
    if n_clicks == 0 or not sub_types:
        return px.bar(), []

    bar_groups = sub_types
    radar_groups = sub_types

    if player_type == "pitcher":
        # for bar: only POS matters
        bar_groups = sub_types
        # for radar: needs underscore code
        radar_groups = [s.replace(" ", "_") for s in sub_types]        # -> ["SP_R","RP_L"]

    # 1) Bar chart：team vs league
    fig_bar = plot_performance_bar(team_id=TEAM_ID, player_type=player_type, groups=bar_groups)

    # 2) Radar charts：多選 → 多張雷達圖
    radar_cards = []
    for g in radar_groups:
        fig_radar = plot_performance_radar(player_type=player_type, group_code=g)
        radar_cards.append(
            card(
                dcc.Graph(
                    figure=fig_radar,
                    config={"displayModeBar": False}
                ),
                title=f"{TEAM_ID} {g} – Radar (PR values)",
            )
        )

    radar_grid = html.Div(
        radar_cards,
        style={
            "display": "grid",
            "gridTemplateColumns": "repeat(3, minmax(320px, 1fr))",
            "gap": "12px",
        },
    )

    return fig_bar, radar_grid

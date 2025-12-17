from dash import html, dcc

from src.containers import (
    overview_container,
    filter_bar,
    contribution_salary_container
)


def page_overview():
    return html.Div(
        [
            overview_container(),
        ],
        style={"padding": "16px"},
    )


def page_performance():
    return html.Div(
        [
            filter_bar(
                radio_id="player-type-radio",
                dropdown_id="sub-type-dropdown",
                button_id="apply-button",
                default_player_type="batter",
            ),

            html.Div(
                [
                    # Bar Chart 容器添加陰影
                    html.Div(
                        [
                            html.H5("Team vs League Performance", style={
                                "textAlign": "center",
                                "color": "#2c3e50",
                                "fontWeight": "600",
                                "marginBottom": "15px",
                                "fontSize": "18px"
                            }),
                            dcc.Graph(id="perf-bar-chart")
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
                    html.Div(id="perf-radar-grid"),
                ],
                style={"display": "flex", "flexDirection": "column", "gap": "14px"},
            ),
        ],
        style={"padding": "16px"},
    )


def page_contribution():
    return html.Div(
        [
            filter_bar(
                radio_id="player-type-radio",
                dropdown_id="sub-type-dropdown",
                button_id="apply-button",
                default_player_type="batter",
            ),
            contribution_salary_container()
        ],
        style={"padding": "16px"},
    )

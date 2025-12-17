from dash import dcc, html, Input, Output, callback

from src.page import (
    page_overview,
    page_performance,
    page_contribution
)


layout = html.Div(
    [
        # ===== Header with logo and tabs =====
        html.Div(
            [
                # Logo area (left)
                html.Div(
                    [
                        html.Img(
                            src="/assets/LAA_logo.jpeg",
                            style={"height": "80px"},
                            alt="LAA Logo"
                        ),
                        html.H3("LAA Dashboard", style={"margin": "0", "marginLeft": "10px"})
                    ],
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "flex": "1"
                    }
                ),

                # Navigation tabs (right)
                html.Div(
                    [
                        dcc.Tabs(
                            id="top-tabs",
                            value="overview",
                            children=[
                                dcc.Tab(label="Overview", value="overview"),
                                dcc.Tab(label="Performance", value="performance"),
                                dcc.Tab(label="Contribution", value="contribution"),
                            ],
                        ),
                    ],
                    style={"flex": "0 0 auto"}
                )
            ],
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "padding": "10px 20px",
                "borderBottom": "1px solid #ddd",
                "backgroundColor": "#f8f9fa"
            }
        ),

        # ===== Page content =====
        html.Div(id="page-content"),
    ],
    style={"padding": "0px"},
)


@callback(
    Output("page-content", "children"),
    Input("top-tabs", "value"),
)
def render_page(tab):
    if tab == "overview":
        return page_overview()
    if tab == "performance":
        return page_performance()
    if tab == "contribution":
        return page_contribution()
    return page_overview()

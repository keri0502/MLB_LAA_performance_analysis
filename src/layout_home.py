# src/layout_home.py
from dash import html

from containers import contribution_salary_container, radar_container


layout = html.Div(
    [
        html.H1(
            "MLB Team Weakness Diagnosis Dashboard",
            style={"textAlign": "center"},
        ),
        html.Hr(),
        
        contribution_salary_container(),

        radar_container(),
    ]
)

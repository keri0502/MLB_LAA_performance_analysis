# src/layout_home.py
from dash import html

from containers import contribution_salary_container


layout = html.Div(
    [
        html.H1(
            "MLB Team Weakness Diagnosis Dashboard",
            style={"textAlign": "center"},
        ),
        html.Hr(),
        # 未來可以在這裡放 Radio/Dropdown 控制「選哪一隊」
        contribution_salary_container(),
        # 之後：再把 radar / bar 的 container 放在下面
    ]
)

from typing import Literal, List

import plotly.express as px
import plotly.graph_objects as go

from sql_connector import query


TEAM_ID = "LAA"


def plot_contribution_salary_scatter(player_type: Literal["batter", "pitcher"], roles: List[str]) -> go.Figure:
    """
    畫選手貢獻和薪資的散布圖
    """
    # 取資料（分打者跟投手）
    roles_str = "','".join(roles)
    if player_type == "batter":
        # 篩選 team 跟 position
        pos_filter_sql = f"""
            SELECT playerID, `ops+`, salary
            FROM batter
            WHERE teamID = '{TEAM_ID}'
                AND POS IN ('{roles_str}')
        """
        y_axis = "ops+"

    elif player_type == "pitcher":
        # 篩選 team, position 跟 throws（position 跟 throws concat）
        pos_filter_sql = f"""
            SELECT playerID, `fip-`, salary
            FROM pitcher
            WHERE teamID = '{TEAM_ID}'
                AND POS || ' ' || throws IN ('{roles_str}')
        """
        y_axis = "fip-"

    salary_sql = f"""
        SELECT salary
        FROM {player_type}
    """
    # query db
    pos_filter_result = query(sql=pos_filter_sql)
    salary_result = query(sql=salary_sql)
    salary_median = salary_result['salary'].median()
    # 畫圖
    fig = px.scatter(
        data_frame=pos_filter_result,
        x="salary",
        y=y_axis,
        hover_data=["playerID"]
    )
    fig.add_shape(
        type="line",
        x0=min(pos_filter_result['salary'].min(), salary_median),
        y0=100,
        x1=max(pos_filter_result['salary'].max(), salary_median),
        y1=100,
        line=dict(width=2, dash="dash", color="black")
    )
    fig.add_annotation(
        x=pos_filter_result["salary"].max(),
        y=100,
        text=f"{y_axis.upper()} = 100",
        showarrow=False,
        yanchor="bottom",
        xanchor="right",
        font=dict(size=12, color="black")
    )
    fig.add_shape(
        type="line",
        y0=pos_filter_result[y_axis].min(),
        x0=salary_median,
        y1=pos_filter_result[y_axis].max(),
        x1=salary_median,
        line=dict(width=2, dash="dash", color="black")
    )
    fig.add_annotation(
        x=salary_median,
        y=pos_filter_result[y_axis].max(),
        text=f"Median salary = {salary_median:,.0f}",
        showarrow=False,
        yanchor="top",
        xanchor="left",
        font=dict(size=12, color="black")
    )

    return fig

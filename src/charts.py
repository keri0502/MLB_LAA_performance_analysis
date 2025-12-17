import operator
from typing import Literal, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.db_access import query, load_batter_raw, load_pitcher_raw
from src.constant import TEAM_ID, BATTER_RADAR_METRICS, PITCHER_RADAR_METRICS, TEAM_COLOR


def compute_batter_rates(df: pd.DataFrame) -> pd.DataFrame:
    """
    計算打者的各種率（AVG, OBP, SLG, BB_rate, K_rate）
    """
    df = df.copy()
    # 基本打擊指標計算
    df["1B"] = df["H"] - df["2B"] - df["3B"] - df["HR"]
    df["PA"] = df["AB"] + df["BB"] + df["HBP"] + df["SF"] + df["SH"]

    df["AVG"] = df["H"] / df["AB"].where(df["AB"] > 0, 1)
    df["OBP"] = (df["H"] + df["BB"] + df["HBP"]) / df["PA"].where(df["PA"] > 0, 1)
    df["SLG"] = (df["1B"] + 2 * df["2B"] + 3 * df["3B"] + 4 * df["HR"]) / df["AB"].where(df["AB"] > 0, 1)
    df["BB_rate"] = df["BB"] / df["PA"].where(df["PA"] > 0, 1)
    df["K_rate"] = df["SO"] / df["PA"].where(df["PA"] > 0, 1)
    df["OPS_plus"] = pd.to_numeric(df["OPS_plus"], errors="coerce")

    return df


def add_batter_pr(df: pd.DataFrame) -> pd.DataFrame:
    """
    計算打者各指標的百分等級排名（PR）
    """
    df = df.copy()
    league = df[df["PA"] >= 50].copy()  # 設門檻，避免樣本太小

    # 每個指標的 PR
    for col in ["AVG", "OBP", "SLG", "BB_rate", "OPS_plus"]:
        rank = league[col].rank(pct=True) * 100
        df[f"{col}_PR"] = rank.reindex(df.index)

    # K_rate 越低越好，所以反向
    rank_k = (1 - league["K_rate"].rank(pct=True)) * 100
    df["K_rate_PR"] = rank_k.reindex(df.index)

    return df


def compute_pitcher_rates(df: pd.DataFrame) -> pd.DataFrame:
    """
    計算投手的各種率（K9, BB9, H9, WHIP）
    """
    df = df.copy()

    # 將 IPouts 轉成局數
    df["IP"] = df["IPouts"] / 3.0

    # 避免除以 0 的情況：IP <= 0 時，把分母設成 1（結果不會被我們當成有意義的樣本）
    ip_safe = df["IP"].where(df["IP"] > 0, 1)

    # K/9, BB/9, H/9
    df["K9"] = df["SO"] * 9 / ip_safe
    df["BB9"] = df["BB"] * 9 / ip_safe
    df["H9"] = df["H"] * 9 / ip_safe

    # WHIP = (BB + H) / IP
    df["WHIP"] = (df["BB"] + df["H"]) / ip_safe

    # 確保 ERA、fip 是數值
    df["ERA"] = pd.to_numeric(df["ERA"], errors="coerce")
    df["fip"] = pd.to_numeric(df["fip"], errors="coerce")

    return df


def add_pitcher_pr(df: pd.DataFrame) -> pd.DataFrame:
    """
    計算投手各指標的百分等級排名（PR）
    """
    df = df.copy()

    # 設定聯盟樣本門檻：例如 IP >= 20
    league = df[df["IP"] >= 20].copy()

    # 「越高越好」的指標：K9
    for col in ["K9"]:
        rank = league[col].rank(pct=True) * 100  # 0~100
        df[f"{col}_PR"] = rank.reindex(df.index)

    # 「越低越好」的指標：ERA, FIP, WHIP, BB9, H9
    for col in ["ERA", "fip", "WHIP", "BB9", "H9"]:
        rank = (1 - league[col].rank(pct=True)) * 100  # 0~100，數值越好 PR 越高
        df[f"{col}_PR"] = rank.reindex(df.index)

    return df


def get_players(player_type: Literal["batter", "pitcher"], roles: List[str]) -> pd.DataFrame:
    """
    取得特定位置的球員數據
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

    elif player_type == "pitcher":
        # 篩選 team, position 跟 throws（position 跟 throws concat）
        pos_filter_sql = f"""
            SELECT playerID, `fip-`, salary
            FROM pitcher
            WHERE teamID = '{TEAM_ID}'
                AND POS || ' ' || throws IN ('{roles_str}')
        """

    # query db
    pos_filter_result = query(sql=pos_filter_sql)
    return pos_filter_result


def get_salary_median(player_type: Literal["batter", "pitcher"]) -> float:
    """
    取得該 player type 的薪水中位數
    """
    salary_sql = f"""
        SELECT salary
        FROM {player_type}
    """
    # query db
    salary_result = query(sql=salary_sql)
    salary_median = salary_result['salary'].median()
    return salary_median


def get_metric_name(player_type: Literal["batter", "pitcher"]) -> str:
    """
    根據 player type 決定要看什麼指標（ops+ or fip-）
    """
    metrics = {
        "batter": "ops+",
        "pitcher": "fip-"
    }
    metric = metrics[player_type]
    return metric


def plot_contribution_salary_scatter(player_type: Literal["batter", "pitcher"], roles: List[str]) -> go.Figure:
    """
    畫選手貢獻和薪資的散布圖
    """
    y_axis = get_metric_name(player_type=player_type)
    # 取資料
    players = get_players(
        player_type=player_type,
        roles=roles
    )
    salary_median = get_salary_median(player_type=player_type)
    
    # 創建四象限的分類
    players['quadrant'] = 'Other'
    median_performance = 100
    
    # 定義四象限
    high_sal_high_perf = (players['salary'] >= salary_median) & (players[y_axis] >= median_performance)
    high_sal_low_perf = (players['salary'] >= salary_median) & (players[y_axis] < median_performance)
    low_sal_high_perf = (players['salary'] < salary_median) & (players[y_axis] >= median_performance)
    low_sal_low_perf = (players['salary'] < salary_median) & (players[y_axis] < median_performance)
    
    players.loc[high_sal_high_perf, 'quadrant'] = 'Star Players'
    players.loc[high_sal_low_perf, 'quadrant'] = 'Overpaid'
    players.loc[low_sal_high_perf, 'quadrant'] = 'Value Players'
    players.loc[low_sal_low_perf, 'quadrant'] = 'Developing'
    
    # 自定義顏色
    color_map = {
        'Star Players': '#28a745',    # 綠色
        'Value Players': '#17a2b8',   # 青色
        'Overpaid': '#dc3545',        # 紅色
        'Developing': '#ffc107'       # 黃色
    }
    
    # 畫圖
    fig = px.scatter(
        data_frame=players,
        x="salary",
        y=y_axis,
        color='quadrant',
        color_discrete_map=color_map,
        hover_data=["playerID"],
        size_max=12,
        opacity=0.8
    )
    
    # 美化散點
    fig.update_traces(
        marker=dict(
            size=10,
            line=dict(width=1, color='white'),
            sizemode='diameter'
        )
    )

    # 水平線 (performance = 100)
    fig.add_shape(
        type="line",
        x0=min(players['salary'].min(), salary_median),
        y0=median_performance,
        x1=max(players['salary'].max(), salary_median),
        y1=median_performance,
        line=dict(width=2, dash="dash", color="rgba(128,128,128,0.7)")
    )
    
    # 垂直線 (median salary)
    fig.add_shape(
        type="line",
        y0=players[y_axis].min(),
        x0=salary_median,
        y1=players[y_axis].max(),
        x1=salary_median,
        line=dict(width=2, dash="dash", color="rgba(128,128,128,0.7)")
    )
    
    # 美化註解
    fig.add_annotation(
        x=players["salary"].max() * 0.95,
        y=median_performance + 5,
        text=f"League Average {y_axis.upper()} = 100",
        showarrow=False,
        yanchor="bottom",
        xanchor="right",
        font=dict(size=12, color="#2c3e50"),
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="#2c3e50",
        borderwidth=1
    )
    
    fig.add_annotation(
        x=salary_median + (players["salary"].max() - salary_median) * 0.1,
        y=players[y_axis].max() * 0.95,
        text=f"Median Salary<br>${salary_median:,.0f}",
        showarrow=False,
        yanchor="top",
        xanchor="left",
        font=dict(size=12, color="#2c3e50"),
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="#2c3e50",
        borderwidth=1
    )
    
    # 美化布局
    fig.update_layout(
        title={
            'text': f"{player_type.title()} Salary vs Performance Analysis",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#2c3e50'}
        },
        xaxis_title="Salary ($)",
        yaxis_title=f"{y_axis.upper()} (League Average = 100)",
        font=dict(family="Roboto, sans-serif", color="#2c3e50"),
        plot_bgcolor='rgba(248,249,250,0.8)',
        paper_bgcolor='white',
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(255,255,255,0.8)",
            borderwidth=0,
            title_text=""
        ),
        margin=dict(l=60, r=120, t=80, b=60)
    )
    
    # 美化軸
    fig.update_xaxes(
        gridcolor='rgba(128,128,128,0.2)',
        zerolinecolor='rgba(128,128,128,0.4)',
        tickformat='$,.0f'
    )
    fig.update_yaxes(
        gridcolor='rgba(128,128,128,0.2)',
        zerolinecolor='rgba(128,128,128,0.4)'
    )

    return fig


def get_player_list(player_type: Literal["batter", "pitcher"], roles: List[str], action: Literal["retain", "trade", "extend", "option"]) -> pd.DataFrame:
    """
    根據 action 及位置篩選球員
    """
    op_map = {
        "batter": operator.ge,  # >=
        "pitcher": operator.le  # <=
    }
    op = op_map[player_type]
    players = get_players(
        player_type=player_type,
        roles=roles
    )
    salary_median = get_salary_median(player_type=player_type)
    metric = get_metric_name(player_type=player_type)

    if action == "retain":
        condition = (players["salary"] >= salary_median) & (op(players[metric], 100))
    elif action == "trade":
        condition = (players["salary"] >= salary_median) & (~op(players[metric], 100))
    elif action == "extend":
        condition = (players["salary"] < salary_median) & (op(players[metric], 100))
    elif action == "option":
        condition = (players["salary"] < salary_median) & (~op(players[metric], 100))

    filtered_players = players[condition]
    filtered_players["salary"] = filtered_players["salary"].apply(lambda x: f"{x:,.0f}")
    filtered_players[metric] = filtered_players[metric].apply(lambda x: round(float(x), 2))
    return filtered_players


def build_laa_batter_group_profile(group_code: str) -> pd.Series | None:
    """
    回傳洛杉磯天使隊 (TEAM_ID) 某打者群組的 6 個 PR 平均值。
    """
    df_raw = load_batter_raw()
    df = compute_batter_rates(df_raw)
    df = add_batter_pr(df)

    # 只看 LAA
    df = df[df["teamID"] == TEAM_ID].copy()

    # 根據 group_code 過濾守位
    df = df[df["POS"] == group_code]

    if df.empty:
        return None

    profile = df[BATTER_RADAR_METRICS].mean()
    return profile


def build_laa_pitcher_group_profile(group_code: str) -> pd.Series | None:
    """
    回傳洛杉磯天使隊 (TEAM_ID) 某投手群組的 6 個 PR 平均值。

    group_code 可能是：
        "SP"    : 全隊先發投手
        "RP"    : 全隊中繼+後援投手
        "SP_L"  : 先發左投
        "SP_R"  : 先發右投
        "RP_L"  : 中繼+後援左投
        "RP_R"  : 中繼+後援右投
    """

    # 1. 撈 raw 投手資料 + 算 rate + PR
    df_raw = load_pitcher_raw()
    df = compute_pitcher_rates(df_raw)
    df = add_pitcher_pr(df)

    # 2. 只看 LAA
    df = df[df["teamID"] == TEAM_ID].copy()

    # 3. 根據 group_code 過濾 POS / throws
    if group_code == "SP":
        df = df[df["POS"] == "SP"]
    elif group_code == "RP":
        df = df[df["POS"] == "RP"]
    elif group_code == "SP_L":
        df = df[(df["POS"] == "SP") & (df["throws"] == "L")]
    elif group_code == "SP_R":
        df = df[(df["POS"] == "SP") & (df["throws"] == "R")]
    elif group_code == "RP_L":
        df = df[(df["POS"] == "RP") & (df["throws"] == "L")]
    elif group_code == "RP_R":
        df = df[(df["POS"] == "RP") & (df["throws"] == "R")]
    else:
        # 未知 group，直接回傳 None
        return None

    if df.empty:
        return None

    # 4. 計算這個群組在六個指標上的平均 PR
    profile = df[PITCHER_RADAR_METRICS].mean()

    return profile


def plot_laa_batter_radar(group_code: str) -> go.Figure:
    """
    畫出 LAA 在指定打者群組 (group_code) 的雷達圖。

    group_code:
        "C", "1B", "2B", "3B", "SS", "OF", "DH"
    """
    profile = build_laa_batter_group_profile(group_code)

    if profile is None:
        return go.Figure(
            layout_title_text=f"{TEAM_ID} {group_code} – No data for selected group"
        )

    metrics = profile.index.tolist()
    values = profile.values.tolist()

    # 雷達圖需要閉合
    metrics += [metrics[0]]
    values += [values[0]]

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=metrics,
            fill='toself',
            name=f"{TEAM_ID} {group_code}"
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=False,
    )

    return fig


def plot_laa_pitcher_radar(group_code: str) -> go.Figure:
    """
    畫出 LAA 在指定投手群組 (group_code) 的雷達圖。
    """
    profile = build_laa_pitcher_group_profile(group_code)

    if profile is None:
        return go.Figure(
            layout_title_text=f"{TEAM_ID} {group_code} – No data for selected pitcher group"
        )

    metrics = profile.index.tolist()
    values = profile.values.tolist()

    # 雷達圖首尾相接
    metrics += [metrics[0]]
    values += [values[0]]

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=metrics,
            fill="toself",
            name=f"{TEAM_ID} {group_code}",
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],  # PR 值 0~100
            )
        ),
        showlegend=False,
    )

    return fig


def build_laa_hitter_team_profile() -> pd.Series | None:
    df_raw = load_batter_raw()
    df = compute_batter_rates(df_raw)
    df = add_batter_pr(df)

    df = df[df["teamID"] == TEAM_ID].copy()
    df = df[df["POS"].isin(["C", "1B", "2B", "3B", "SS", "OF", "DH"])]

    if df.empty:
        return None

    return df[BATTER_RADAR_METRICS].mean()


def plot_laa_hitter_team_radar() -> go.Figure:
    profile = build_laa_hitter_team_profile()
    if profile is None:
        return go.Figure(layout_title_text=f"{TEAM_ID} Hitters – No data")

    metrics = profile.index.tolist()
    values = profile.values.tolist()
    metrics += [metrics[0]]
    values += [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=metrics, fill="toself", name=f"{TEAM_ID} Hitters"))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
    )
    return fig


def plot_overview_breakdown(team_id: str, group: str) -> go.Figure:
    """
    Overview breakdown: Team vs League
    group:
      - "SP" / "RP" : pitcher, breakdown by throws (R/L), metric = fip-
      - "H"         : batter, breakdown by POS, metric = ops+
    """

    if group in ["SP", "RP"]:
        df = query(f"""
            SELECT
                throws AS category,
                AVG(`fip-`) AS league_metric,
                AVG(CASE WHEN teamID = '{team_id}' THEN `fip-` END) AS team_metric
            FROM pitcher
            WHERE POS = '{group}'
              AND throws IN ('R','L')
            GROUP BY throws
            ORDER BY category
        """)
        metric_name = "FIP-"
        x_title = "Throws"

    else:  # group == "H"
        hitter_pos = ["1B", "2B", "3B", "SS", "OF", "C", "DH"]
        pos_str = "','".join(hitter_pos)

        df = query(f"""
            SELECT
                POS AS category,
                AVG(`ops+`) AS league_metric,
                AVG(CASE WHEN teamID = '{team_id}' THEN `ops+` END) AS team_metric
            FROM batter
            WHERE POS IN ('{pos_str}')
            GROUP BY POS
            ORDER BY category
        """)
        metric_name = "OPS+"
        x_title = "Position"

    # 本隊沒有資料的類別會是 NULL，先排除
    df = df.dropna(subset=["team_metric"])

    fig = go.Figure()
    fig.add_bar(
        x=df["category"],
        y=df["league_metric"],
        name="League Average"
    )
    fig.add_bar(
        x=df["category"],
        y=df["team_metric"],
        name="Team Average"
    )

    fig.update_layout(
        barmode="group",
        xaxis_title=x_title,
        yaxis_title=metric_name,
        legend_title="",
        margin=dict(l=40, r=20, t=40, b=40),
        title=f"{team_id} vs League – {group}",
    )

    return fig


def plot_performance_bar(team_id: str, player_type: str, groups: list[str]) -> go.Figure:
    """
    Bar chart for Performance page:
    - batter: compare OPS+ by POS (team vs league)
    - pitcher: compare FIP- by POS (SP/RP) (team vs league)
    groups: selected categories from dropdown
    """
    fig = go.Figure()

    team_color = TEAM_COLOR
    league_color = "#BDC3C7"
    if player_type == "batter":
        pos_str = "','".join(groups)
        df = query(f"""
            SELECT
                POS AS category,
                AVG(`ops+`) AS league_metric,
                AVG(CASE WHEN teamID = '{team_id}' THEN `ops+` END) AS team_metric
            FROM batter
            WHERE POS IN ('{pos_str}')
            GROUP BY POS
            ORDER BY category
        """).dropna(subset=["team_metric"])

        metric_name = "OPS+"

    else:
        roles_str = "','".join(groups)  # groups 會是 ["SP R","SP L","RP R","RP L"]

        df = query(f"""
            SELECT
                (POS || ' ' || throws) AS category,
                AVG(`fip-`) AS league_metric,
                AVG(CASE WHEN teamID = '{team_id}' THEN `fip-` END) AS team_metric
            FROM pitcher
            WHERE (POS || ' ' || throws) IN ('{roles_str}')
            GROUP BY (POS || ' ' || throws)
            ORDER BY category
        """).dropna(subset=["team_metric"])

        metric_name = "FIP-"

    x_title = "Position"

    fig.add_bar(x=df["category"], y=df["league_metric"], name="League Average", marker_color=league_color)
    fig.add_bar(x=df["category"], y=df["team_metric"], name="Team Average", marker_color=team_color)

    fig.update_layout(
        title={
            'text': f"{team_id} vs League Average",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 20, 'family': "Roboto, sans-serif"}
        },
        barmode="group",
        bargap=0.5,
        bargroupgap=0.15,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title=""
        ),
        xaxis=dict(
            title=x_title,
            showgrid=False,
            linecolor='rgba(0,0,0,0.2)',
            tickfont=dict(family='Roboto', size=12)
        ),
        yaxis=dict(
            title=metric_name,
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            gridwidth=1,
            zeroline=False
        ),
        margin=dict(l=40, r=20, t=60, b=40)
    )
    return fig


def plot_performance_radar(player_type: str, group_code: str) -> go.Figure:
    """
    Performance page 用的統一雷達入口（LAA only）
    player_type: "batter" / "pitcher"
    group_code:
      - batter: "C","1B","2B","3B","SS","OF","DH"
      - pitcher: "SP","RP"
    """
    if player_type == "batter":
        return plot_laa_batter_radar(group_code)

    if player_type == "pitcher":
        return plot_laa_pitcher_radar(group_code)

    return go.Figure(layout_title_text=f"Unknown player_type: {player_type}")


def get_overview_tiles(team_id: str) -> dict:
    """
    回傳 Overview tiles 需要的數值（從 DB 計算）：
    {
      "SP": {"metric": float, "diff": float},  # diff: 100 - fip-
      "RP": {"metric": float, "diff": float},
      "H":  {"metric": float, "diff": float},  # diff: ops+ - 100
    }
    """
    BASELINE = 100

    # SP (pitcher POS = SP), metric = avg(fip-)
    sp_df = query(f"""
        SELECT AVG(`fip-`) AS metric
        FROM pitcher
        WHERE teamID = '{team_id}' AND POS = 'SP'
    """)
    sp_metric = float(sp_df.iloc[0]["metric"]) if not sp_df.empty and sp_df.iloc[0]["metric"] is not None else None

    # RP (pitcher POS = RP), metric = avg(fip-)
    rp_df = query(f"""
        SELECT AVG(`fip-`) AS metric
        FROM pitcher
        WHERE teamID = '{team_id}' AND POS = 'RP'
    """)
    rp_metric = float(rp_df.iloc[0]["metric"]) if not rp_df.empty and rp_df.iloc[0]["metric"] is not None else None

    # H (batters), metric = avg(ops+)
    h_df = query(f"""
        SELECT AVG(`ops+`) AS metric
        FROM batter
        WHERE teamID = '{team_id}'
          AND POS IN ('C','1B','2B','3B','SS','OF','DH')
    """)
    h_metric = float(h_df.iloc[0]["metric"]) if not h_df.empty and h_df.iloc[0]["metric"] is not None else None

    # diffs (依你的定義)
    sp_diff = (BASELINE - sp_metric) if sp_metric is not None else None
    rp_diff = (BASELINE - rp_metric) if rp_metric is not None else None
    h_diff = (h_metric - BASELINE) if h_metric is not None else None

    return {
        "SP": {"metric": sp_metric, "diff": sp_diff},
        "RP": {"metric": rp_metric, "diff": rp_diff},
        "H": {"metric": h_metric, "diff": h_diff},
    }


def get_team_record(team_id: str) -> dict:
    """
    從 DB 的 team table 取戰績與排名
    回傳: {"name": str|None, "W": int|None, "L": int|None, "Rank": int|None}
    """
    df = query(f"""
        SELECT name, W, L, Rank
        FROM team
        WHERE teamID = '{team_id}'
        LIMIT 1
    """)

    if df.empty:
        return {"name": None, "W": None, "L": None, "Rank": None}

    row = df.iloc[0]
    return {
        "name": row["name"] if "name" in df.columns else None,
        "W": int(row["W"]) if row["W"] is not None else None,
        "L": int(row["L"]) if row["L"] is not None else None,
        "Rank": int(row["Rank"]) if row["Rank"] is not None else None,
    }

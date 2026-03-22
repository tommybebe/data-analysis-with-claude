# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "google-cloud-bigquery",
#     "pandas",
#     "plotly",
#     "db-dtypes",
# ]
# ///
"""
FitTrack 수익/세그먼트 인터랙티브 탐색 노트북

이 marimo 노트북은 두 가지 목적으로 설계되었습니다:

1. **분석 목적**: 플랫폼·구독 등급·유입 채널별 수익 및 참여도 세그먼트 분석
2. **교육 목적**: marimo의 반응형(reactive) UI 패턴 시연

   marimo는 Jupyter와 달리 셀 간 의존성을 자동으로 추적합니다.
   UI 위젯(드롭다운, 슬라이더)의 값이 바뀌면 의존하는 셀이 자동으로 재실행됩니다.
   에이전트가 생성하는 노트북에서도 이 패턴을 활용하면
   이해관계자가 파라미터를 직접 조정하며 분석을 탐색할 수 있습니다.

fct_daily_active_users 마트 모델의 풍부한 컬럼(subscription_tier, referral_source 등)을 활용합니다.

사용법:
  marimo edit examples/marimo-revenue-segments.py
"""

import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium")


@app.cell
def title():
    import marimo as mo

    mo.md(
        """
        # 💰 FitTrack 수익 세그먼트 탐색기

        **분석 기간**: 2026년 1분기 (2026-01-01 ~ 2026-03-31)

        ---

        ## 이 노트북 사용 방법

        아래 **필터 패널**에서 분석 파라미터를 조정하면,
        모든 차트와 지표가 **자동으로 업데이트**됩니다.

        이것이 marimo의 핵심 특징입니다:
        - 셀 간 의존성을 자동으로 추적 → UI 값 변경 시 연관 셀만 재실행
        - Jupyter와 달리 "위에서 아래로 재실행" 없이 필요한 셀만 갱신
        - 에이전트가 생성한 노트북을 이해관계자가 직접 탐색할 수 있음

        > **harness 관점**: 에이전트가 `stage:6-analyze` 단계에서 이 패턴으로 노트북을 생성하면,
        > 리뷰어가 PR에서 노트북을 열어 파라미터를 조정하며 결과를 직접 확인할 수 있습니다.
        """
    )
    return (mo,)


@app.cell
def config():
    # --- 프로젝트 설정 ---

    PROJECT_ID = "your-gcp-project-id"  # GCP 프로젝트 ID
    DATASET = "fittrack"  # BigQuery 데이터셋
    return DATASET, PROJECT_ID


@app.cell
def setup_client(PROJECT_ID):
    # --- BigQuery 클라이언트 ---

    from google.cloud import bigquery

    client = bigquery.Client(project=PROJECT_ID)
    return (client,)


@app.cell
def load_data(DATASET, PROJECT_ID, client, mo):
    # --- 데이터 로드 ---
    # fct_daily_active_users에서 분석에 필요한 컬럼을 모두 조회합니다.
    # 한 번 로드한 데이터는 메모리에 유지되어, 필터 변경 시 재조회 없이 활용됩니다.
    # (BigQuery on-demand 비용 절감 패턴)

    import pandas as pd

    query = f"""
    SELECT
        activity_date,
        platform,
        dau          AS dau_count,
        new_users,
        returning_users,
        total_sessions,
        total_events,
        avg_sessions_per_user,
        avg_events_per_user,
        total_revenue,
        avg_revenue_per_user,
        premium_dau,
        premium_ratio
    FROM `{PROJECT_ID}.{DATASET}.fct_daily_active_users`
    WHERE activity_date BETWEEN '2026-01-01' AND '2026-03-31'
    ORDER BY activity_date, platform
    """

    df_raw = client.query(query).to_dataframe()
    df_raw["activity_date"] = pd.to_datetime(df_raw["activity_date"])
    df_raw["month"] = df_raw["activity_date"].dt.strftime("%Y-%m")
    df_raw["week"] = df_raw["activity_date"].dt.to_period("W").apply(lambda p: str(p.start_time.date()))

    mo.md(
        f"""
        ### 📋 데이터 로드 완료

        - **기간**: {df_raw["activity_date"].min().strftime("%Y-%m-%d")} ~ {df_raw["activity_date"].max().strftime("%Y-%m-%d")}
        - **행 수**: {len(df_raw):,}행 (날짜 × 플랫폼)
        - **플랫폼**: {", ".join(sorted(df_raw["platform"].unique()))}

        > 💡 데이터는 한 번만 조회됩니다. 아래 필터를 변경해도 BigQuery 재조회 없이 분석됩니다.
        """
    )
    return (df_raw,)


@app.cell
def filter_panel(df_raw, mo):
    # --- 필터 패널 (반응형 UI) ---
    # marimo UI 위젯을 사용하여 인터랙티브 필터를 구성합니다.
    # 이 셀의 출력값(selected_platform, selected_metric, date_granularity)은
    # 아래 모든 차트 셀에서 참조됩니다.
    #
    # harness 설계 시사점:
    # 에이전트가 생성하는 노트북에서도 이 패턴을 적용하면
    # 이해관계자가 노트북을 직접 탐색할 수 있습니다.

    platform_options = ["전체"] + sorted(df_raw["platform"].unique().tolist())

    selected_platform = mo.ui.dropdown(
        options=platform_options,
        value="전체",
        label="플랫폼 필터",
    )

    selected_metric = mo.ui.dropdown(
        options={
            "DAU (일간 활성 사용자)": "dau_count",
            "총 수익 (원)": "total_revenue",
            "사용자당 평균 수익 (원)": "avg_revenue_per_user",
            "총 세션 수": "total_sessions",
            "사용자당 평균 세션": "avg_sessions_per_user",
            "프리미엄 사용자 수": "premium_dau",
            "프리미엄 비율": "premium_ratio",
        },
        value="DAU (일간 활성 사용자)",
        label="분석 지표",
    )

    date_granularity = mo.ui.radio(
        options={"일별": "daily", "주별": "weekly", "월별": "monthly"},
        value="일별",
        label="시간 단위",
    )

    mo.md("## 🎛️ 분석 파라미터")
    mo.hstack(
        [
            mo.vstack([mo.md("**플랫폼**"), selected_platform]),
            mo.vstack([mo.md("**지표**"), selected_metric]),
            mo.vstack([mo.md("**시간 단위**"), date_granularity]),
        ],
        gap=2,
        justify="start",
    )
    return (date_granularity, selected_metric, selected_platform)


@app.cell
def filter_data(date_granularity, df_raw, selected_metric, selected_platform, mo):
    # --- 필터 적용 ---
    # 위젯 값에 따라 데이터를 필터링하고 집계합니다.
    # selected_platform, selected_metric, date_granularity 중 하나라도 바뀌면
    # 이 셀과 이에 의존하는 모든 셀이 자동으로 재실행됩니다.

    import pandas as pd

    # 플랫폼 필터 적용
    platform_val = selected_platform.value
    if platform_val == "전체":
        df_filtered = df_raw.copy()
    else:
        df_filtered = df_raw[df_raw["platform"] == platform_val].copy()

    # 시간 단위에 따른 집계 키 결정
    granularity_val = date_granularity.value
    if granularity_val == "daily":
        time_col = "activity_date"
    elif granularity_val == "weekly":
        time_col = "week"
    else:
        time_col = "month"

    # 지표명 추출
    metric_col = selected_metric.value

    # 집계 방식 결정: 합산 지표 vs 평균 지표
    sum_metrics = {"dau_count", "total_revenue", "total_sessions", "premium_dau", "new_users", "returning_users"}
    avg_metrics = {"avg_revenue_per_user", "avg_sessions_per_user", "avg_events_per_user", "premium_ratio"}

    if metric_col in sum_metrics:
        df_agg = df_filtered.groupby(time_col)[metric_col].sum().reset_index()
    else:
        df_agg = df_filtered.groupby(time_col)[metric_col].mean().reset_index()

    # 시간 컬럼을 datetime으로 변환 (정렬 보장)
    if granularity_val != "daily":
        df_agg[time_col] = pd.to_datetime(df_agg[time_col])

    df_agg = df_agg.sort_values(time_col)

    # 현재 선택된 파라미터 표시
    mo.md(
        f"""
        > **현재 설정**: 플랫폼={platform_val} | 지표={selected_metric.value} | 시간={granularity_val}
        > | 데이터 포인트: {len(df_agg)}개
        """
    )
    return (df_agg, metric_col, time_col)


@app.cell
def chart_trend(date_granularity, df_agg, metric_col, mo, selected_metric, selected_platform, time_col):
    # --- 차트 1: 시계열 추이 ---
    # 선택된 지표의 시계열 추이를 라인 차트로 표시합니다.
    # 필터가 변경되면 이 차트가 자동으로 업데이트됩니다.

    import plotly.express as px
    import plotly.graph_objects as go

    # 이동평균 계산 (일별 데이터에서만 7일 이동평균 적용)
    df_plot = df_agg.copy()
    show_ma = date_granularity.value == "daily"
    if show_ma:
        df_plot["ma7"] = df_plot[metric_col].rolling(window=7, min_periods=1).mean()

    fig = go.Figure()

    # 원본 데이터
    fig.add_trace(
        go.Scatter(
            x=df_plot[time_col],
            y=df_plot[metric_col],
            mode="lines+markers" if len(df_plot) <= 30 else "lines",
            line=dict(color="#2196F3", width=1.5, dash="dot" if show_ma else "solid"),
            marker=dict(size=4),
            name=selected_metric.value,
            opacity=0.7 if show_ma else 1.0,
        )
    )

    # 7일 이동평균 (일별 데이터에서만)
    if show_ma:
        fig.add_trace(
            go.Scatter(
                x=df_plot[time_col],
                y=df_plot["ma7"],
                mode="lines",
                line=dict(color="#F44336", width=2.5),
                name="7일 이동평균",
            )
        )

    fig.update_layout(
        title=f"{selected_metric.value} 추이 — {selected_platform.value} ({date_granularity.value})",
        xaxis_title="기간",
        yaxis_title=selected_metric.value,
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )

    # 통계 요약
    avg_val = df_agg[metric_col].mean()
    max_val = df_agg[metric_col].max()
    min_val = df_agg[metric_col].min()

    mo.md(
        f"""
        ## 📈 1. {selected_metric.value} 추이

        | 통계 | 값 |
        |------|----|
        | 평균 | {avg_val:,.2f} |
        | 최대 | {max_val:,.2f} |
        | 최소 | {min_val:,.2f} |
        """
    )
    mo.ui.plotly(fig)
    return (fig,)


@app.cell
def chart_platform_comparison(df_raw, metric_col, mo, selected_metric):
    # --- 차트 2: 플랫폼별 비교 (바 차트) ---
    # 필터의 플랫폼 설정과 무관하게 항상 iOS vs Android를 비교합니다.
    # 이 차트는 selected_platform 위젯에 의존하지 않아 항상 전체 데이터를 표시합니다.

    import plotly.express as px
    import pandas as pd

    # 플랫폼별 월별 집계
    sum_metrics = {"dau_count", "total_revenue", "total_sessions", "premium_dau", "new_users"}
    if metric_col in sum_metrics:
        df_compare = (
            df_raw.groupby(["month", "platform"])[metric_col].sum().reset_index()
        )
    else:
        df_compare = (
            df_raw.groupby(["month", "platform"])[metric_col].mean().reset_index()
        )

    color_map = {"ios": "#007AFF", "android": "#34A853"}

    fig_compare = px.bar(
        df_compare,
        x="month",
        y=metric_col,
        color="platform",
        color_discrete_map=color_map,
        barmode="group",
        title=f"플랫폼별 {selected_metric.value} 비교 (월별)",
        labels={
            "month": "월",
            metric_col: selected_metric.value,
            "platform": "플랫폼",
        },
    )

    fig_compare.update_layout(
        template="plotly_white",
        legend_title="플랫폼",
    )

    # 플랫폼별 전체 기간 합계/평균
    if metric_col in sum_metrics:
        platform_summary = df_raw.groupby("platform")[metric_col].sum()
    else:
        platform_summary = df_raw.groupby("platform")[metric_col].mean()

    summary_rows = "\n".join([
        f"        | {p} | {v:,.2f} |"
        for p, v in platform_summary.items()
    ])

    mo.md(
        f"""
        ## 🆚 2. 플랫폼별 비교

        **전체 기간 {"합계" if metric_col in sum_metrics else "평균"}**:

        | 플랫폼 | {selected_metric.value} |
        |--------|---------|
{summary_rows}
        """
    )
    mo.ui.plotly(fig_compare)
    return (fig_compare,)


@app.cell
def chart_premium_breakdown(df_raw, mo):
    # --- 차트 3: 프리미엄 전환율 추이 ---
    # 구독 등급 관련 지표를 고정으로 표시합니다.
    # 이 차트는 필터 위젯에 의존하지 않아 항상 전체 데이터를 기반으로 합니다.

    import plotly.express as px
    import pandas as pd

    # 플랫폼별 월별 프리미엄 비율
    df_premium = (
        df_raw.groupby(["month", "platform"])
        .agg(
            total_dau=("dau_count", "sum"),
            total_premium=("premium_dau", "sum"),
        )
        .reset_index()
    )
    df_premium["premium_pct"] = (
        df_premium["total_premium"] / df_premium["total_dau"] * 100
    ).round(1)

    color_map = {"ios": "#007AFF", "android": "#34A853"}

    fig_premium = px.line(
        df_premium,
        x="month",
        y="premium_pct",
        color="platform",
        color_discrete_map=color_map,
        markers=True,
        title="월별 프리미엄 사용자 비율 추이 (플랫폼별)",
        labels={
            "month": "월",
            "premium_pct": "프리미엄 비율 (%)",
            "platform": "플랫폼",
        },
    )

    fig_premium.update_layout(
        yaxis=dict(ticksuffix="%", range=[0, 100]),
        template="plotly_white",
        hovermode="x unified",
    )

    # 최신 월의 프리미엄 비율
    latest_month = df_premium["month"].max()
    latest_premium = df_premium[df_premium["month"] == latest_month].set_index("platform")["premium_pct"]

    mo.md(
        f"""
        ## 👑 3. 프리미엄 전환율 추이

        **{latest_month} 현재 프리미엄 비율**:
        - iOS: {latest_premium.get("ios", "N/A")}%
        - Android: {latest_premium.get("android", "N/A")}%

        > 프리미엄 사용자(premium + premium_plus)는 수익의 핵심 기반입니다.
        """
    )
    mo.ui.plotly(fig_premium)
    return (fig_premium,)


@app.cell
def harness_note(mo):
    # --- harness 패턴 설명 ---
    # 이 노트북은 교육 목적으로 harness 엔지니어링 패턴을 시연합니다.

    mo.md(
        """
        ---

        ## 🔧 harness 엔지니어링 패턴 요약

        이 노트북이 시연하는 주요 패턴:

        ### 1. 데이터를 한 번만 로드 (비용 절감)
        ```python
        # load_data 셀: 전체 기간 데이터를 한 번 로드
        df_raw = client.query(query).to_dataframe()

        # filter_data 셀: 메모리에서 필터링 (BigQuery 재조회 없음)
        df_filtered = df_raw[df_raw["platform"] == platform_val]
        ```

        ### 2. UI 위젯 의존성으로 반응형 탐색
        ```python
        # filter_panel 셀: 위젯 정의
        selected_platform = mo.ui.dropdown(...)

        # filter_data 셀: 위젯 값에 의존 → 자동 재실행
        def filter_data(selected_platform, df_raw, ...):
            if selected_platform.value == "전체":
                ...
        ```

        ### 3. 고정 차트 vs 반응형 차트 분리
        - **반응형**: `chart_trend` → 필터 위젯에 의존, 파라미터 변경 시 업데이트
        - **고정**: `chart_premium_breakdown` → 필터 무관, 항상 전체 데이터 표시

        ### 4. 에이전트 생성 노트북에서의 활용
        에이전트가 `stage:6-analyze`에서 이 패턴으로 노트북을 생성하면:
        - 이해관계자가 PR에서 노트북을 열어 파라미터 직접 조정 가능
        - 분석가가 추가 탐색을 수행할 수 있는 기반 제공
        - 정적 리포트(HTML/PDF)와 함께 인터랙티브 탐색 도구로 활용 가능
        """
    )
    return


if __name__ == "__main__":
    app.run()

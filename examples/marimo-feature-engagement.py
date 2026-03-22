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
FitTrack 기능별 참여도 인터랙티브 분석 노트북

이 marimo 노트북은 FitTrack 앱의 핵심 기능(운동, 목표 설정, 소셜 공유, 구매)별
참여도와 채택률을 인터랙티브하게 탐색합니다.

harness 통합 패턴을 함께 시연합니다:
- 에이전트가 설정하는 config 셀 (ANALYSIS_CONFIG)
- 비용 효율적 데이터 로드 (한 번 쿼리, 메모리 내 필터링)
- 완료 증거 생성 (evidence/ 디렉토리)
- mo.stop()을 활용한 조건부 실행

dbt mart 모델 fct_feature_engagement를 사용합니다.

사용법:
  marimo edit examples/marimo-feature-engagement.py
  marimo run examples/marimo-feature-engagement.py

HTML 내보내기:
  marimo export html examples/marimo-feature-engagement.py -o reports/feature-engagement-report.html
"""

import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium")


@app.cell
def title():
    import marimo as mo

    mo.md(
        """
        # ⚙️ FitTrack 기능별 참여도 분석

        **분석 기간**: 2026년 1분기 (2026-01-01 ~ 2026-03-31)
        **분석 대상**: 운동, 목표 설정, 소셜 공유, 구매/결제 기능

        ---

        ## 분석 개요

        기능별 채택률(Adoption Rate)과 완료율(Completion Rate)을 추적하여
        어떤 기능이 사용자 참여를 이끌어내는지, 어디에서 이탈이 발생하는지 파악합니다.

        ### 메트릭 정의
        - **채택률 (Adoption Rate)**: 당일 DAU 중 해당 기능을 1회 이상 사용한 사용자 비율
        - **완료율 (Completion Rate)**: 기능 시작 건수 대비 완료 건수 비율 (Funnel drop-off)
        - **목표 달성률 (Achievement Rate)**: 설정된 목표 중 실제 달성된 비율

        ### harness 통합 안내

        > 이 노트북은 `stage:6-analyze` 단계에서 에이전트가 생성하는 형태를 시연합니다.
        > 에이전트는 아래 `ANALYSIS_CONFIG` 딕셔너리의 값을 이슈 파싱 결과에 따라 자동 설정합니다.
        > 나머지 셀은 변경하지 않고, config만 수정하면 전체 분석이 업데이트됩니다.
        """
    )
    return (mo,)


@app.cell
def config():
    # --- 분석 설정 (에이전트가 자동 설정하는 셀) ---
    # harness의 stage:6-analyze 단계에서 에이전트가 이슈 파싱 결과를 기반으로
    # 이 딕셔너리의 값을 수정합니다. 다른 셀은 그대로 유지됩니다.

    ANALYSIS_CONFIG = {
        "project_id": "your-gcp-project-id",   # GCP 프로젝트 ID
        "dataset": "fittrack",                   # BigQuery 데이터셋
        "start_date": "2026-01-01",              # 분석 시작일
        "end_date": "2026-03-31",                # 분석 종료일
        # 분석 초점: "all" | "workout" | "goal" | "social" | "purchase"
        "focus_feature": "all",
        # 완료 증거 파일 경로 (harness가 검증에 사용)
        "evidence_output_path": "evidence/feature-engagement-evidence.json",
    }
    return (ANALYSIS_CONFIG,)


@app.cell
def setup_bigquery(ANALYSIS_CONFIG):
    # --- BigQuery 클라이언트 초기화 ---
    # 로컬: gcloud auth application-default login
    # CI/CD: GOOGLE_APPLICATION_CREDENTIALS 환경변수 (서비스 계정 JSON)

    from google.cloud import bigquery

    bq_client = bigquery.Client(project=ANALYSIS_CONFIG["project_id"])

    # 연결 확인
    try:
        bq_client.get_dataset(ANALYSIS_CONFIG["dataset"])
        print("✅ BigQuery 연결 성공")
    except Exception as e:
        print(f"❌ BigQuery 연결 실패: {e}")

    return (bq_client,)


@app.cell
def load_feature_data(ANALYSIS_CONFIG, bq_client, mo):
    # --- 기능 참여도 데이터 로드 ---
    # fct_feature_engagement에서 전체 기간 데이터를 한 번에 로드합니다.
    # 이후 인터랙티브 필터는 메모리 내에서 처리하여 BigQuery 재조회를 최소화합니다.
    # (on-demand 비용 절감 패턴)

    import pandas as pd

    feature_query = f"""
    SELECT
        activity_date,
        dau,
        -- 운동 기능 지표
        workout_users,
        workout_completers,
        total_workout_starts,
        total_workout_completes,
        workout_adoption_rate,
        workout_completion_rate,
        -- 목표 기능 지표
        goal_setters,
        goal_achievers,
        total_goals_set,
        total_goals_achieved,
        goal_adoption_rate,
        goal_achievement_rate,
        -- 소셜 기능 지표
        social_sharers,
        total_shares,
        social_adoption_rate,
        avg_shares_per_sharer,
        -- 구매/결제 지표
        purchasers,
        total_purchases,
        total_revenue_krw,
        purchase_conversion_rate,
        revenue_per_purchaser_krw
    FROM `{ANALYSIS_CONFIG["project_id"]}.{ANALYSIS_CONFIG["dataset"]}.fct_feature_engagement`
    WHERE activity_date BETWEEN '{ANALYSIS_CONFIG["start_date"]}' AND '{ANALYSIS_CONFIG["end_date"]}'
    ORDER BY activity_date
    """

    df_features = bq_client.query(feature_query).to_dataframe()

    # 데이터 전처리
    df_features["activity_date"] = pd.to_datetime(df_features["activity_date"])
    df_features["week"] = df_features["activity_date"].dt.to_period("W").apply(
        lambda p: str(p.start_time.date())
    )
    df_features["month"] = df_features["activity_date"].dt.strftime("%Y-%m")

    # 비율 컬럼을 퍼센트로 변환 (시각화용)
    rate_cols = [
        "workout_adoption_rate", "workout_completion_rate",
        "goal_adoption_rate", "goal_achievement_rate",
        "social_adoption_rate", "purchase_conversion_rate",
    ]
    for col in rate_cols:
        df_features[f"{col}_pct"] = (df_features[col] * 100).round(2)

    mo.md(
        f"""
        ### 📋 기능 참여도 데이터 로드 완료

        - **기간**: {df_features["activity_date"].min().strftime("%Y-%m-%d")} ~
          {df_features["activity_date"].max().strftime("%Y-%m-%d")}
        - **행 수**: {len(df_features):,}행 (일별)
        - **평균 DAU**: {df_features["dau"].mean():,.0f}명

        > 💡 데이터는 한 번만 조회됩니다. 아래 필터 변경 시 BigQuery 재조회 없이 분석됩니다.
        """
    )
    return (df_features,)


@app.cell
def filter_panel(mo):
    # --- 인터랙티브 필터 패널 ---
    # marimo의 반응형 UI를 활용합니다.
    # 이 셀의 위젯 값이 변경되면 의존하는 모든 셀이 자동으로 재실행됩니다.
    # harness가 생성한 노트북을 이해관계자가 직접 탐색할 때 유용합니다.

    selected_granularity = mo.ui.radio(
        options={"일별": "daily", "주별": "weekly", "월별": "monthly"},
        value="주별",
        label="시간 단위",
    )

    selected_features = mo.ui.multiselect(
        options={
            "운동 (Workout)": "workout",
            "목표 설정 (Goal)": "goal",
            "소셜 공유 (Social)": "social",
            "구매/결제 (Purchase)": "purchase",
        },
        value=["운동 (Workout)", "목표 설정 (Goal)", "소셜 공유 (Social)"],
        label="분석 기능 선택",
    )

    selected_metric_type = mo.ui.dropdown(
        options={
            "채택률 (Adoption Rate %)": "adoption",
            "완료율/달성률 (Completion Rate %)": "completion",
            "사용자 수 (Raw Count)": "users",
        },
        value="채택률 (Adoption Rate %)",
        label="지표 유형",
    )

    mo.md("## 🎛️ 분석 파라미터")
    mo.hstack(
        [
            mo.vstack([mo.md("**시간 단위**"), selected_granularity]),
            mo.vstack([mo.md("**기능 선택**"), selected_features]),
            mo.vstack([mo.md("**지표 유형**"), selected_metric_type]),
        ],
        gap=2,
        justify="start",
    )
    return (selected_features, selected_granularity, selected_metric_type)


@app.cell
def prepare_chart_data(
    df_features,
    selected_features,
    selected_granularity,
    selected_metric_type,
    mo,
):
    # --- 필터 적용 및 집계 ---
    # 위젯 값에 따라 시간 단위와 지표를 결정합니다.
    # marimo는 이 셀이 의존하는 위젯이 변경될 때 자동으로 재실행합니다.

    import pandas as pd

    granularity = selected_granularity.value
    metric_type = selected_metric_type.value

    # 시간 단위별 집계 키
    if granularity == "daily":
        time_col = "activity_date"
        df_agg = df_features.copy()
    elif granularity == "weekly":
        time_col = "week"
        # 주별 집계: 채택률은 평균, 사용자 수는 합산
        df_agg = df_features.groupby("week").agg(
            dau=("dau", "mean"),
            workout_users=("workout_users", "mean"),
            workout_completers=("workout_completers", "mean"),
            total_workout_starts=("total_workout_starts", "sum"),
            total_workout_completes=("total_workout_completes", "sum"),
            workout_adoption_rate_pct=("workout_adoption_rate_pct", "mean"),
            workout_completion_rate_pct=("workout_completion_rate_pct", "mean"),
            goal_setters=("goal_setters", "mean"),
            goal_achievers=("goal_achievers", "mean"),
            total_goals_set=("total_goals_set", "sum"),
            total_goals_achieved=("total_goals_achieved", "sum"),
            goal_adoption_rate_pct=("goal_adoption_rate_pct", "mean"),
            goal_achievement_rate_pct=("goal_achievement_rate_pct", "mean"),
            social_sharers=("social_sharers", "mean"),
            total_shares=("total_shares", "sum"),
            social_adoption_rate_pct=("social_adoption_rate_pct", "mean"),
            purchasers=("purchasers", "mean"),
            total_purchases=("total_purchases", "sum"),
            total_revenue_krw=("total_revenue_krw", "sum"),
            purchase_conversion_rate_pct=("purchase_conversion_rate_pct", "mean"),
        ).reset_index()
        df_agg[time_col] = pd.to_datetime(df_agg[time_col])
    else:
        time_col = "month"
        df_agg = df_features.groupby("month").agg(
            dau=("dau", "mean"),
            workout_users=("workout_users", "mean"),
            workout_completers=("workout_completers", "mean"),
            total_workout_starts=("total_workout_starts", "sum"),
            total_workout_completes=("total_workout_completes", "sum"),
            workout_adoption_rate_pct=("workout_adoption_rate_pct", "mean"),
            workout_completion_rate_pct=("workout_completion_rate_pct", "mean"),
            goal_setters=("goal_setters", "mean"),
            goal_achievers=("goal_achievers", "mean"),
            total_goals_set=("total_goals_set", "sum"),
            total_goals_achieved=("total_goals_achieved", "sum"),
            goal_adoption_rate_pct=("goal_adoption_rate_pct", "mean"),
            goal_achievement_rate_pct=("goal_achievement_rate_pct", "mean"),
            social_sharers=("social_sharers", "mean"),
            total_shares=("total_shares", "sum"),
            social_adoption_rate_pct=("social_adoption_rate_pct", "mean"),
            purchasers=("purchasers", "mean"),
            total_purchases=("total_purchases", "sum"),
            total_revenue_krw=("total_revenue_krw", "sum"),
            purchase_conversion_rate_pct=("purchase_conversion_rate_pct", "mean"),
        ).reset_index()

    # 선택된 기능과 지표 유형에 따라 표시할 지표 결정
    feature_metric_map = {
        "workout": {
            "adoption": ("workout_adoption_rate_pct", "운동 채택률 (%)"),
            "completion": ("workout_completion_rate_pct", "운동 완료율 (%)"),
            "users": ("workout_users", "운동 사용자 수"),
        },
        "goal": {
            "adoption": ("goal_adoption_rate_pct", "목표 채택률 (%)"),
            "completion": ("goal_achievement_rate_pct", "목표 달성률 (%)"),
            "users": ("goal_setters", "목표 설정 사용자 수"),
        },
        "social": {
            "adoption": ("social_adoption_rate_pct", "소셜 채택률 (%)"),
            "completion": ("social_adoption_rate_pct", "소셜 채택률 (%)"),  # 소셜은 completion 없음
            "users": ("social_sharers", "소셜 공유 사용자 수"),
        },
        "purchase": {
            "adoption": ("purchase_conversion_rate_pct", "결제 전환율 (%)"),
            "completion": ("purchase_conversion_rate_pct", "결제 전환율 (%)"),
            "users": ("purchasers", "구매자 수"),
        },
    }

    # 기능 코드 매핑
    feature_code_map = {
        "운동 (Workout)": "workout",
        "목표 설정 (Goal)": "goal",
        "소셜 공유 (Social)": "social",
        "구매/결제 (Purchase)": "purchase",
    }

    selected_feature_codes = [
        feature_code_map[f] for f in selected_features.value
        if f in feature_code_map
    ]

    mo.md(
        f"""
        > **현재 설정**: {granularity} | {selected_metric_type.value} | 기능: {", ".join(selected_features.value) if selected_features.value else "없음"}
        """
    )

    return (df_agg, feature_metric_map, selected_feature_codes, time_col)


@app.cell
def chart_feature_trends(
    df_agg,
    feature_metric_map,
    mo,
    selected_feature_codes,
    selected_granularity,
    selected_metric_type,
    time_col,
):
    # --- 차트 1: 기능별 지표 추이 비교 ---
    # 선택된 기능들의 채택률/완료율 추이를 라인 차트로 비교합니다.
    # 필터 변경 시 자동으로 업데이트됩니다.

    import plotly.graph_objects as go
    import marimo as mo

    # 기능별 색상
    feature_colors = {
        "workout": "#2196F3",   # 파랑 — 운동
        "goal": "#4CAF50",      # 초록 — 목표
        "social": "#FF9800",    # 주황 — 소셜
        "purchase": "#9C27B0",  # 보라 — 구매
    }

    feature_names = {
        "workout": "운동",
        "goal": "목표 설정",
        "social": "소셜 공유",
        "purchase": "구매/결제",
    }

    metric_type = selected_metric_type.value

    if not selected_feature_codes:
        mo.stop(True, mo.md("⚠️ 분석 기능을 1개 이상 선택하세요."))

    fig = go.Figure()

    for feature_code in selected_feature_codes:
        if feature_code not in feature_metric_map:
            continue

        col_name, col_label = feature_metric_map[feature_code][metric_type]

        if col_name not in df_agg.columns:
            continue

        # 7일/7포인트 이동평균 (일별 데이터에서만 적용)
        y_values = df_agg[col_name]
        show_ma = selected_granularity.value == "daily"
        if show_ma:
            y_ma = y_values.rolling(window=7, min_periods=1).mean()
        else:
            y_ma = y_values

        color = feature_colors.get(feature_code, "#666")
        name = feature_names.get(feature_code, feature_code)

        # 원본 데이터 (투명, 일별만)
        if show_ma:
            fig.add_trace(
                go.Scatter(
                    x=df_agg[time_col],
                    y=y_values,
                    mode="lines",
                    line=dict(color=color, width=1, dash="dot"),
                    opacity=0.35,
                    name=f"{name} (일별)",
                    showlegend=False,
                )
            )

        # 이동평균 또는 집계 값 (굵은 선)
        fig.add_trace(
            go.Scatter(
                x=df_agg[time_col],
                y=y_ma,
                mode="lines+markers" if selected_granularity.value != "daily" else "lines",
                line=dict(color=color, width=2.5),
                marker=dict(size=6),
                name=f"{name} {'(7일 이동평균)' if show_ma else ''}",
            )
        )

    # Y축 레이블 설정
    y_title = "비율 (%)" if metric_type in ("adoption", "completion") else "사용자 수"

    fig.update_layout(
        title=f"기능별 {selected_metric_type.value} 추이 ({selected_granularity.value})",
        xaxis_title="기간",
        yaxis_title=y_title,
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )

    if metric_type in ("adoption", "completion"):
        fig.update_layout(yaxis=dict(ticksuffix="%"))

    mo.md("## 📈 1. 기능별 지표 추이")
    mo.ui.plotly(fig)
    return (fig,)


@app.cell
def chart_funnel(df_features, mo):
    # --- 차트 2: 운동 기능 퍼널 분석 (Funnel Chart) ---
    # 전체 기간 합산 기준으로 운동 시작 → 완료 퍼널을 시각화합니다.
    # 어느 단계에서 이탈이 가장 많이 발생하는지 파악합니다.
    # 이 차트는 필터 위젯에 독립적입니다 (전체 기간 고정 표시).

    import plotly.graph_objects as go

    # 전체 기간 합산
    total_dau = int(df_features["dau"].sum())
    total_workout_starters = int(df_features["workout_users"].sum())
    total_workout_completers = int(df_features["workout_completers"].sum())
    total_goal_setters = int(df_features["goal_setters"].sum())
    total_goal_achievers = int(df_features["goal_achievers"].sum())

    # 전환율 계산
    workout_adoption_pct = total_workout_starters / total_dau * 100 if total_dau > 0 else 0
    workout_completion_pct = total_workout_completers / total_workout_starters * 100 if total_workout_starters > 0 else 0
    goal_adoption_pct = total_goal_setters / total_dau * 100 if total_dau > 0 else 0
    goal_achievement_pct = total_goal_achievers / total_goal_setters * 100 if total_goal_setters > 0 else 0

    fig_funnel = go.Figure()

    # 운동 퍼널
    fig_funnel.add_trace(
        go.Funnel(
            name="운동 기능",
            y=["전체 DAU (합산)", "운동 시작 사용자", "운동 완료 사용자"],
            x=[total_dau, total_workout_starters, total_workout_completers],
            textposition="inside",
            textinfo="value+percent initial",
            marker=dict(color=["#E3F2FD", "#1976D2", "#0D47A1"]),
            connector=dict(line=dict(color="#90CAF9", width=2)),
        )
    )

    fig_funnel.update_layout(
        title={
            "text": "운동 기능 참여 퍼널 (전체 기간 합산)",
            "x": 0.5,
            "xanchor": "center",
        },
        template="plotly_white",
        height=350,
    )

    mo.md(
        f"""
        ## 🔽 2. 운동 기능 참여 퍼널

        | 단계 | 사용자 수 | 전환율 |
        |------|-----------|--------|
        | 전체 DAU (합산) | {total_dau:,} | — |
        | 운동 시작 | {total_workout_starters:,} | DAU 대비 **{workout_adoption_pct:.1f}%** |
        | 운동 완료 | {total_workout_completers:,} | 시작 대비 **{workout_completion_pct:.1f}%** |

        > **해석**: 운동 완료율이 낮다면 운동 프로그램 난이도나 길이를 재검토하세요.
        """
    )
    mo.ui.plotly(fig_funnel)
    return (
        fig_funnel,
        goal_achievement_pct,
        goal_adoption_pct,
        total_goal_achievers,
        total_goal_setters,
        workout_adoption_pct,
        workout_completion_pct,
    )


@app.cell
def chart_adoption_heatmap(df_features, mo):
    # --- 차트 3: 기능 채택률 비교 히트맵 ---
    # 월별 기능 채택률을 히트맵으로 시각화합니다.
    # 어떤 기능이 어떤 시기에 상대적으로 높은 채택률을 보이는지 한눈에 파악합니다.

    import pandas as pd
    import plotly.graph_objects as go
    import numpy as np

    # 월별 평균 채택률 집계
    df_monthly = df_features.groupby("month").agg(
        workout_adoption=("workout_adoption_rate_pct", "mean"),
        goal_adoption=("goal_adoption_rate_pct", "mean"),
        social_adoption=("social_adoption_rate_pct", "mean"),
        purchase_conversion=("purchase_conversion_rate_pct", "mean"),
    ).reset_index()

    # 히트맵 데이터 구성
    features = ["운동 채택률", "목표 채택률", "소셜 채택률", "결제 전환율"]
    months = df_monthly["month"].tolist()

    z_data = [
        df_monthly["workout_adoption"].round(1).tolist(),
        df_monthly["goal_adoption"].round(1).tolist(),
        df_monthly["social_adoption"].round(1).tolist(),
        df_monthly["purchase_conversion"].round(1).tolist(),
    ]

    text_data = [
        [f"{v:.1f}%" for v in row]
        for row in z_data
    ]

    fig_heatmap = go.Figure(
        data=go.Heatmap(
            z=z_data,
            x=months,
            y=features,
            text=text_data,
            texttemplate="%{text}",
            textfont={"size": 12},
            colorscale="Blues",
            colorbar=dict(
                title="채택률 (%)",
                ticksuffix="%",
            ),
            hovertemplate=(
                "기능: %{y}<br>"
                "월: %{x}<br>"
                "채택률: %{z:.1f}%<extra></extra>"
            ),
        )
    )

    fig_heatmap.update_layout(
        title={
            "text": "기능별 채택률 월별 히트맵",
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis_title="월",
        yaxis_title="기능",
        template="plotly_white",
        height=300,
    )

    mo.md("## 🗓️ 3. 기능별 채택률 월별 비교")
    mo.ui.plotly(fig_heatmap)
    return (df_monthly, fig_heatmap)


@app.cell
def summary_and_evidence(
    ANALYSIS_CONFIG,
    df_features,
    df_monthly,
    goal_achievement_pct,
    goal_adoption_pct,
    mo,
    workout_adoption_pct,
    workout_completion_pct,
):
    # --- 주요 발견 요약 및 완료 증거 생성 ---
    # 분석 결과를 요약하고 harness가 검증할 수 있는 evidence JSON을 생성합니다.
    # evidence/ 디렉토리의 JSON 파일은 GitHub Actions의 stage:7-report에서
    # 분석 완료 여부 기계적 검증에 사용됩니다.

    import json
    import os
    import pandas as pd

    # 핵심 지표 산출
    avg_workout_adoption = df_features["workout_adoption_rate_pct"].mean()
    avg_social_adoption = df_features["social_adoption_rate_pct"].mean()
    avg_purchase_conversion = df_features["purchase_conversion_rate_pct"].mean()

    # 월별 추이: 가장 최근 월 vs 첫 번째 월 비교
    if len(df_monthly) >= 2:
        workout_trend = df_monthly["workout_adoption"].iloc[-1] - df_monthly["workout_adoption"].iloc[0]
        social_trend = df_monthly["social_adoption"].iloc[-1] - df_monthly["social_adoption"].iloc[0]
    else:
        workout_trend = 0.0
        social_trend = 0.0

    # 완료 증거 딕셔너리 (harness가 검증하는 아티팩트)
    evidence = {
        "analysis_type": "feature_engagement",
        "period": {
            "start": ANALYSIS_CONFIG["start_date"],
            "end": ANALYSIS_CONFIG["end_date"],
        },
        "key_metrics": {
            "avg_workout_adoption_pct": round(avg_workout_adoption, 2),
            "workout_completion_rate_pct": round(workout_completion_pct, 2),
            "avg_goal_adoption_pct": round(goal_adoption_pct, 2),
            "goal_achievement_rate_pct": round(goal_achievement_pct, 2),
            "avg_social_adoption_pct": round(avg_social_adoption, 2),
            "avg_purchase_conversion_pct": round(avg_purchase_conversion, 2),
        },
        "trends": {
            "workout_adoption_change_pct": round(workout_trend, 2),
            "social_adoption_change_pct": round(social_trend, 2),
        },
        "generated_at": pd.Timestamp.now().isoformat(),
    }

    # evidence 파일 저장 (CI/CD 환경에서 검증용)
    evidence_path = ANALYSIS_CONFIG["evidence_output_path"]
    try:
        os.makedirs(os.path.dirname(evidence_path), exist_ok=True)
        with open(evidence_path, "w", encoding="utf-8") as f:
            json.dump(evidence, f, ensure_ascii=False, indent=2)
        evidence_status = f"✅ 완료 증거 저장: `{evidence_path}`"
    except Exception as e:
        evidence_status = f"⚠️ 증거 저장 건너뜀 (로컬 경로 미생성): {e}"

    mo.md(
        f"""
        ---

        ## 🔍 주요 발견 요약

        1. **운동 기능 채택률**: 평균 **{avg_workout_adoption:.1f}%** 의 DAU가 매일 운동 기능을 사용합니다.
           운동 완료율은 **{workout_completion_pct:.1f}%**로,
           {"목표 수준(80%) 이상입니다" if workout_completion_pct >= 80 else "개선 여지가 있습니다 (목표: 80% 이상)"}.

        2. **목표 설정 기능**: 채택률 **{goal_adoption_pct:.1f}%**, 달성률 **{goal_achievement_pct:.1f}%**.
           목표 달성이 사용자 재참여와 연결되므로 달성률 향상이 리텐션에 직결됩니다.

        3. **소셜 공유 기능**: 채택률 **{avg_social_adoption:.1f}%**.
           {"소셜 공유가 활발하여 바이럴 효과 기대 가능합니다" if avg_social_adoption > 10 else "소셜 채택률이 낮아 공유 기능 UX 개선이 필요합니다"}.

        4. **결제 전환율**: 일평균 **{avg_purchase_conversion:.2f}%**.
           {"B2C 모바일 앱 평균(1-2%) 대비 양호한 수준입니다" if avg_purchase_conversion >= 1 else "결제 전환 유도를 강화할 여지가 있습니다"}.

        5. **분기 추이**:
           - 운동 채택률: {workout_trend:+.1f}%p {"상승 ▲" if workout_trend > 0 else "하락 ▼" if workout_trend < 0 else "유지 —"}
           - 소셜 채택률: {social_trend:+.1f}%p {"상승 ▲" if social_trend > 0 else "하락 ▼" if social_trend < 0 else "유지 —"}

        ---

        ### 🤖 harness 완료 증거

        {evidence_status}

        ```json
        {json.dumps(evidence, ensure_ascii=False, indent=2)}
        ```

        > 이 JSON은 `stage:7-report` 단계에서 분석 완료 검증에 사용됩니다.
        > harness는 `key_metrics` 필드의 값이 모두 존재하는지 확인합니다.

        ---

        > 이 리포트는 FitTrack 합성 데이터를 기반으로 생성되었습니다.
        > 생성일: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}
        """
    )
    return (evidence,)


@app.cell
def export_info(mo):
    # --- 내보내기 안내 ---

    mo.md(
        """
        ---

        ### 💡 리포트 내보내기

        ```bash
        # HTML 내보내기
        marimo export html examples/marimo-feature-engagement.py \\
            -o reports/feature-engagement-report.html

        # PDF 내보내기 (Chromium 필요)
        marimo export pdf examples/marimo-feature-engagement.py \\
            -o reports/feature-engagement-report.pdf
        ```

        > **harness 참고**: `stage:7-report` 단계에서 GitHub Actions가 위 명령을 자동 실행합니다.
        > HTML/PDF는 워크플로 아티팩트로 업로드되며, PR에는 `.py` 소스 파일만 포함됩니다.
        """
    )
    return


if __name__ == "__main__":
    app.run()

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
FitTrack 사용자 퍼널 분석 노트북

이 marimo 노트북은 FitTrack 앱의 사용자 생애주기 퍼널을 인터랙티브하게 분석합니다.

## 퍼널 유형

1. **온보딩 퍼널**: 가입 → 활성화 → 첫 운동 완료 → 유료 전환
2. **일별 운동 퍼널**: 앱 오픈(DAU) → 운동 시작 → 운동 완료
3. **채널별 퍼널**: 유입 채널(referral_source)별 온보딩 전환율 비교

## 사용 데이터 소스
- `int_user_metrics`: 사용자 누적 지표 + 세그먼트 (온보딩/채널 퍼널)
- `fct_feature_engagement`: 일별 기능 참여도 (운동 퍼널)

## harness 연동
7단계 자동 워크플로의 `stage:6-analyze` 단계에서 에이전트가 이 구조를 참조합니다.
채널별 마케팅 효율 분석 이슈(예: "유입 채널별 온보딩 전환율 비교")에 적합한 템플릿입니다.

사용법:
  marimo edit examples/marimo-funnel-analysis.py
  marimo run examples/marimo-funnel-analysis.py

HTML 내보내기:
  marimo export html examples/marimo-funnel-analysis.py -o reports/funnel-analysis-report.html
"""

import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium")


@app.cell
def title():
    import marimo as mo

    mo.md(
        """
        # 🔽 FitTrack 사용자 퍼널 분석

        **분석 기간**: 2026년 1분기 신규 가입 코호트
        **분석 대상**: 앱 가입 ~ 유료 전환까지의 생애주기 전환율

        ---

        ## 분석 개요

        퍼널 분석은 사용자가 목표(전환) 달성까지 거치는 **단계별 이탈률**을 측정합니다.
        각 단계에서 얼마나 많은 사용자가 이탈하는지 파악하여
        제품 개선 우선순위를 결정하는 데 활용합니다.

        ### 이 노트북의 퍼널 구조

        | 퍼널 | 단계 | 핵심 질문 |
        |------|------|-----------|
        | 온보딩 | 가입 → 활성화 → 첫 운동 → 유료 전환 | "어디서 가장 많이 이탈하는가?" |
        | 운동 | DAU → 운동 시작 → 운동 완료 | "운동 시작률과 완료율 중 어떤 것이 낮은가?" |
        | 채널 | 채널별 활성화율 · 전환율 비교 | "어느 채널 사용자가 가장 가치 있는가?" |

        ### marimo 반응형 UI 활용

        > **harness 패턴**: 아래 필터 패널에서 파라미터를 조정하면
        > 관련 차트가 자동으로 업데이트됩니다.
        > 이해관계자가 PR에서 노트북을 열어 직접 탐색할 수 있는 인터랙티브 리포트입니다.
        """
    )
    return (mo,)


@app.cell
def config():
    # --- 분석 설정 (에이전트가 자동 설정하는 셀) ---
    # stage:6-analyze에서 에이전트가 이슈 파싱 결과를 기반으로
    # 이 딕셔너리의 값을 수정합니다. 나머지 셀은 그대로 유지됩니다.

    import os

    ANALYSIS_CONFIG = {
        # GCP 설정
        "project_id": os.getenv("GCP_PROJECT_ID", "your-gcp-project-id"),
        "dataset": "fittrack",

        # 분석 기간 (이슈 본문에서 파싱)
        "start_date": "2026-01-01",  # 온보딩 퍼널: 이 날짜 이후 가입자만 포함
        "end_date": "2026-03-31",    # 일별 운동 퍼널: 이 기간의 fct_feature_engagement 조회

        # 활성화 기준 (가입 후 N일 이내 첫 이벤트)
        "activation_window_days": 7,

        # 완료 증거 출력 경로
        "evidence_path": "evidence/funnel-analysis-evidence.json",
    }
    return (ANALYSIS_CONFIG,)


@app.cell
def setup_bigquery(ANALYSIS_CONFIG, mo):
    # --- BigQuery 클라이언트 초기화 ---
    # 로컬: gcloud auth application-default login
    # CI/CD: GOOGLE_APPLICATION_CREDENTIALS 환경변수 (서비스 계정 JSON)
    # mo.stop() 패턴: 연결 실패 시 후속 셀 실행을 중단하여 오류 원인을 명확히 합니다.

    from google.cloud import bigquery

    try:
        bq_client = bigquery.Client(project=ANALYSIS_CONFIG["project_id"])
        bq_client.get_dataset(ANALYSIS_CONFIG["dataset"])
        connection_ok = True
        connection_msg = "✅ BigQuery 연결 성공"
    except Exception as e:
        connection_ok = False
        connection_msg = f"❌ BigQuery 연결 실패: {e}"
        bq_client = None

    mo.md(connection_msg)

    # 연결 실패 시 후속 셀 실행 중단
    mo.stop(
        not connection_ok,
        mo.md(f"⛔ BigQuery 연결 실패로 분석을 중단합니다.\n\n{connection_msg}"),
    )

    return (bq_client,)


@app.cell
def load_user_metrics(ANALYSIS_CONFIG, bq_client, mo):
    # --- 온보딩 퍼널용 사용자 데이터 로드 ---
    # int_user_metrics에서 사용자 누적 지표와 세그먼트를 조회합니다.
    # 전체 데이터를 한 번에 로드하고, 이후 필터링은 메모리(pandas)에서 처리합니다.
    # (BigQuery on-demand 비용 절감 패턴: 한 번 로드, 메모리 내 재사용)

    import pandas as pd

    user_query = f"""
    SELECT
        user_id,
        signup_date_kst,
        platform,
        referral_source,
        subscription_tier,
        country,

        -- 활성화 여부 (가입 후 {ANALYSIS_CONFIG["activation_window_days"]}일 이내 첫 이벤트)
        is_activated,
        days_to_first_activity,

        -- 운동 완료 이력
        lifetime_workouts,
        lifetime_workouts > 0 AS has_completed_workout,

        -- 유료 전환 여부
        subscription_tier IN ('premium', 'premium_plus') AS is_paying,

        -- LTV 지표
        lifetime_revenue_krw,

        -- 이탈 위험 지표
        days_since_last_activity,
        activity_segment

    FROM `{ANALYSIS_CONFIG["project_id"]}.{ANALYSIS_CONFIG["dataset"]}.int_user_metrics`
    WHERE signup_date_kst BETWEEN '{ANALYSIS_CONFIG["start_date"]}' AND '{ANALYSIS_CONFIG["end_date"]}'
    """

    df_users = bq_client.query(user_query).to_dataframe()

    # 데이터 타입 변환
    df_users["signup_date_kst"] = pd.to_datetime(df_users["signup_date_kst"])
    df_users["signup_month"] = df_users["signup_date_kst"].dt.strftime("%Y-%m")
    df_users["signup_week"] = df_users["signup_date_kst"].dt.to_period("W").apply(
        lambda p: str(p.start_time.date())
    )

    total_users = len(df_users)
    active_users = df_users["is_activated"].sum()
    workout_users = df_users["has_completed_workout"].sum()
    paying_users = df_users["is_paying"].sum()

    mo.md(
        f"""
        ### 📋 온보딩 퍼널 데이터 로드 완료

        - **총 사용자**: {total_users:,}명
        - **활성화 사용자**: {active_users:,}명 ({active_users/total_users*100:.1f}%)
        - **운동 완료 경험**: {workout_users:,}명 ({workout_users/total_users*100:.1f}%)
        - **유료 전환**: {paying_users:,}명 ({paying_users/total_users*100:.1f}%)

        > 💡 데이터는 한 번만 조회됩니다. 채널·플랫폼 필터 변경 시 BigQuery 재조회 없이 분석됩니다.
        """
    )
    return (df_users,)


@app.cell
def load_daily_features(ANALYSIS_CONFIG, bq_client, mo):
    # --- 일별 운동 퍼널용 데이터 로드 ---
    # fct_feature_engagement에서 일별 DAU, 운동 시작자, 운동 완료자를 조회합니다.

    import pandas as pd

    daily_query = f"""
    SELECT
        activity_date,
        dau,
        workout_users,
        workout_completers,
        total_workout_starts,
        total_workout_completes,
        workout_adoption_rate,
        workout_completion_rate
    FROM `{ANALYSIS_CONFIG["project_id"]}.{ANALYSIS_CONFIG["dataset"]}.fct_feature_engagement`
    WHERE activity_date BETWEEN '{ANALYSIS_CONFIG["start_date"]}' AND '{ANALYSIS_CONFIG["end_date"]}'
    ORDER BY activity_date
    """

    df_daily = bq_client.query(daily_query).to_dataframe()
    df_daily["activity_date"] = pd.to_datetime(df_daily["activity_date"])
    df_daily["workout_adoption_pct"] = (df_daily["workout_adoption_rate"] * 100).round(2)
    df_daily["workout_completion_pct"] = (df_daily["workout_completion_rate"] * 100).round(2)

    mo.md(
        f"""
        ### 📋 일별 운동 퍼널 데이터 로드 완료

        - **기간**: {df_daily["activity_date"].min().strftime("%Y-%m-%d")} ~
          {df_daily["activity_date"].max().strftime("%Y-%m-%d")}
        - **행 수**: {len(df_daily):,}일
        """
    )
    return (df_daily,)


@app.cell
def filter_panel(df_users, mo):
    # --- 인터랙티브 필터 패널 ---
    # marimo의 반응형 UI 패턴:
    # 이 셀에서 정의된 위젯 값이 변경되면,
    # 이 값들을 참조하는 모든 하위 셀이 자동으로 재실행됩니다.
    #
    # harness 활용 관점:
    # 에이전트가 생성한 노트북에 이 패턴을 포함하면
    # PR 리뷰어가 파라미터를 직접 조정하며 분석 결과를 탐색할 수 있습니다.

    platform_options = ["전체"] + sorted(df_users["platform"].unique().tolist())
    referral_options = ["전체"] + sorted(df_users["referral_source"].dropna().unique().tolist())

    selected_platform = mo.ui.dropdown(
        options=platform_options,
        value="전체",
        label="플랫폼 필터",
    )

    selected_referral = mo.ui.dropdown(
        options=referral_options,
        value="전체",
        label="유입 채널 필터",
    )

    selected_cohort_period = mo.ui.radio(
        options={"전체 기간": "all", "월별 비교": "monthly", "주별 비교": "weekly"},
        value="전체 기간",
        label="코호트 분류",
    )

    mo.md("## 🎛️ 분석 파라미터")
    mo.hstack(
        [
            mo.vstack([mo.md("**플랫폼**"), selected_platform]),
            mo.vstack([mo.md("**유입 채널**"), selected_referral]),
            mo.vstack([mo.md("**코호트 분류**"), selected_cohort_period]),
        ],
        gap=2,
        justify="start",
    )
    return (selected_cohort_period, selected_platform, selected_referral)


@app.cell
def chart_onboarding_funnel(
    df_users,
    mo,
    selected_cohort_period,
    selected_platform,
    selected_referral,
):
    # --- 차트 1: 온보딩 퍼널 (Funnel Chart) ---
    # 전체/선택 필터 기준으로 온보딩 4단계 퍼널을 시각화합니다.
    # Plotly의 go.Funnel을 사용하여 각 단계 사용자 수와 전환율을 표시합니다.
    #
    # 퍼널 단계 정의:
    # Step 1. 가입 (Signup)     → 분석 기간 내 가입한 모든 사용자
    # Step 2. 활성화 (Activated) → 가입 후 7일 이내 앱 이벤트 발생
    # Step 3. 운동 완료          → 생애 최소 1회 운동 완료
    # Step 4. 유료 전환          → premium 또는 premium_plus 구독

    import plotly.graph_objects as go
    import pandas as pd

    # 플랫폼 필터 적용
    df_filtered = df_users.copy()
    if selected_platform.value != "전체":
        df_filtered = df_filtered[df_filtered["platform"] == selected_platform.value]
    if selected_referral.value != "전체":
        df_filtered = df_filtered[df_filtered["referral_source"] == selected_referral.value]

    # 코호트 분류에 따른 집계
    period_val = selected_cohort_period.value

    if period_val == "all":
        # 전체 기간 집계
        funnel_data = [{
            "label": "전체",
            "step1": len(df_filtered),
            "step2": df_filtered["is_activated"].sum(),
            "step3": df_filtered["has_completed_workout"].sum(),
            "step4": df_filtered["is_paying"].sum(),
        }]
    else:
        # 월별 또는 주별 코호트 집계
        group_col = "signup_month" if period_val == "monthly" else "signup_week"
        funnel_data = []
        for period_label, group_df in df_filtered.groupby(group_col):
            funnel_data.append({
                "label": str(period_label),
                "step1": len(group_df),
                "step2": group_df["is_activated"].sum(),
                "step3": group_df["has_completed_workout"].sum(),
                "step4": group_df["is_paying"].sum(),
            })

    # 전체 기간 퍼널 차트
    agg_data = funnel_data[0] if period_val == "all" else {
        "label": "전체 합산",
        "step1": sum(d["step1"] for d in funnel_data),
        "step2": sum(d["step2"] for d in funnel_data),
        "step3": sum(d["step3"] for d in funnel_data),
        "step4": sum(d["step4"] for d in funnel_data),
    }

    s1 = agg_data["step1"]
    s2 = agg_data["step2"]
    s3 = agg_data["step3"]
    s4 = agg_data["step4"]

    # 단계별 전환율 계산 (이전 단계 대비)
    r12 = s2 / s1 * 100 if s1 > 0 else 0  # 활성화율
    r23 = s3 / s2 * 100 if s2 > 0 else 0  # 활성화 → 운동 완료 전환율
    r34 = s4 / s3 * 100 if s3 > 0 else 0  # 운동 완료 → 유료 전환율
    r14 = s4 / s1 * 100 if s1 > 0 else 0  # 전체 전환율 (가입 → 유료)

    # 단계별 이탈자 수
    drop12 = s1 - s2
    drop23 = s2 - s3
    drop34 = s3 - s4

    fig_funnel = go.Figure(
        go.Funnel(
            y=[
                f"Step 1: 가입 ({s1:,}명)",
                f"Step 2: 활성화 ({s2:,}명)",
                f"Step 3: 첫 운동 완료 ({s3:,}명)",
                f"Step 4: 유료 전환 ({s4:,}명)",
            ],
            x=[s1, s2, s3, s4],
            textposition="inside",
            textinfo="value+percent initial",
            marker=dict(
                color=["#E3F2FD", "#90CAF9", "#1976D2", "#0D47A1"],
                line=dict(width=1, color="white"),
            ),
            connector=dict(line=dict(color="#BBDEFB", width=2)),
            hovertemplate=(
                "%{y}<br>"
                "사용자: %{x:,}명<br>"
                "가입 대비: %{percentInitial}<extra></extra>"
            ),
        )
    )

    fig_funnel.update_layout(
        title={
            "text": f"온보딩 퍼널 — {selected_platform.value} / {selected_referral.value}",
            "x": 0.5,
            "xanchor": "center",
        },
        template="plotly_white",
        height=420,
        margin=dict(l=200),
    )

    mo.md(
        f"""
        ## 🔽 1. 온보딩 퍼널

        ### 단계별 전환율

        | 전환 구간 | 전환율 | 이탈자 수 |
        |-----------|--------|-----------|
        | 가입 → 활성화 | **{r12:.1f}%** | {drop12:,}명 |
        | 활성화 → 첫 운동 완료 | **{r23:.1f}%** | {drop23:,}명 |
        | 운동 완료 → 유료 전환 | **{r34:.1f}%** | {drop34:,}명 |
        | **전체 (가입 → 유료)** | **{r14:.1f}%** | — |

        > **가장 큰 이탈 단계**: {"가입 → 활성화" if drop12 >= drop23 and drop12 >= drop34 else "활성화 → 첫 운동 완료" if drop23 >= drop34 else "운동 완료 → 유료 전환"}
        > 에서 **{max(drop12, drop23, drop34):,}명**이 이탈합니다.
        > 이 구간의 경험을 개선하면 전반적인 전환율을 가장 효과적으로 높일 수 있습니다.
        """
    )
    mo.ui.plotly(fig_funnel)
    return (
        drop12,
        drop23,
        drop34,
        fig_funnel,
        r12,
        r14,
        r23,
        r34,
        s1,
        s2,
        s3,
        s4,
    )


@app.cell
def chart_funnel_by_cohort(
    df_users,
    mo,
    selected_cohort_period,
    selected_platform,
    selected_referral,
):
    # --- 차트 2: 코호트별 퍼널 전환율 추이 ---
    # 월별 또는 주별 코호트의 단계별 전환율을 라인 차트로 시각화합니다.
    # "최근 코호트의 활성화율이 개선되고 있는가?"를 파악하는 데 활용합니다.

    import plotly.graph_objects as go
    import pandas as pd

    # 필터 적용
    df_filtered = df_users.copy()
    if selected_platform.value != "전체":
        df_filtered = df_filtered[df_filtered["platform"] == selected_platform.value]
    if selected_referral.value != "전체":
        df_filtered = df_filtered[df_filtered["referral_source"] == selected_referral.value]

    period_val = selected_cohort_period.value

    # 전체 기간인 경우 이 차트는 의미 없으므로 월별로 기본 표시
    group_col = "signup_month" if period_val in ("all", "monthly") else "signup_week"

    cohort_funnel = []
    for period_label, group_df in df_filtered.groupby(group_col):
        n = len(group_df)
        if n == 0:
            continue
        cohort_funnel.append({
            "period": str(period_label),
            "total_users": n,
            "activation_rate": group_df["is_activated"].sum() / n * 100,
            "workout_rate": group_df["has_completed_workout"].sum() / n * 100,
            "conversion_rate": group_df["is_paying"].sum() / n * 100,
        })

    df_cohort = pd.DataFrame(cohort_funnel)

    if df_cohort.empty:
        mo.stop(True, mo.md("⚠️ 선택한 필터 조합에 해당하는 데이터가 없습니다."))

    fig_cohort = go.Figure()

    # 단계별 전환율 라인
    rate_config = [
        ("activation_rate", "활성화율 (가입 → 7일 활성)", "#1976D2"),
        ("workout_rate", "운동 완료율 (가입 → 첫 운동)", "#388E3C"),
        ("conversion_rate", "유료 전환율 (가입 → 유료)", "#7B1FA2"),
    ]

    for col, label, color in rate_config:
        fig_cohort.add_trace(
            go.Scatter(
                x=df_cohort["period"],
                y=df_cohort[col],
                mode="lines+markers",
                line=dict(color=color, width=2),
                marker=dict(size=8),
                name=label,
                hovertemplate=f"{label}: %{{y:.1f}}%<extra></extra>",
            )
        )

    fig_cohort.update_layout(
        title={
            "text": f"코호트별 온보딩 퍼널 전환율 추이 ({group_col.replace('signup_', '')}별)",
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis_title="가입 코호트",
        yaxis=dict(
            title="전환율 (%)",
            ticksuffix="%",
            range=[0, 105],
        ),
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )

    mo.md("## 📈 2. 코호트별 퍼널 전환율 추이")
    mo.ui.plotly(fig_cohort)
    return (df_cohort, fig_cohort)


@app.cell
def chart_daily_workout_funnel(df_daily, mo):
    # --- 차트 3: 일별 운동 퍼널 추이 ---
    # DAU 중 운동 시작자 비율(채택률)과 운동 시작자 중 완료자 비율(완료율)을
    # 시계열로 추적합니다.
    # 이 두 지표 중 어떤 것이 더 낮은지에 따라 개선 전략이 달라집니다:
    # - 채택률이 낮으면: 운동 기능 발견성(discoverability) 개선
    # - 완료율이 낮으면: 운동 프로그램 난이도·길이 최적화

    import plotly.graph_objects as go

    fig_workout = go.Figure()

    # 운동 채택률 (DAU 중 운동 시작자 비율)
    fig_workout.add_trace(
        go.Scatter(
            x=df_daily["activity_date"],
            y=df_daily["workout_adoption_pct"].rolling(window=7, min_periods=1).mean(),
            mode="lines",
            line=dict(color="#1976D2", width=2.5),
            name="운동 채택률 (7일 이동평균)",
            hovertemplate="채택률: %{y:.1f}%<extra></extra>",
        )
    )

    # 운동 완료율 (시작자 중 완료자 비율)
    fig_workout.add_trace(
        go.Scatter(
            x=df_daily["activity_date"],
            y=df_daily["workout_completion_pct"].rolling(window=7, min_periods=1).mean(),
            mode="lines",
            line=dict(color="#388E3C", width=2.5),
            name="운동 완료율 (7일 이동평균)",
            hovertemplate="완료율: %{y:.1f}%<extra></extra>",
        )
    )

    fig_workout.update_layout(
        title={
            "text": "일별 운동 퍼널 — 채택률 vs 완료율 (7일 이동평균)",
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis_title="날짜",
        yaxis=dict(
            title="비율 (%)",
            ticksuffix="%",
            range=[0, 105],
        ),
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )

    # 기간 평균 지표 계산
    avg_adoption = df_daily["workout_adoption_pct"].mean()
    avg_completion = df_daily["workout_completion_pct"].mean()
    bottleneck = "채택률 (운동 기능 발견성 개선 필요)" if avg_adoption < avg_completion else "완료율 (운동 난이도·길이 최적화 필요)"

    mo.md(
        f"""
        ## 🏃 3. 일별 운동 퍼널 (DAU → 시작 → 완료)

        | 지표 | 기간 평균 |
        |------|-----------|
        | 운동 채택률 (DAU 중 시작 비율) | **{avg_adoption:.1f}%** |
        | 운동 완료율 (시작자 중 완료 비율) | **{avg_completion:.1f}%** |

        > **병목 단계**: {bottleneck}
        """
    )
    mo.ui.plotly(fig_workout)
    return (avg_adoption, avg_completion, fig_workout)


@app.cell
def chart_channel_funnel(df_users, mo):
    # --- 차트 4: 유입 채널별 퍼널 전환율 비교 ---
    # 마케팅 채널별 온보딩 품질을 비교합니다.
    # 동일한 CAC(고객 획득 비용)이라면 전환율이 높은 채널이 더 효율적입니다.
    # 이 차트는 필터 위젯과 독립적으로 항상 전체 데이터를 표시합니다.

    import plotly.express as px
    import pandas as pd

    # 유입 채널별 퍼널 집계
    channel_funnel = (
        df_users.groupby("referral_source")
        .agg(
            total_users=("user_id", "count"),
            activation_rate=("is_activated", "mean"),
            workout_rate=("has_completed_workout", "mean"),
            conversion_rate=("is_paying", "mean"),
            avg_ltv_krw=("lifetime_revenue_krw", "mean"),
        )
        .reset_index()
    )

    # 비율 → 퍼센트 변환
    for rate_col in ["activation_rate", "workout_rate", "conversion_rate"]:
        channel_funnel[f"{rate_col}_pct"] = (channel_funnel[rate_col] * 100).round(1)

    # 유료 전환율 기준 내림차순 정렬
    channel_funnel = channel_funnel.sort_values("conversion_rate_pct", ascending=False)

    # 3개 지표를 그룹 바 차트로 표시
    df_melt = channel_funnel.melt(
        id_vars=["referral_source", "total_users"],
        value_vars=["activation_rate_pct", "workout_rate_pct", "conversion_rate_pct"],
        var_name="metric",
        value_name="rate_pct",
    )

    metric_labels = {
        "activation_rate_pct": "활성화율",
        "workout_rate_pct": "운동 완료율",
        "conversion_rate_pct": "유료 전환율",
    }
    df_melt["metric_label"] = df_melt["metric"].map(metric_labels)

    color_map = {
        "활성화율": "#1976D2",
        "운동 완료율": "#388E3C",
        "유료 전환율": "#7B1FA2",
    }

    fig_channel = px.bar(
        df_melt,
        x="referral_source",
        y="rate_pct",
        color="metric_label",
        color_discrete_map=color_map,
        barmode="group",
        title="유입 채널별 온보딩 퍼널 전환율 비교",
        labels={
            "referral_source": "유입 채널",
            "rate_pct": "전환율 (%)",
            "metric_label": "지표",
        },
        text_auto=".1f",
    )

    fig_channel.update_traces(textposition="outside", textfont_size=10)
    fig_channel.update_layout(
        yaxis=dict(ticksuffix="%", range=[0, 115]),
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )

    # 채널별 LTV 테이블
    ltv_table = channel_funnel[["referral_source", "total_users", "conversion_rate_pct", "avg_ltv_krw"]].copy()
    ltv_table.columns = ["유입 채널", "사용자 수", "유료 전환율 (%)", "평균 LTV (원)"]
    ltv_table["평균 LTV (원)"] = ltv_table["평균 LTV (원)"].round(0).astype(int)

    mo.md("## 📢 4. 유입 채널별 퍼널 전환율 비교")
    mo.ui.plotly(fig_channel)
    mo.md("### 채널별 평균 LTV")
    mo.ui.table(ltv_table)
    return (channel_funnel, fig_channel, ltv_table)


@app.cell
def summary_and_evidence(
    ANALYSIS_CONFIG,
    avg_adoption,
    avg_completion,
    channel_funnel,
    df_cohort,
    drop12,
    drop23,
    drop34,
    mo,
    r12,
    r14,
    r23,
    r34,
    s1,
    s4,
):
    # --- 주요 발견 요약 및 완료 증거 생성 ---
    # 분석 결과를 요약하고 harness가 검증할 완료 증거 JSON을 생성합니다.
    # evidence/ 디렉토리의 JSON은 stage:7-report에서 분석 완료 검증에 사용됩니다.

    import json
    import os
    import pandas as pd

    # 가장 큰 이탈 단계 식별
    drops = {"가입 → 활성화": drop12, "활성화 → 운동 완료": drop23, "운동 완료 → 유료 전환": drop34}
    biggest_drop_stage = max(drops, key=drops.get)
    biggest_drop_count = max(drops.values())

    # 최고 성과 채널 (유료 전환율 기준)
    best_channel = channel_funnel.iloc[0]["referral_source"] if not channel_funnel.empty else "N/A"
    best_channel_rate = channel_funnel.iloc[0]["conversion_rate_pct"] if not channel_funnel.empty else 0

    # 최근 코호트 vs 최초 코호트 비교 (활성화율)
    if len(df_cohort) >= 2:
        activation_trend = df_cohort.iloc[-1]["activation_rate"] - df_cohort.iloc[0]["activation_rate"]
    else:
        activation_trend = 0.0

    # 완료 증거 생성
    evidence = {
        "analysis_type": "funnel_analysis",
        "period": {
            "start": ANALYSIS_CONFIG["start_date"],
            "end": ANALYSIS_CONFIG["end_date"],
        },
        "key_metrics": {
            "total_users": int(s1),
            "overall_conversion_rate_pct": round(r14, 2),
            "activation_rate_pct": round(r12, 2),
            "activation_to_workout_rate_pct": round(r23, 2),
            "workout_to_paid_rate_pct": round(r34, 2),
            "avg_workout_adoption_pct": round(avg_adoption, 2),
            "avg_workout_completion_pct": round(avg_completion, 2),
        },
        "insights": {
            "biggest_drop_stage": biggest_drop_stage,
            "biggest_drop_count": int(biggest_drop_count),
            "best_channel": best_channel,
            "best_channel_conversion_pct": round(float(best_channel_rate), 2),
            "activation_trend_pct": round(activation_trend, 2),
        },
        "generated_at": pd.Timestamp.now().isoformat(),
    }

    # 증거 파일 저장
    evidence_path = ANALYSIS_CONFIG["evidence_path"]
    try:
        os.makedirs(os.path.dirname(evidence_path), exist_ok=True)
        with open(evidence_path, "w", encoding="utf-8") as f:
            json.dump(evidence, f, ensure_ascii=False, indent=2)
        evidence_status = f"✅ 완료 증거 저장: `{evidence_path}`"
    except Exception as e:
        evidence_status = f"⚠️ 증거 저장 건너뜀: {e}"

    mo.md(
        f"""
        ---

        ## 🔍 주요 발견 요약

        1. **전체 전환율**: 가입에서 유료 전환까지의 전체 전환율은 **{r14:.1f}%**입니다.
           {s1:,}명이 가입하여 최종적으로 **{s4:,}명**이 유료 사용자가 되었습니다.

        2. **최대 이탈 구간**: **"{biggest_drop_stage}"** 구간에서
           **{biggest_drop_count:,}명**이 이탈하여 전체 퍼널 개선의 최우선 타겟입니다.

        3. **활성화율**: 가입 후 7일 이내 앱을 재방문하는 사용자는 **{r12:.1f}%**입니다.
           {"온보딩 시퀀스(푸시 알림, 이메일 리마인더)를 강화하여 이 비율을 높이세요." if r12 < 60 else "양호한 수준이나, 활성화 이후 운동 완료율 개선에 집중하세요."}

        4. **운동 퍼널 병목**: 일별 운동 채택률 **{avg_adoption:.1f}%** vs 완료율 **{avg_completion:.1f}%**.
           {"채택률이 더 낮아 운동 기능 발견성(홈 화면 배치, 알림) 개선이 필요합니다." if avg_adoption < avg_completion else "완료율이 더 낮아 운동 프로그램 난이도와 길이 최적화가 필요합니다."}

        5. **최고 성과 채널**: **{best_channel}** 채널이 유료 전환율 **{best_channel_rate:.1f}%**로
           가장 높은 채널 품질을 보입니다. 이 채널에 마케팅 예산을 우선 배분하세요.

        ---

        ### 🤖 harness 완료 증거

        {evidence_status}

        > `stage:7-report`에서 이 JSON의 `key_metrics` 필드를 검증합니다.

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
        marimo export html examples/marimo-funnel-analysis.py \\
            -o reports/funnel-analysis-report.html

        # PDF 내보내기 (Chromium 필요)
        marimo export pdf examples/marimo-funnel-analysis.py \\
            -o reports/funnel-analysis-report.pdf
        ```

        > **harness 참고**: `stage:7-report` 단계에서 GitHub Actions가 위 명령을 자동 실행합니다.
        > HTML/PDF는 워크플로 아티팩트로 업로드되며, PR에는 `.py` 소스 파일만 포함됩니다.
        """
    )
    return


if __name__ == "__main__":
    app.run()

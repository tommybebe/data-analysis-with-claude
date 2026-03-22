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
FitTrack 사용자 세그먼트 & LTV 분석 노트북

이 marimo 노트북은 FitTrack 앱의 사용자 세그먼트 분포와 LTV(생애 가치)를
인터랙티브하게 탐색합니다.

## 분석 내용

1. **세그먼트 분포**: 활동 세그먼트 × 수익 세그먼트 교차 분포
2. **LTV 분석**: 세그먼트별 평균 LTV 비교 및 전체 LTV 구성 비율
3. **재참여 우선순위**: 재참여 우선순위 점수가 높은 이탈 위험 사용자 타겟팅
4. **채널 품질**: 유입 채널별 세그먼트 구성 비교 (채널 품질 평가)

## 세그먼트 정의

### 활동 세그먼트 (activity_segment)
- **power_user**: 최근 30일 내 20일 이상 활동
- **regular**: 최근 30일 내 8~19일 활동
- **casual**: 최근 30일 내 1~7일 활동
- **dormant**: 최근 31~90일 동안 미활동
- **churned**: 91일 이상 미활동

### 수익 세그먼트 (revenue_segment)
- **high_value**: 누적 결제 상위 20%
- **mid_value**: 누적 결제 중위 60%
- **low_value**: 결제 경험 있는 하위 20%
- **non_paying**: 결제 이력 없음

## 사용 데이터 소스
- `fct_user_segments`: 사용자 세그먼트 교차 집계 스냅샷

## harness 연동
`stage:6-analyze`에서 "사용자 세그먼트별 LTV 비교" 또는
"재참여 캠페인 타겟 사용자 선별" 이슈에 적합한 노트북 템플릿입니다.
에이전트는 ANALYSIS_CONFIG만 수정하고 나머지 패턴은 유지합니다.

사용법:
  marimo edit examples/marimo-user-segments-ltv.py
  marimo run examples/marimo-user-segments-ltv.py

HTML 내보내기:
  marimo export html examples/marimo-user-segments-ltv.py -o reports/user-segments-report.html
"""

import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium")


@app.cell
def title():
    import marimo as mo

    mo.md(
        """
        # 👥 FitTrack 사용자 세그먼트 & LTV 분석

        **분석 기준**: 현재 시점 스냅샷 (실행 시점의 세그먼트 상태)
        **데이터 소스**: `fct_user_segments` (활동 × 수익 세그먼트 교차 집계)

        ---

        ## 분석 개요

        사용자 세그먼트 분석은 **누가 우리의 핵심 고객인지, 어떤 사용자가
        이탈 위험에 처해있는지, 어디에 마케팅 자원을 배분해야 하는지**를
        데이터 기반으로 파악합니다.

        ### 핵심 질문

        1. **현황**: 전체 사용자 중 파워 유저, 일반 유저, 이탈 위험 유저의 비중은?
        2. **수익 집중도**: 상위 몇 %의 사용자가 전체 수익의 80%를 창출하는가?
        3. **재참여 기회**: LTV가 높지만 최근 이탈한 사용자는 누구인가?
        4. **채널 품질**: 어떤 유입 채널이 파워 유저를 가장 많이 만들어내는가?

        ### marimo 반응형 UI

        > 아래 필터 패널에서 플랫폼, 구독 등급, 국가를 조정하면
        > 모든 차트가 **자동으로 업데이트**됩니다.
        > BigQuery 재조회 없이 메모리 내 필터링으로 즉시 반영됩니다.
        """
    )
    return (mo,)


@app.cell
def config():
    # --- 분석 설정 (에이전트가 수정하는 유일한 셀) ---
    # stage:6-analyze에서 에이전트가 이슈 파싱 결과에 따라 이 값을 설정합니다.
    # 나머지 셀의 패턴은 변경하지 않습니다.

    import os

    ANALYSIS_CONFIG = {
        # GCP 설정
        "project_id": os.getenv("GCP_PROJECT_ID", "your-gcp-project-id"),
        "dataset": "fittrack",

        # 분석 초점 (이슈에서 파싱, 선택적으로 특정 세그먼트에 집중)
        # "all": 전체 세그먼트 / "power_user", "dormant", "churned" 등 특정 세그먼트
        "focus_segment": "all",

        # 재참여 우선순위 임계값: 이 점수 이상인 사용자를 재참여 캠페인 타겟으로 선정
        "reengagement_threshold": 5.0,

        # 완료 증거 출력 경로
        "evidence_path": "evidence/user-segments-ltv-evidence.json",
    }
    return (ANALYSIS_CONFIG,)


@app.cell
def setup_bigquery(ANALYSIS_CONFIG, mo):
    # --- BigQuery 클라이언트 초기화 ---
    # mo.stop() 패턴: 연결 실패 시 후속 셀 실행을 즉시 중단합니다.

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
    mo.stop(
        not connection_ok,
        mo.md(f"⛔ BigQuery 연결 실패로 분석을 중단합니다.\n\n{connection_msg}"),
    )

    return (bq_client,)


@app.cell
def load_segment_data(ANALYSIS_CONFIG, bq_client, mo):
    # --- 세그먼트 데이터 로드 ---
    # fct_user_segments에서 활동·수익 세그먼트 교차 집계 데이터를 조회합니다.
    # 이 테이블은 사전 집계된 스냅샷이므로 데이터 크기가 작고 빠르게 로드됩니다.
    #
    # 비용 절감 패턴: 이 작은 집계 테이블을 한 번 로드하고
    # 이후의 모든 필터링/시각화는 메모리(pandas)에서 처리합니다.

    import pandas as pd

    segment_query = f"""
    SELECT
        activity_segment,
        revenue_segment,
        subscription_tier,
        referral_source,
        country,
        platform,

        -- 사용자 수 및 비율
        user_count,
        user_share,

        -- 활동 행동 지표
        avg_active_days,
        avg_activity_density,
        avg_daily_session_minutes,
        avg_lifetime_workouts,
        avg_workout_completion_rate,

        -- 수익 지표
        paying_user_rate,
        avg_ltv_krw,
        total_ltv_krw,
        max_ltv_krw,

        -- 활성화 지표
        activation_rate,
        avg_days_to_first_activity,

        -- 이탈 위험 지표
        avg_days_since_last_activity,

        -- 재참여 우선순위 점수
        reengagement_priority_score

    FROM `{ANALYSIS_CONFIG["project_id"]}.{ANALYSIS_CONFIG["dataset"]}.fct_user_segments`
    """

    df_segments = bq_client.query(segment_query).to_dataframe()

    # 비율 컬럼을 퍼센트로 변환 (시각화용)
    pct_cols = {
        "user_share": "user_share_pct",
        "avg_workout_completion_rate": "avg_workout_completion_pct",
        "paying_user_rate": "paying_user_rate_pct",
        "activation_rate": "activation_rate_pct",
    }
    for src, dst in pct_cols.items():
        df_segments[dst] = (df_segments[src] * 100).round(1)

    # 세그먼트 순서 정의 (차트 정렬용)
    activity_order = ["power_user", "regular", "casual", "dormant", "churned"]
    revenue_order = ["high_value", "mid_value", "low_value", "non_paying"]

    total_users = df_segments["user_count"].sum()
    total_ltv = df_segments["total_ltv_krw"].sum()

    mo.md(
        f"""
        ### 📋 세그먼트 데이터 로드 완료

        - **총 세그먼트 조합**: {len(df_segments):,}개
        - **총 사용자 수**: {total_users:,}명
        - **총 누적 LTV**: ₩{total_ltv:,.0f}

        > 💡 이 집계 테이블은 한 번만 조회됩니다.
        > 아래 필터 변경 시 BigQuery 재조회 없이 분석됩니다.
        """
    )
    return (activity_order, df_segments, revenue_order, total_ltv, total_users)


@app.cell
def filter_panel(df_segments, mo):
    # --- 인터랙티브 필터 패널 ---
    # 이 셀의 위젯 값이 변경되면, 의존하는 모든 하위 셀이 자동으로 재실행됩니다.
    # Jupyter와의 차이: "Run All Below" 없이 자동으로 의존 셀만 재실행됩니다.

    platform_options = ["전체"] + sorted(df_segments["platform"].dropna().unique().tolist())
    tier_options = ["전체"] + sorted(df_segments["subscription_tier"].dropna().unique().tolist())
    referral_options = ["전체"] + sorted(df_segments["referral_source"].dropna().unique().tolist())

    selected_platform = mo.ui.dropdown(
        options=platform_options,
        value="전체",
        label="플랫폼",
    )

    selected_tier = mo.ui.dropdown(
        options=tier_options,
        value="전체",
        label="구독 등급",
    )

    selected_referral = mo.ui.dropdown(
        options=referral_options,
        value="전체",
        label="유입 채널",
    )

    mo.md("## 🎛️ 분석 파라미터")
    mo.hstack(
        [
            mo.vstack([mo.md("**플랫폼**"), selected_platform]),
            mo.vstack([mo.md("**구독 등급**"), selected_tier]),
            mo.vstack([mo.md("**유입 채널**"), selected_referral]),
        ],
        gap=2,
        justify="start",
    )
    return (selected_platform, selected_referral, selected_tier)


@app.cell
def apply_filters(df_segments, mo, selected_platform, selected_referral, selected_tier):
    # --- 필터 적용 ---
    # 위젯 값에 따라 세그먼트 데이터를 필터링합니다.
    # 세 위젯 중 하나라도 변경되면 이 셀과 하위 셀이 자동으로 재실행됩니다.

    df_filtered = df_segments.copy()

    if selected_platform.value != "전체":
        df_filtered = df_filtered[df_filtered["platform"] == selected_platform.value]
    if selected_tier.value != "전체":
        df_filtered = df_filtered[df_filtered["subscription_tier"] == selected_tier.value]
    if selected_referral.value != "전체":
        df_filtered = df_filtered[df_filtered["referral_source"] == selected_referral.value]

    # 필터 후 합산
    filtered_users = df_filtered["user_count"].sum()
    filtered_ltv = df_filtered["total_ltv_krw"].sum()

    mo.md(
        f"""
        > **현재 필터**: 플랫폼={selected_platform.value} | 구독={selected_tier.value} | 채널={selected_referral.value}
        > | **선택 사용자**: {filtered_users:,}명 | **선택 LTV**: ₩{filtered_ltv:,.0f}
        """
    )
    return (df_filtered, filtered_ltv, filtered_users)


@app.cell
def chart_activity_segment_distribution(activity_order, df_filtered, mo):
    # --- 차트 1: 활동 세그먼트 분포 (도넛 차트) ---
    # power_user ~ churned까지의 활동 세그먼트 사용자 분포를 시각화합니다.
    # 선택된 필터 기준의 세그먼트 현황을 한눈에 파악합니다.

    import plotly.express as px
    import pandas as pd

    # 활동 세그먼트별 집계 (필터 적용 후)
    activity_agg = (
        df_filtered.groupby("activity_segment")["user_count"]
        .sum()
        .reset_index()
    )

    # 세그먼트 순서 적용
    activity_agg["order"] = activity_agg["activity_segment"].map(
        {s: i for i, s in enumerate(activity_order)}
    )
    activity_agg = activity_agg.sort_values("order").dropna(subset=["order"])

    # 한국어 레이블 매핑
    segment_labels = {
        "power_user": "파워 유저",
        "regular": "일반 유저",
        "casual": "캐주얼 유저",
        "dormant": "휴면 유저",
        "churned": "이탈 유저",
    }
    activity_agg["label"] = activity_agg["activity_segment"].map(segment_labels)

    # 세그먼트별 색상
    color_map = {
        "파워 유저": "#0D47A1",
        "일반 유저": "#1976D2",
        "캐주얼 유저": "#64B5F6",
        "휴면 유저": "#FFB74D",
        "이탈 유저": "#EF5350",
    }

    fig_activity = px.pie(
        activity_agg,
        values="user_count",
        names="label",
        title="활동 세그먼트 분포",
        color="label",
        color_discrete_map=color_map,
        hole=0.4,
    )

    fig_activity.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="%{label}: %{value:,}명 (%{percent})<extra></extra>",
    )
    fig_activity.update_layout(
        template="plotly_white",
        legend=dict(orientation="v", yanchor="middle", y=0.5),
    )

    # 주요 지표 요약
    total = activity_agg["user_count"].sum()
    power_pct = activity_agg[activity_agg["activity_segment"] == "power_user"]["user_count"].sum() / total * 100 if total > 0 else 0
    risk_pct = activity_agg[activity_agg["activity_segment"].isin(["dormant", "churned"])]["user_count"].sum() / total * 100 if total > 0 else 0

    mo.md(
        f"""
        ## 📊 1. 활동 세그먼트 분포

        | 세그먼트 | 사용자 수 | 비율 |
        |----------|-----------|------|
        | 파워 유저 | {activity_agg[activity_agg["activity_segment"] == "power_user"]["user_count"].sum():,} | {power_pct:.1f}% |
        | 이탈 위험 (휴면+이탈) | {activity_agg[activity_agg["activity_segment"].isin(["dormant", "churned"])]["user_count"].sum():,} | {risk_pct:.1f}% |

        > **파워 유저 비율 {power_pct:.1f}%**: {"앱 코어팬 기반이 잘 구축되어 있습니다." if power_pct > 15 else "파워 유저 육성 프로그램 강화가 필요합니다."}
        """
    )
    mo.ui.plotly(fig_activity)
    return (activity_agg, fig_activity, power_pct, risk_pct, total)


@app.cell
def chart_ltv_by_segment(activity_order, df_filtered, mo):
    # --- 차트 2: 세그먼트별 평균 LTV 비교 (바 차트) ---
    # 활동 세그먼트별 평균 LTV를 비교하여
    # "파워 유저가 얼마나 더 많은 수익을 창출하는가"를 정량화합니다.
    # 이 수치는 파워 유저 육성 프로그램의 ROI 계산에 활용됩니다.

    import plotly.graph_objects as go
    import pandas as pd

    # 세그먼트별 LTV 집계 (가중평균: user_count를 가중치로 사용)
    ltv_agg = (
        df_filtered.groupby("activity_segment")
        .apply(
            lambda x: pd.Series({
                "user_count": x["user_count"].sum(),
                "total_ltv": x["total_ltv_krw"].sum(),
                "avg_ltv_krw": (
                    (x["avg_ltv_krw"] * x["user_count"]).sum() / x["user_count"].sum()
                    if x["user_count"].sum() > 0 else 0
                ),
            })
        )
        .reset_index()
    )

    # 세그먼트 순서 적용
    ltv_agg["order"] = ltv_agg["activity_segment"].map(
        {s: i for i, s in enumerate(activity_order)}
    )
    ltv_agg = ltv_agg.sort_values("order").dropna(subset=["order"])

    # 한국어 레이블
    segment_labels = {
        "power_user": "파워 유저",
        "regular": "일반 유저",
        "casual": "캐주얼 유저",
        "dormant": "휴면 유저",
        "churned": "이탈 유저",
    }
    ltv_agg["label"] = ltv_agg["activity_segment"].map(segment_labels)

    bar_colors = ["#0D47A1", "#1976D2", "#64B5F6", "#FFB74D", "#EF5350"]

    fig_ltv = go.Figure(
        go.Bar(
            x=ltv_agg["label"],
            y=ltv_agg["avg_ltv_krw"],
            marker_color=bar_colors[:len(ltv_agg)],
            text=[f"₩{v:,.0f}" for v in ltv_agg["avg_ltv_krw"]],
            textposition="outside",
            hovertemplate=(
                "%{x}<br>"
                "평균 LTV: ₩%{y:,.0f}<br>"
                "<extra></extra>"
            ),
        )
    )

    fig_ltv.update_layout(
        title={
            "text": "활동 세그먼트별 평균 LTV (₩)",
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis_title="활동 세그먼트",
        yaxis_title="평균 LTV (원)",
        template="plotly_white",
        yaxis=dict(tickprefix="₩", tickformat=","),
        showlegend=False,
    )

    # 파워 유저 vs 일반 유저 LTV 배수 계산
    power_ltv = ltv_agg[ltv_agg["activity_segment"] == "power_user"]["avg_ltv_krw"].values
    regular_ltv = ltv_agg[ltv_agg["activity_segment"] == "regular"]["avg_ltv_krw"].values

    if len(power_ltv) > 0 and len(regular_ltv) > 0 and regular_ltv[0] > 0:
        ltv_multiplier = power_ltv[0] / regular_ltv[0]
        ltv_insight = f"파워 유저의 평균 LTV는 일반 유저 대비 **{ltv_multiplier:.1f}배** 높습니다."
    else:
        ltv_insight = "세그먼트별 LTV 비교를 위한 데이터가 충분하지 않습니다."

    mo.md(
        f"""
        ## 💰 2. 세그먼트별 평균 LTV

        {ltv_insight}

        > **인사이트**: LTV 배수가 높을수록 파워 유저 육성 프로그램의 ROI가 높습니다.
        > 파워 유저 1명을 만들기 위한 비용이 일반 유저 LTV 차이보다 낮다면
        > 파워 유저 전환 프로그램에 적극적으로 투자해야 합니다.
        """
    )
    mo.ui.plotly(fig_ltv)
    return (fig_ltv, ltv_agg)


@app.cell
def chart_ltv_concentration(df_filtered, mo, revenue_order):
    # --- 차트 3: 수익 집중도 분석 (파레토 차트) ---
    # 수익 세그먼트별 사용자 비중과 LTV 비중을 비교합니다.
    # "상위 X%의 사용자가 전체 수익의 Y%를 차지한다"는 파레토 원칙을 검증합니다.

    import plotly.graph_objects as go
    import pandas as pd

    # 수익 세그먼트별 집계
    revenue_agg = (
        df_filtered.groupby("revenue_segment")
        .agg(
            user_count=("user_count", "sum"),
            total_ltv=("total_ltv_krw", "sum"),
        )
        .reset_index()
    )

    # 세그먼트 순서 적용
    revenue_agg["order"] = revenue_agg["revenue_segment"].map(
        {s: i for i, s in enumerate(revenue_order)}
    )
    revenue_agg = revenue_agg.sort_values("order").dropna(subset=["order"])

    total_users_rev = revenue_agg["user_count"].sum()
    total_ltv_rev = revenue_agg["total_ltv"].sum()

    revenue_agg["user_pct"] = (revenue_agg["user_count"] / total_users_rev * 100).round(1)
    revenue_agg["ltv_pct"] = (revenue_agg["total_ltv"] / total_ltv_rev * 100).round(1) if total_ltv_rev > 0 else 0

    # 한국어 레이블
    revenue_labels = {
        "high_value": "고가치 (상위 20%)",
        "mid_value": "중가치 (중위 60%)",
        "low_value": "저가치 (하위 20%)",
        "non_paying": "비결제",
    }
    revenue_agg["label"] = revenue_agg["revenue_segment"].map(revenue_labels)

    fig_pareto = go.Figure()

    # 사용자 비중 바
    fig_pareto.add_trace(
        go.Bar(
            name="사용자 비중",
            x=revenue_agg["label"],
            y=revenue_agg["user_pct"],
            marker_color="#90CAF9",
            text=[f"{v:.1f}%" for v in revenue_agg["user_pct"]],
            textposition="outside",
            yaxis="y",
        )
    )

    # LTV 비중 바
    fig_pareto.add_trace(
        go.Bar(
            name="LTV 비중",
            x=revenue_agg["label"],
            y=revenue_agg["ltv_pct"],
            marker_color="#1565C0",
            text=[f"{v:.1f}%" for v in revenue_agg["ltv_pct"]],
            textposition="outside",
            yaxis="y",
        )
    )

    fig_pareto.update_layout(
        title={
            "text": "수익 세그먼트별 사용자 비중 vs LTV 비중",
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis_title="수익 세그먼트",
        yaxis=dict(title="비중 (%)", ticksuffix="%", range=[0, 120]),
        template="plotly_white",
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )

    # 파레토 분석: 고가치 세그먼트의 LTV 기여도
    high_value_data = revenue_agg[revenue_agg["revenue_segment"] == "high_value"]
    if not high_value_data.empty:
        hv_user_pct = high_value_data["user_pct"].values[0]
        hv_ltv_pct = high_value_data["ltv_pct"].values[0]
        pareto_insight = (
            f"고가치 사용자 **{hv_user_pct:.1f}%**가 전체 LTV의 "
            f"**{hv_ltv_pct:.1f}%**를 창출합니다."
        )
    else:
        pareto_insight = "고가치 세그먼트 데이터가 없습니다."

    mo.md(
        f"""
        ## 📐 3. 수익 집중도 분석

        {pareto_insight}

        > **파레토 원칙 검증**: LTV/사용자 비중 배율이 클수록 수익이 소수 사용자에게 집중됩니다.
        > 배율이 3배 이상이면 고가치 사용자 유지(retention)에 불균형적으로 집중해야 합니다.
        """
    )
    mo.ui.plotly(fig_pareto)
    return (fig_pareto, revenue_agg)


@app.cell
def chart_reengagement_targets(ANALYSIS_CONFIG, df_filtered, mo):
    # --- 차트 4: 재참여 우선순위 분석 ---
    # 재참여 우선순위 점수(reengagement_priority_score)를 기반으로
    # 재참여 캠페인의 타겟 세그먼트를 식별합니다.
    #
    # 재참여 우선순위 공식 (fct_user_segments 참조):
    #   score = (avg_ltv_krw / 1000) × ln(avg_days_since_last_activity + 1)
    #   → LTV가 높고(가치 있음), 최근 이탈했을수록(아직 살릴 수 있음) 점수가 높음
    #
    # 이 차트는 필터 위젯에 독립적입니다 (항상 전체 데이터 기준 표시).

    import plotly.express as px
    import pandas as pd

    # 이탈 위험 세그먼트 (dormant + churned)만 필터
    df_reeng = df_filtered[
        df_filtered["activity_segment"].isin(["dormant", "churned"])
    ].copy()

    if df_reeng.empty:
        mo.stop(True, mo.md("⚠️ 선택한 필터 기준에서 이탈 위험 세그먼트 데이터가 없습니다."))

    # 재참여 우선순위 기준으로 집계
    threshold = ANALYSIS_CONFIG["reengagement_threshold"]

    # 버블 차트: x=avg_days_since_last_activity, y=avg_ltv_krw, 크기=user_count, 색=priority_score
    fig_reeng = px.scatter(
        df_reeng,
        x="avg_days_since_last_activity",
        y="avg_ltv_krw",
        size="user_count",
        color="reengagement_priority_score",
        color_continuous_scale="Oranges",
        hover_data={
            "activity_segment": True,
            "revenue_segment": True,
            "subscription_tier": True,
            "referral_source": True,
            "user_count": True,
            "avg_ltv_krw": ":.0f",
            "avg_days_since_last_activity": ":.1f",
            "reengagement_priority_score": ":.2f",
        },
        title="재참여 우선순위 분석 (이탈 위험 사용자 그룹)",
        labels={
            "avg_days_since_last_activity": "평균 마지막 활동 이후 일수",
            "avg_ltv_krw": "평균 LTV (원)",
            "reengagement_priority_score": "재참여 우선순위 점수",
            "user_count": "사용자 수",
        },
    )

    # 임계값 라인 추가 (우선순위 점수 기준)
    # x축 최대값 구간에서 threshold에 해당하는 y값 역산
    # score = (ltv/1000) × ln(days+1) → ltv = score × 1000 / ln(days+1)
    import numpy as np
    x_range = np.linspace(
        df_reeng["avg_days_since_last_activity"].min(),
        df_reeng["avg_days_since_last_activity"].max(),
        100,
    )
    # threshold 라인: score = threshold → y = threshold × 1000 / ln(x+1)
    y_threshold = threshold * 1000 / np.log(x_range + 1)

    fig_reeng.add_trace(
        px.line(
            x=x_range,
            y=y_threshold,
        ).data[0]
    )
    fig_reeng.data[-1].update(
        line=dict(color="red", dash="dash", width=1.5),
        name=f"우선순위 임계값 (점수={threshold})",
        showlegend=True,
    )

    fig_reeng.update_layout(
        template="plotly_white",
        coloraxis_colorbar=dict(title="우선순위\n점수"),
    )

    # 임계값 초과 세그먼트 수
    priority_targets = df_reeng[df_reeng["reengagement_priority_score"] >= threshold]
    priority_user_count = priority_targets["user_count"].sum()

    mo.md(
        f"""
        ## 🎯 4. 재참여 캠페인 우선순위 분석

        **버블 크기** = 사용자 수 | **색상** = 재참여 우선순위 점수 (짙을수록 높음)

        **빨간 점선 위의 세그먼트**: 재참여 우선순위 점수 ≥ {threshold}
        → **{priority_user_count:,}명** 재참여 캠페인 우선 타겟

        > **재참여 우선순위 점수 공식**: `(평균 LTV / 1,000) × ln(마지막 활동 이후 일수 + 1)`
        >
        > - LTV가 높을수록 (좋은 고객) → 점수 상승
        > - 이탈 기간이 길수록 (재참여 필요성 큼) → 점수 상승
        > - 이 점수가 높은 그룹부터 순서대로 재참여 캠페인을 실시하면 ROI가 극대화됩니다.
        """
    )
    mo.ui.plotly(fig_reeng)
    return (df_reeng, fig_reeng, priority_targets, priority_user_count, threshold)


@app.cell
def chart_channel_segment_quality(df_segments, mo):
    # --- 차트 5: 채널별 파워 유저 비율 비교 ---
    # 유입 채널별로 파워 유저 비율을 비교하여 채널 품질을 평가합니다.
    # 이 차트는 필터 위젯과 독립적으로 항상 전체 데이터를 기반으로 합니다.
    # (특정 채널을 선택하면 해당 채널만 표시되어 비교가 의미 없어지기 때문)

    import plotly.express as px
    import pandas as pd

    # 채널별 파워 유저 비율 집계
    channel_agg = (
        df_segments.groupby("referral_source")
        .apply(
            lambda x: pd.Series({
                "total_users": x["user_count"].sum(),
                "power_users": x[x["activity_segment"] == "power_user"]["user_count"].sum(),
                "churned_users": x[x["activity_segment"] == "churned"]["user_count"].sum(),
                "avg_ltv_krw": (
                    (x["avg_ltv_krw"] * x["user_count"]).sum() / x["user_count"].sum()
                    if x["user_count"].sum() > 0 else 0
                ),
            })
        )
        .reset_index()
    )

    channel_agg["power_user_rate_pct"] = (
        channel_agg["power_users"] / channel_agg["total_users"] * 100
    ).round(1)
    channel_agg["churn_rate_pct"] = (
        channel_agg["churned_users"] / channel_agg["total_users"] * 100
    ).round(1)

    # 파워 유저 비율 기준 내림차순 정렬
    channel_agg = channel_agg.sort_values("power_user_rate_pct", ascending=False)

    df_melt = channel_agg.melt(
        id_vars=["referral_source", "total_users", "avg_ltv_krw"],
        value_vars=["power_user_rate_pct", "churn_rate_pct"],
        var_name="metric",
        value_name="rate_pct",
    )
    metric_labels = {
        "power_user_rate_pct": "파워 유저 비율",
        "churn_rate_pct": "이탈 유저 비율",
    }
    df_melt["metric_label"] = df_melt["metric"].map(metric_labels)

    color_map = {
        "파워 유저 비율": "#0D47A1",
        "이탈 유저 비율": "#EF5350",
    }

    fig_channel = px.bar(
        df_melt,
        x="referral_source",
        y="rate_pct",
        color="metric_label",
        color_discrete_map=color_map,
        barmode="group",
        title="유입 채널별 파워 유저 vs 이탈 유저 비율",
        labels={
            "referral_source": "유입 채널",
            "rate_pct": "사용자 비율 (%)",
            "metric_label": "세그먼트",
        },
        text_auto=".1f",
    )

    fig_channel.update_traces(textposition="outside", textfont_size=10)
    fig_channel.update_layout(
        yaxis=dict(ticksuffix="%", range=[0, 60]),
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )

    # 최고/최저 채널 식별
    best_channel = channel_agg.iloc[0]["referral_source"]
    best_power_rate = channel_agg.iloc[0]["power_user_rate_pct"]
    worst_channel = channel_agg.iloc[-1]["referral_source"]
    worst_power_rate = channel_agg.iloc[-1]["power_user_rate_pct"]

    mo.md(
        f"""
        ## 📢 5. 채널별 사용자 품질 비교

        | 평가 | 채널 | 파워 유저 비율 |
        |------|------|---------------|
        | 🏆 최고 품질 채널 | {best_channel} | {best_power_rate:.1f}% |
        | 📉 최저 품질 채널 | {worst_channel} | {worst_power_rate:.1f}% |

        > **채널 품질 = 파워 유저 비율 + 낮은 이탈률**
        > 동일한 CAC(고객 획득 비용)이라면 파워 유저 비율이 높은 채널이 ROI가 더 높습니다.
        """
    )
    mo.ui.plotly(fig_channel)
    return (best_channel, channel_agg, fig_channel, worst_channel)


@app.cell
def summary_and_evidence(
    ANALYSIS_CONFIG,
    activity_agg,
    best_channel,
    df_filtered,
    filtered_ltv,
    filtered_users,
    mo,
    power_pct,
    priority_user_count,
    revenue_agg,
    risk_pct,
    threshold,
    worst_channel,
):
    # --- 주요 발견 요약 및 완료 증거 생성 ---
    # 분석 결과를 요약하고 harness 검증용 완료 증거 JSON을 생성합니다.

    import json
    import os
    import pandas as pd

    # 수익 집중도: 고가치 세그먼트의 LTV 비중
    hv_data = revenue_agg[revenue_agg["revenue_segment"] == "high_value"]
    high_value_ltv_pct = hv_data["ltv_pct"].values[0] if not hv_data.empty else 0
    high_value_user_pct = hv_data["user_pct"].values[0] if not hv_data.empty else 0

    # 완료 증거 생성
    evidence = {
        "analysis_type": "user_segments_ltv",
        "key_metrics": {
            "total_users_analyzed": int(filtered_users),
            "total_ltv_krw": round(float(filtered_ltv), 0),
            "power_user_pct": round(float(power_pct), 2),
            "churn_risk_pct": round(float(risk_pct), 2),
            "high_value_user_pct": round(float(high_value_user_pct), 2),
            "high_value_ltv_pct": round(float(high_value_ltv_pct), 2),
            "reengagement_targets": int(priority_user_count),
        },
        "insights": {
            "best_channel": best_channel,
            "worst_channel": worst_channel,
            "reengagement_threshold": threshold,
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

        1. **사용자 현황**: 분석 대상 **{filtered_users:,}명** 중
           파워 유저 **{power_pct:.1f}%**, 이탈 위험(휴면+이탈) **{risk_pct:.1f}%**.
           {"파워 유저 비율이 양호하여 핵심 팬 기반이 잘 형성되어 있습니다." if power_pct > 15 else "파워 유저 비율이 낮아 활성 사용자 육성 프로그램 강화가 필요합니다."}

        2. **수익 집중도**: 고가치 사용자 **{high_value_user_pct:.1f}%**가
           전체 LTV의 **{high_value_ltv_pct:.1f}%**를 차지합니다.
           {"수익이 소수 고가치 사용자에게 집중되어, 이들의 이탈 방지가 최우선 과제입니다." if high_value_ltv_pct > 50 else "수익이 비교적 고르게 분산되어 있습니다."}

        3. **재참여 기회**: 재참여 우선순위 점수 ≥ {threshold}인 이탈 위험 그룹이
           **{priority_user_count:,}명**입니다. LTV가 높지만 최근 이탈한 이 그룹을
           재활성화하면 즉각적인 수익 회복이 가능합니다.

        4. **채널 전략**: **{best_channel}** 채널이 파워 유저 전환율이 가장 높습니다.
           **{worst_channel}** 채널은 파워 유저 비율이 가장 낮아 온보딩 개선이 필요합니다.

        5. **총 LTV**: 현재 필터 기준 누적 LTV는 **₩{filtered_ltv:,.0f}**입니다.

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
        marimo export html examples/marimo-user-segments-ltv.py \\
            -o reports/user-segments-report.html

        # PDF 내보내기 (Chromium 필요)
        marimo export pdf examples/marimo-user-segments-ltv.py \\
            -o reports/user-segments-report.pdf
        ```

        > **harness 참고**: `stage:7-report` 단계에서 GitHub Actions가 위 명령을 자동 실행합니다.
        > HTML/PDF는 워크플로 아티팩트로 업로드되며, PR에는 `.py` 소스 파일만 포함됩니다.

        ### 사용 가이드

        이 노트북이 시연하는 핵심 패턴:

        | 패턴 | 설명 |
        |------|------|
        | 사전 집계 테이블 활용 | `fct_user_segments`는 이미 집계된 테이블 → 빠른 로드, 저비용 |
        | 반응형 필터 | 플랫폼·구독·채널 위젯 변경 시 관련 차트 자동 업데이트 |
        | 독립 차트 분리 | 채널 품질 차트는 필터 무관 → 채널 비교의 일관성 유지 |
        | 완료 증거 | `evidence/` JSON으로 분석 완료를 기계적으로 검증 |
        """
    )
    return


if __name__ == "__main__":
    app.run()

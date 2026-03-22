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
FitTrack 앱 DAU/MAU 분석 리포트

이 marimo 노트북은 B2C 모바일 앱(FitTrack)의 일간/월간 활성 사용자 분석을 수행합니다.
7단계 자동 워크플로의 stage:6-analyze 단계에서 에이전트가 생성하는 노트북의 참조 템플릿입니다.

사용법:
  marimo edit examples/marimo-dau-mau-analysis.py
  marimo run examples/marimo-dau-mau-analysis.py

HTML/PDF 내보내기:
  marimo export html examples/marimo-dau-mau-analysis.py -o reports/dau-mau-report.html
  marimo export pdf examples/marimo-dau-mau-analysis.py -o reports/dau-mau-report.pdf
"""

import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium")


@app.cell
def title():
    import marimo as mo

    mo.md(
        """
        # 📊 FitTrack 앱 DAU/MAU 분석 리포트

        **분석 기간**: 2026년 1분기 (2026-01-01 ~ 2026-03-31)
        **분석 대상**: FitTrack 모바일 앱 사용자
        **주요 세그먼트**: 플랫폼 (iOS / Android)

        ---

        ## 분석 개요

        이 리포트는 FitTrack 앱의 사용자 활성도를 DAU(일간 활성 사용자)와 MAU(월간 활성 사용자)
        지표를 통해 분석합니다. 플랫폼별 Stickiness(DAU/MAU 비율) 비교를 통해
        Q2 리텐션 전략 수립을 위한 인사이트를 도출합니다.

        ### 메트릭 정의
        - **DAU**: 해당 일자에 1회 이상 이벤트를 발생시킨 고유 사용자 수
        - **MAU**: 해당 월에 1회 이상 이벤트를 발생시킨 고유 사용자 수
        - **Stickiness**: DAU / MAU (일별 활성 사용자가 월간 활성 사용자에서 차지하는 비율)
        """
    )
    return (mo,)


@app.cell
def config():
    # --- 분석 설정 ---
    # 이 셀에서 분석 파라미터를 정의합니다.
    # 에이전트가 이슈 파싱 결과를 기반으로 이 값들을 자동 설정합니다.

    ANALYSIS_CONFIG = {
        "project_id": "your-gcp-project-id",  # GCP 프로젝트 ID
        "dataset": "fittrack",  # BigQuery 데이터셋
        "start_date": "2026-01-01",  # 분석 시작일
        "end_date": "2026-03-31",  # 분석 종료일
        "exclude_test_users": True,  # 테스트 계정 제외 여부
        "primary_segment": "platform",  # 주요 세그먼트
    }
    return (ANALYSIS_CONFIG,)


@app.cell
def setup_bigquery(ANALYSIS_CONFIG):
    # --- BigQuery 클라이언트 초기화 ---
    # 로컬 실행 시 GOOGLE_APPLICATION_CREDENTIALS 환경변수 또는
    # gcloud auth application-default login 인증을 사용합니다.

    from google.cloud import bigquery

    bq_client = bigquery.Client(project=ANALYSIS_CONFIG["project_id"])

    # 연결 테스트: 데이터셋 존재 여부 확인
    dataset_ref = bq_client.dataset(ANALYSIS_CONFIG["dataset"])
    try:
        bq_client.get_dataset(dataset_ref)
        connection_status = "✅ BigQuery 연결 성공"
    except Exception as e:
        connection_status = f"❌ BigQuery 연결 실패: {e}"

    print(connection_status)
    return (bq_client,)


@app.cell
def query_dau(ANALYSIS_CONFIG, bq_client, mo):
    # --- DAU 데이터 조회 ---
    # dbt mart 모델(fct_daily_active_users)에서 일별 활성 사용자 수를 조회합니다.
    # 테스트 사용자(user_id LIKE 'test_%')는 dbt 모델 단계에서 이미 제외되어 있습니다.

    import pandas as pd

    dau_query = f"""
    SELECT
        activity_date,
        platform,
        dau_count
    FROM `{ANALYSIS_CONFIG["project_id"]}.{ANALYSIS_CONFIG["dataset"]}.fct_daily_active_users`
    WHERE activity_date BETWEEN '{ANALYSIS_CONFIG["start_date"]}' AND '{ANALYSIS_CONFIG["end_date"]}'
    ORDER BY activity_date, platform
    """

    df_dau = bq_client.query(dau_query).to_dataframe()

    # 데이터 타입 변환
    df_dau["activity_date"] = pd.to_datetime(df_dau["activity_date"])
    df_dau["day_of_week"] = df_dau["activity_date"].dt.day_name()
    df_dau["is_weekend"] = df_dau["activity_date"].dt.dayofweek >= 5

    mo.md(
        f"""
        ### 📋 DAU 데이터 요약

        - **조회 행 수**: {len(df_dau):,}행
        - **기간**: {df_dau["activity_date"].min().strftime("%Y-%m-%d")} ~ {df_dau["activity_date"].max().strftime("%Y-%m-%d")}
        - **플랫폼**: {", ".join(df_dau["platform"].unique())}
        """
    )
    return (df_dau,)


@app.cell
def query_mau(ANALYSIS_CONFIG, bq_client, mo):
    # --- MAU 데이터 조회 ---
    # dbt mart 모델(fct_monthly_active_users)에서 월별 활성 사용자 수를 조회합니다.

    import pandas as pd

    mau_query = f"""
    SELECT
        activity_month,
        platform,
        mau_count
    FROM `{ANALYSIS_CONFIG["project_id"]}.{ANALYSIS_CONFIG["dataset"]}.fct_monthly_active_users`
    WHERE activity_month BETWEEN
        DATE_TRUNC(DATE '{ANALYSIS_CONFIG["start_date"]}', MONTH) AND
        DATE_TRUNC(DATE '{ANALYSIS_CONFIG["end_date"]}', MONTH)
    ORDER BY activity_month, platform
    """

    df_mau = bq_client.query(mau_query).to_dataframe()

    # 데이터 타입 변환
    df_mau["activity_month"] = pd.to_datetime(df_mau["activity_month"])
    df_mau["month_label"] = df_mau["activity_month"].dt.strftime("%Y년 %m월")

    mo.md(
        f"""
        ### 📋 MAU 데이터 요약

        - **조회 행 수**: {len(df_mau):,}행
        - **기간**: {df_mau["month_label"].iloc[0]} ~ {df_mau["month_label"].iloc[-1]}
        """
    )
    return (df_mau,)


@app.cell
def chart_dau_trend(df_dau, mo):
    # --- 차트 1: 일별 DAU 추이 (플랫폼별) ---
    # 라인 차트로 플랫폼(iOS/Android)별 일간 활성 사용자 수 추이를 시각화합니다.
    # 주말은 배경 색상으로 구분하여 주말 효과를 시각적으로 확인할 수 있도록 합니다.

    import plotly.express as px
    import plotly.graph_objects as go

    # 플랫폼별 색상 매핑
    color_map = {"ios": "#007AFF", "android": "#34A853"}

    fig_dau = px.line(
        df_dau,
        x="activity_date",
        y="dau_count",
        color="platform",
        color_discrete_map=color_map,
        title="일별 DAU 추이 (플랫폼별)",
        labels={
            "activity_date": "날짜",
            "dau_count": "DAU (명)",
            "platform": "플랫폼",
        },
    )

    # 주말 영역 표시
    weekend_dates = df_dau[df_dau["is_weekend"]]["activity_date"].unique()
    for date in weekend_dates:
        fig_dau.add_vrect(
            x0=date,
            x1=date,
            fillcolor="gray",
            opacity=0.1,
            line_width=0,
        )

    fig_dau.update_layout(
        xaxis_title="날짜",
        yaxis_title="DAU (명)",
        legend_title="플랫폼",
        hovermode="x unified",
        template="plotly_white",
        annotations=[
            dict(
                text="회색 영역 = 주말",
                xref="paper",
                yref="paper",
                x=1.0,
                y=1.05,
                showarrow=False,
                font=dict(size=10, color="gray"),
            )
        ],
    )

    mo.md("## 📈 1. 일별 DAU 추이")
    mo.ui.plotly(fig_dau)
    return (fig_dau,)


@app.cell
def chart_mau_trend(df_mau, mo):
    # --- 차트 2: 월별 MAU 추이 (바 차트) ---
    # 플랫폼별 MAU를 스택 바 차트로 시각화하여 월간 변화와 플랫폼 비중을 함께 확인합니다.

    import plotly.express as px

    color_map = {"ios": "#007AFF", "android": "#34A853"}

    fig_mau = px.bar(
        df_mau,
        x="month_label",
        y="mau_count",
        color="platform",
        color_discrete_map=color_map,
        barmode="group",
        title="월별 MAU 추이 (플랫폼별)",
        labels={
            "month_label": "월",
            "mau_count": "MAU (명)",
            "platform": "플랫폼",
        },
    )

    fig_mau.update_layout(
        xaxis_title="월",
        yaxis_title="MAU (명)",
        legend_title="플랫폼",
        template="plotly_white",
    )

    mo.md("## 📊 2. 월별 MAU 추이")
    mo.ui.plotly(fig_mau)
    return (fig_mau,)


@app.cell
def calculate_stickiness(df_dau, df_mau, mo):
    # --- Stickiness(DAU/MAU 비율) 계산 ---
    # 각 일자의 DAU를 해당 월의 MAU로 나누어 Stickiness를 산출합니다.
    # Stickiness가 높을수록 사용자가 앱을 자주, 꾸준히 사용한다는 의미입니다.
    # 일반적으로 B2C 앱의 Stickiness는 10~25% 범위입니다.

    import pandas as pd

    # DAU에 월 정보 추가
    df_stickiness = df_dau.copy()
    df_stickiness["activity_month"] = df_stickiness["activity_date"].dt.to_period("M").dt.to_timestamp()

    # MAU와 조인하여 Stickiness 계산
    df_stickiness = df_stickiness.merge(
        df_mau[["activity_month", "platform", "mau_count"]],
        on=["activity_month", "platform"],
        how="left",
    )
    df_stickiness["stickiness"] = (
        df_stickiness["dau_count"] / df_stickiness["mau_count"]
    )
    df_stickiness["stickiness_pct"] = df_stickiness["stickiness"] * 100

    # 플랫폼별 평균 Stickiness 요약
    avg_stickiness = (
        df_stickiness.groupby("platform")["stickiness_pct"]
        .mean()
        .round(1)
    )

    mo.md(
        f"""
        ### 📋 Stickiness 요약

        | 플랫폼 | 평균 Stickiness |
        |--------|----------------|
        | iOS | {avg_stickiness.get("ios", "N/A")}% |
        | Android | {avg_stickiness.get("android", "N/A")}% |

        > **해석**: Stickiness가 20% 이상이면 일반적인 B2C 앱 대비 양호한 수준입니다.
        """
    )
    return (df_stickiness,)


@app.cell
def chart_stickiness_trend(df_stickiness, mo):
    # --- 차트 3: DAU/MAU 비율(Stickiness) 트렌드 ---
    # 플랫폼별 Stickiness 추이를 라인 차트로 시각화합니다.
    # 7일 이동평균을 함께 표시하여 노이즈를 줄이고 트렌드를 파악합니다.

    import plotly.express as px
    import plotly.graph_objects as go

    color_map = {"ios": "#007AFF", "android": "#34A853"}

    # 7일 이동평균 계산
    df_plot = df_stickiness.copy()
    df_plot["stickiness_ma7"] = (
        df_plot.groupby("platform")["stickiness_pct"]
        .transform(lambda x: x.rolling(window=7, min_periods=1).mean())
    )

    fig_stickiness = go.Figure()

    for platform, color in color_map.items():
        platform_data = df_plot[df_plot["platform"] == platform]

        # 일별 원본 (투명하게)
        fig_stickiness.add_trace(
            go.Scatter(
                x=platform_data["activity_date"],
                y=platform_data["stickiness_pct"],
                mode="markers",
                marker=dict(color=color, size=3, opacity=0.3),
                name=f"{platform} (일별)",
                showlegend=False,
            )
        )

        # 7일 이동평균 (굵은 선)
        fig_stickiness.add_trace(
            go.Scatter(
                x=platform_data["activity_date"],
                y=platform_data["stickiness_ma7"],
                mode="lines",
                line=dict(color=color, width=2.5),
                name=f"{platform} (7일 이동평균)",
            )
        )

    fig_stickiness.update_layout(
        title="DAU/MAU 비율 (Stickiness) 트렌드 — 플랫폼별",
        xaxis_title="날짜",
        yaxis_title="Stickiness (%)",
        legend_title="플랫폼",
        hovermode="x unified",
        template="plotly_white",
        yaxis=dict(ticksuffix="%"),
    )

    mo.md("## 📉 3. Stickiness (DAU/MAU) 트렌드")
    mo.ui.plotly(fig_stickiness)
    return (fig_stickiness,)


@app.cell
def weekday_analysis(df_dau, mo):
    # --- 추가 분석: 요일별 DAU 패턴 ---
    # 이슈 요청에 "주말 효과" 확인이 포함되어 있으므로 요일별 패턴을 분석합니다.
    # 한국어 요일명으로 표시하며, 월요일부터 일요일 순서를 유지합니다.

    import plotly.express as px

    # 요일 순서 및 한국어 매핑
    day_order = [
        "Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday",
    ]
    day_kr = {
        "Monday": "월", "Tuesday": "화", "Wednesday": "수",
        "Thursday": "목", "Friday": "금", "Saturday": "토", "Sunday": "일",
    }

    df_weekday = (
        df_dau.groupby(["day_of_week", "platform"])["dau_count"]
        .mean()
        .round(0)
        .reset_index()
    )
    df_weekday["day_kr"] = df_weekday["day_of_week"].map(day_kr)
    df_weekday["day_order"] = df_weekday["day_of_week"].map(
        {d: i for i, d in enumerate(day_order)}
    )
    df_weekday = df_weekday.sort_values("day_order")

    color_map = {"ios": "#007AFF", "android": "#34A853"}

    fig_weekday = px.bar(
        df_weekday,
        x="day_kr",
        y="dau_count",
        color="platform",
        color_discrete_map=color_map,
        barmode="group",
        title="요일별 평균 DAU (플랫폼별)",
        labels={
            "day_kr": "요일",
            "dau_count": "평균 DAU (명)",
            "platform": "플랫폼",
        },
    )

    fig_weekday.update_layout(
        template="plotly_white",
        xaxis=dict(categoryorder="array", categoryarray=list(day_kr.values())),
    )

    # 주말 대비 평일 DAU 비율 계산
    weekend_avg = df_dau[df_dau["is_weekend"]]["dau_count"].mean()
    weekday_avg = df_dau[~df_dau["is_weekend"]]["dau_count"].mean()
    weekend_effect = ((weekend_avg / weekday_avg) - 1) * 100

    mo.md(
        f"""
        ## 📅 4. 요일별 DAU 패턴

        주말 효과: 주말 평균 DAU가 평일 대비 **{weekend_effect:+.1f}%** {"높습니다" if weekend_effect > 0 else "낮습니다"}.
        """
    )
    mo.ui.plotly(fig_weekday)
    return (fig_weekday, weekend_effect)


@app.cell
def summary_findings(df_dau, df_mau, df_stickiness, weekend_effect, mo):
    # --- 주요 발견 요약 ---
    # 이슈 요청의 기대 산출물 중 "주요 발견 요약 (3~5문장)"에 해당합니다.
    # 분석 결과를 기반으로 핵심 인사이트를 정리합니다.

    import pandas as pd

    # 핵심 통계 산출
    total_dau_avg = df_dau.groupby("activity_date")["dau_count"].sum().mean()
    ios_stickiness = df_stickiness[df_stickiness["platform"] == "ios"]["stickiness_pct"].mean()
    android_stickiness = df_stickiness[df_stickiness["platform"] == "android"]["stickiness_pct"].mean()
    stickiness_gap = ios_stickiness - android_stickiness

    # 월별 MAU 추이 (증감)
    mau_total = df_mau.groupby("activity_month")["mau_count"].sum().reset_index()
    if len(mau_total) >= 2:
        mau_change = (
            (mau_total["mau_count"].iloc[-1] / mau_total["mau_count"].iloc[0]) - 1
        ) * 100
        mau_trend_text = f"1분기 동안 전체 MAU는 **{mau_change:+.1f}%** 변화했습니다."
    else:
        mau_trend_text = "MAU 추이 분석에 충분한 데이터가 없습니다."

    mo.md(
        f"""
        ---

        ## 🔍 주요 발견 요약

        1. **전체 DAU**: 1분기 평균 일간 활성 사용자 수는 **{total_dau_avg:,.0f}명**입니다.
        2. **MAU 추이**: {mau_trend_text}
        3. **Stickiness 비교**: iOS의 평균 Stickiness({ios_stickiness:.1f}%)가 Android({android_stickiness:.1f}%)보다
           **{stickiness_gap:.1f}%p** {"높아" if stickiness_gap > 0 else "낮아"}, Android 사용자의 stickiness가 {"상대적으로 낮다는 가설이 지지됩니다" if stickiness_gap > 0 else "iOS보다 높은 것으로 나타났습니다"}.
        4. **주말 효과**: 주말 DAU가 평일 대비 **{weekend_effect:+.1f}%** {"상승하여" if weekend_effect > 0 else "하락하여"}, 여가 시간에 앱 사용이 {"증가" if weekend_effect > 0 else "감소"}하는 패턴이 확인됩니다.
        5. **권고사항**: Android 플랫폼의 Stickiness 개선을 위해 푸시 알림 최적화 및 Android 전용 UX 개선을 Q2 리텐션 전략에 포함할 것을 권고합니다.

        ---

        > 이 리포트는 FitTrack 합성 데이터를 기반으로 생성되었습니다.
        > 생성일: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}
        """
    )
    return


@app.cell
def export_info(mo):
    # --- 내보내기 안내 ---
    # PR에는 이 .py 소스 파일만 포함되며,
    # HTML/PDF 내보내기 파일은 GitHub Actions 아티팩트로 별도 첨부됩니다.

    mo.md(
        """
        ---

        ### 💡 리포트 내보내기

        이 노트북을 HTML 또는 PDF로 내보내려면 다음 명령어를 사용합니다:

        ```bash
        # HTML 내보내기
        marimo export html examples/marimo-dau-mau-analysis.py -o reports/dau-mau-report.html

        # PDF 내보내기 (Chromium 필요)
        marimo export pdf examples/marimo-dau-mau-analysis.py -o reports/dau-mau-report.pdf
        ```

        > **참고**: PR에는 `.py` 소스 파일만 포함됩니다. HTML/PDF는 GitHub Actions 아티팩트로 업로드됩니다.
        """
    )
    return


if __name__ == "__main__":
    app.run()

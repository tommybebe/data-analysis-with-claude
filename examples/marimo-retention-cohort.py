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
FitTrack 코호트 리텐션 분석 리포트

이 marimo 노트북은 B2C 모바일 앱(FitTrack)의 코호트 기반 리텐션 분석을 수행합니다.
가입 주차(cohort_week)를 기준으로 N주 후 잔존율을 계산하고 히트맵으로 시각화합니다.

dbt mart 모델 fct_retention_cohort를 사용합니다.
7단계 자동 워크플로의 stage:6-analyze 단계에서 에이전트가 생성하는 노트북의 참조 템플릿입니다.

사용법:
  marimo edit examples/marimo-retention-cohort.py
  marimo run examples/marimo-retention-cohort.py

HTML/PDF 내보내기:
  marimo export html examples/marimo-retention-cohort.py -o reports/retention-report.html
"""

import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium")


@app.cell
def title():
    import marimo as mo

    mo.md(
        """
        # 📊 FitTrack 코호트 리텐션 분석

        **분석 기간**: 2026년 1분기 가입 코호트 (2026-01-01 ~ 2026-03-31)
        **분석 대상**: FitTrack 모바일 앱 신규 가입 사용자
        **추적 기간**: 가입 후 최대 12주

        ---

        ## 분석 개요

        코호트 리텐션 분석은 같은 기간에 가입한 사용자 그룹(코호트)이
        이후 주차별로 얼마나 남아있는지 추적합니다.

        ### 메트릭 정의
        - **코호트**: 같은 주에 가입한 사용자 그룹 (가입 주 월요일 기준)
        - **Week-0 잔존율**: 가입 주에 이벤트를 발생시킨 비율 (항상 100%)
        - **Week-N 잔존율**: 가입 N주 후에도 이벤트를 발생시킨 사용자 비율
        - **잔존율 기준**: 해당 주에 1회 이상 이벤트 발생 시 "잔존"으로 간주

        ### 분석 질문
        1. 코호트별 초기 이탈률(Week-1, Week-2)은 얼마인가?
        2. 리텐션이 안정화되는 시점(plateau)은 언제인가?
        3. 최근 코호트와 초기 코호트 사이에 리텐션 차이가 있는가?
        """
    )
    return (mo,)


@app.cell
def config():
    # --- 분석 설정 ---
    # 에이전트가 이슈 파싱 결과를 기반으로 이 값들을 자동 설정합니다.

    ANALYSIS_CONFIG = {
        "project_id": "your-gcp-project-id",  # GCP 프로젝트 ID
        "dataset": "fittrack",  # BigQuery 데이터셋
        # 코호트 필터: 이 기간에 가입한 코호트만 분석
        "cohort_start": "2026-01-01",
        "cohort_end": "2026-03-31",
        # 최대 추적 주차 (fct_retention_cohort는 12주까지 지원)
        "max_weeks": 12,
    }
    return (ANALYSIS_CONFIG,)


@app.cell
def setup_bigquery(ANALYSIS_CONFIG):
    # --- BigQuery 클라이언트 초기화 ---
    # 로컬 실행: gcloud auth application-default login 인증 필요
    # CI/CD 실행: GOOGLE_APPLICATION_CREDENTIALS 환경변수 (서비스 계정 JSON 경로)

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
def query_retention(ANALYSIS_CONFIG, bq_client, mo):
    # --- 리텐션 데이터 조회 ---
    # fct_retention_cohort 마트 모델에서 코호트별 주차별 잔존율을 조회합니다.
    # 이 모델은 가입 주 기준으로 최대 12주 후까지의 잔존율을 사전 계산합니다.

    import pandas as pd

    retention_query = f"""
    SELECT
        cohort_week,
        cohort_users,
        weeks_since_signup,
        retained_users,
        retention_rate
    FROM `{ANALYSIS_CONFIG["project_id"]}.{ANALYSIS_CONFIG["dataset"]}.fct_retention_cohort`
    WHERE
        cohort_week BETWEEN '{ANALYSIS_CONFIG["cohort_start"]}' AND '{ANALYSIS_CONFIG["cohort_end"]}'
        AND weeks_since_signup <= {ANALYSIS_CONFIG["max_weeks"]}
    ORDER BY cohort_week, weeks_since_signup
    """

    df_retention = bq_client.query(retention_query).to_dataframe()

    # 데이터 타입 변환
    df_retention["cohort_week"] = pd.to_datetime(df_retention["cohort_week"])
    df_retention["cohort_label"] = df_retention["cohort_week"].dt.strftime("%m/%d")
    df_retention["retention_pct"] = (df_retention["retention_rate"] * 100).round(1)

    # 조회 결과 요약
    total_cohorts = df_retention["cohort_week"].nunique()
    total_users = df_retention[df_retention["weeks_since_signup"] == 0]["cohort_users"].sum()

    mo.md(
        f"""
        ### 📋 리텐션 데이터 요약

        - **코호트 수**: {total_cohorts}개 주차 코호트
        - **총 분석 사용자**: {total_users:,}명
        - **추적 기간**: 가입 후 최대 {ANALYSIS_CONFIG["max_weeks"]}주
        """
    )
    return (df_retention,)


@app.cell
def build_cohort_matrix(df_retention, mo):
    # --- 코호트 매트릭스 생성 ---
    # 히트맵 시각화를 위해 코호트(행) x 주차(열) 피벗 테이블을 생성합니다.
    # 셀 값은 잔존율(%)입니다.

    import pandas as pd

    # 피벗 테이블: 행=코호트, 열=주차
    df_pivot = df_retention.pivot_table(
        index="cohort_label",
        columns="weeks_since_signup",
        values="retention_pct",
        aggfunc="mean",
    )

    # 코호트 시간 순으로 정렬 (최신 코호트가 아래)
    cohort_order = (
        df_retention[["cohort_week", "cohort_label"]]
        .drop_duplicates()
        .sort_values("cohort_week")["cohort_label"]
        .tolist()
    )
    df_pivot = df_pivot.reindex(cohort_order)

    # 열 이름을 "Week N" 형식으로 변경
    df_pivot.columns = [f"Week {int(w)}" for w in df_pivot.columns]

    mo.md(
        f"""
        ### 코호트 매트릭스 ({df_pivot.shape[0]}개 코호트 × {df_pivot.shape[1]}주차)

        행: 가입 주차 (월/일 형식), 열: 가입 후 N주차
        """
    )
    return (df_pivot,)


@app.cell
def chart_heatmap(df_pivot, mo):
    # --- 차트 1: 코호트 리텐션 히트맵 ---
    # 코호트(가입 주)별 주차별 잔존율을 색상으로 표현하는 히트맵입니다.
    # 색상이 진할수록 잔존율이 높습니다.
    # Week-0은 항상 100%이므로 다른 색으로 표시합니다.

    import plotly.graph_objects as go
    import numpy as np

    z_values = df_pivot.values
    x_labels = list(df_pivot.columns)
    y_labels = list(df_pivot.index)

    # 히트맵 텍스트: 잔존율 숫자 표시 (NaN은 공백)
    text_values = [
        [f"{v:.0f}%" if not np.isnan(v) else "" for v in row]
        for row in z_values
    ]

    fig_heatmap = go.Figure(
        data=go.Heatmap(
            z=z_values,
            x=x_labels,
            y=y_labels,
            text=text_values,
            texttemplate="%{text}",
            textfont={"size": 11},
            colorscale=[
                [0.0, "#FFF3E0"],   # 0% — 연한 주황
                [0.1, "#FFCC80"],   # 10%
                [0.3, "#FF9800"],   # 30%
                [0.5, "#4CAF50"],   # 50% — 초록
                [0.7, "#2196F3"],   # 70%
                [1.0, "#0D47A1"],   # 100% — 진한 파랑
            ],
            zmin=0,
            zmax=100,
            colorbar=dict(
                title="잔존율 (%)",
                ticksuffix="%",
            ),
            hovertemplate=(
                "코호트: %{y}<br>"
                "주차: %{x}<br>"
                "잔존율: %{z:.1f}%<extra></extra>"
            ),
        )
    )

    fig_heatmap.update_layout(
        title={
            "text": "코호트 리텐션 히트맵 — 가입 주차별 잔존율",
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis=dict(title="가입 후 주차", side="top"),
        yaxis=dict(title="가입 코호트 (월/일)", autorange="reversed"),
        template="plotly_white",
        height=max(300, len(df_pivot) * 35 + 100),
    )

    mo.md("## 🔥 1. 코호트 리텐션 히트맵")
    mo.ui.plotly(fig_heatmap)
    return (fig_heatmap,)


@app.cell
def chart_retention_curves(df_retention, mo):
    # --- 차트 2: 코호트별 리텐션 커브 ---
    # 각 코호트의 주차별 잔존율을 라인 차트로 시각화합니다.
    # 코호트 간 리텐션 패턴 차이를 비교할 수 있습니다.

    import plotly.express as px

    # 색상 팔레트: 시간 순으로 색이 변함 (최초 코호트 → 최신 코호트)
    fig_curves = px.line(
        df_retention.sort_values(["cohort_week", "weeks_since_signup"]),
        x="weeks_since_signup",
        y="retention_pct",
        color="cohort_label",
        markers=True,
        title="코호트별 리텐션 커브",
        labels={
            "weeks_since_signup": "가입 후 주차",
            "retention_pct": "잔존율 (%)",
            "cohort_label": "가입 코호트",
        },
    )

    fig_curves.update_layout(
        xaxis=dict(
            tickmode="linear",
            tick0=0,
            dtick=1,
            title="가입 후 주차",
        ),
        yaxis=dict(
            title="잔존율 (%)",
            ticksuffix="%",
            range=[0, 105],
        ),
        template="plotly_white",
        hovermode="x unified",
        legend=dict(
            title="가입 코호트",
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.01,
        ),
    )

    mo.md("## 📉 2. 코호트별 리텐션 커브")
    mo.ui.plotly(fig_curves)
    return (fig_curves,)


@app.cell
def avg_retention_by_week(df_retention, mo):
    # --- 차트 3: 주차별 평균 잔존율 ---
    # 모든 코호트의 주차별 평균 잔존율을 계산하여
    # 전체 리텐션 패턴의 기준선(baseline)을 파악합니다.

    import plotly.graph_objects as go
    import pandas as pd

    # 주차별 가중평균 잔존율 계산 (코호트 크기를 가중치로 사용)
    df_weighted = (
        df_retention.groupby("weeks_since_signup")
        .apply(
            lambda x: pd.Series({
                "avg_retention": (
                    (x["retained_users"].sum() / x["cohort_users"].sum()) * 100
                ).round(1),
                "total_users": x["cohort_users"].sum(),
            })
        )
        .reset_index()
    )

    fig_avg = go.Figure()

    # 잔존율 바 차트
    fig_avg.add_trace(
        go.Bar(
            x=df_weighted["weeks_since_signup"],
            y=df_weighted["avg_retention"],
            name="평균 잔존율",
            marker_color="#2196F3",
            text=[f"{v:.1f}%" for v in df_weighted["avg_retention"]],
            textposition="outside",
        )
    )

    fig_avg.update_layout(
        title="주차별 평균 잔존율 (전체 코호트 가중평균)",
        xaxis=dict(
            title="가입 후 주차",
            tickmode="linear",
            tick0=0,
            dtick=1,
        ),
        yaxis=dict(
            title="평균 잔존율 (%)",
            ticksuffix="%",
            range=[0, 115],
        ),
        template="plotly_white",
        showlegend=False,
    )

    # 주요 통계 산출
    week1_retention = df_weighted[df_weighted["weeks_since_signup"] == 1]["avg_retention"].iloc[0] if 1 in df_weighted["weeks_since_signup"].values else None
    week4_retention = df_weighted[df_weighted["weeks_since_signup"] == 4]["avg_retention"].iloc[0] if 4 in df_weighted["weeks_since_signup"].values else None
    week8_retention = df_weighted[df_weighted["weeks_since_signup"] == 8]["avg_retention"].iloc[0] if 8 in df_weighted["weeks_since_signup"].values else None

    mo.md(
        f"""
        ## 📊 3. 주차별 평균 잔존율

        | 시점 | 평균 잔존율 |
        |------|------------|
        | Week-1 (1주 후) | {f"{week1_retention:.1f}%" if week1_retention else "데이터 없음"} |
        | Week-4 (1개월 후) | {f"{week4_retention:.1f}%" if week4_retention else "데이터 없음"} |
        | Week-8 (2개월 후) | {f"{week8_retention:.1f}%" if week8_retention else "데이터 없음"} |
        """
    )
    mo.ui.plotly(fig_avg)
    return (df_weighted, fig_avg, week1_retention, week4_retention, week8_retention)


@app.cell
def summary_findings(df_retention, df_weighted, week1_retention, week4_retention, week8_retention, mo):
    # --- 주요 발견 요약 ---
    # 이슈 요청의 기대 산출물 중 "주요 발견 요약"에 해당합니다.

    import pandas as pd

    # 최초 이탈률 (Week-0 → Week-1 감소율)
    early_churn_pct = 100 - week1_retention if week1_retention else None

    # 리텐션 플래토 감지: 연속 2주간 변화량이 2% 미만인 첫 주차
    plateau_week = None
    if len(df_weighted) >= 3:
        for i in range(1, len(df_weighted) - 1):
            curr = df_weighted.iloc[i]["avg_retention"]
            next_val = df_weighted.iloc[i + 1]["avg_retention"]
            if abs(curr - next_val) < 2.0:
                plateau_week = int(df_weighted.iloc[i]["weeks_since_signup"])
                break

    # 최근 3개 코호트 vs 최초 3개 코호트 Week-4 잔존율 비교
    cohorts_sorted = df_retention["cohort_week"].drop_duplicates().sort_values()
    early_cohorts = cohorts_sorted.iloc[:3]
    recent_cohorts = cohorts_sorted.iloc[-3:]

    week4_data = df_retention[df_retention["weeks_since_signup"] == 4]
    early_w4 = week4_data[week4_data["cohort_week"].isin(early_cohorts)]["retention_pct"].mean()
    recent_w4 = week4_data[week4_data["cohort_week"].isin(recent_cohorts)]["retention_pct"].mean()
    cohort_improvement = recent_w4 - early_w4

    mo.md(
        f"""
        ---

        ## 🔍 주요 발견 요약

        1. **초기 이탈률**: Week-1에 평균 **{early_churn_pct:.1f}%**의 신규 사용자가 이탈합니다.
           이는 온보딩 경험 개선의 핵심 타깃 구간입니다.

        2. **1개월 리텐션**: Week-4 평균 잔존율은 **{week4_retention:.1f}%**로,
           {"B2C 모바일 앱 업계 평균(15-20%) 대비 양호한 수준입니다." if week4_retention and week4_retention > 15 else "업계 평균(15-20%) 대비 개선 여지가 있습니다."}

        3. **리텐션 안정화**: {"Week-" + str(plateau_week) + " 이후 잔존율이 안정화됩니다 (주간 변화 < 2%)." if plateau_week else "분석 기간 내 명확한 안정화 시점이 관찰되지 않습니다."}
           이 이후로도 앱을 사용하는 사용자는 장기 충성 고객입니다.

        4. **코호트 개선 추이**: 최근 코호트의 Week-4 잔존율({recent_w4:.1f}%)이 초기 코호트({early_w4:.1f}%)보다
           **{cohort_improvement:+.1f}%p** {"높아" if cohort_improvement > 0 else "낮아"}, 제품 개선의 효과가 {"확인됩니다" if cohort_improvement > 0 else "아직 리텐션에 반영되지 않았습니다"}.

        5. **권고사항**:
           - **Week-1 이탈 방지**: 가입 후 첫 7일 이내 핵심 기능 경험을 유도하는 온보딩 시퀀스 강화
           - **Week-4 재활성화**: 한 달 미접속 사용자 대상 개인화 푸시 알림 캠페인
           - **장기 충성 고객**: {"Week-" + str(plateau_week) + " 이후 잔존 사용자" if plateau_week else "고리텐션 사용자"} 대상 프리미엄 전환 유도

        ---

        > 이 리포트는 FitTrack 합성 데이터를 기반으로 생성되었습니다.
        > 생성일: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}
        """
    )
    return


@app.cell
def export_info(mo):
    # --- 내보내기 안내 ---

    mo.md(
        """
        ---

        ### 💡 리포트 내보내기

        ```bash
        # HTML 내보내기
        marimo export html examples/marimo-retention-cohort.py -o reports/retention-report.html

        # PDF 내보내기 (Chromium 필요)
        marimo export pdf examples/marimo-retention-cohort.py -o reports/retention-report.pdf
        ```

        > **참고**: PR에는 `.py` 소스 파일만 포함됩니다.
        > HTML/PDF는 GitHub Actions 워크플로의 `stage:7-report` 단계에서 아티팩트로 업로드됩니다.
        """
    )
    return


if __name__ == "__main__":
    app.run()

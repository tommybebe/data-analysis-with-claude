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
FitTrack 데이터 탐색 노트북

dbt 모델 실행 후 데이터 품질과 분포를 확인하기 위한 탐색적 분석 노트북입니다.
stage:5-extract 이후, 본격적인 분석(stage:6-analyze) 전에 데이터를 점검하는 용도로 사용합니다.

이 노트북은 에이전트가 참조하는 탐색 분석 템플릿으로,
수강생이 Module 2(스킬/훅)에서 /analyze 스킬의 기반으로 활용합니다.

사용법:
  marimo edit examples/marimo-data-exploration.py
"""

import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium")


@app.cell
def title():
    import marimo as mo

    mo.md(
        """
        # 🔎 FitTrack 데이터 탐색 및 품질 점검

        dbt 모델 실행 결과의 데이터 품질을 점검하고,
        분석에 앞서 데이터 분포를 확인하는 탐색적 분석 노트북입니다.

        **점검 항목**:
        1. 원본 테이블 행 수 및 기간 확인
        2. 플랫폼별 사용자 분포
        3. 일별 이벤트 수 분포 (이상치 탐지)
        4. dbt mart 모델 출력 검증
        """
    )
    return (mo,)


@app.cell
def config():
    # --- 프로젝트 설정 ---
    # BigQuery 프로젝트 ID와 데이터셋명을 설정합니다.

    PROJECT_ID = "your-gcp-project-id"
    DATASET = "fittrack"
    return DATASET, PROJECT_ID


@app.cell
def setup_client(PROJECT_ID):
    # --- BigQuery 클라이언트 ---

    from google.cloud import bigquery

    client = bigquery.Client(project=PROJECT_ID)
    return (client,)


@app.cell
def check_row_counts(DATASET, PROJECT_ID, client, mo):
    # --- 점검 1: 테이블별 행 수 확인 ---
    # 합성 데이터 생성 후 각 테이블의 행 수가 예상 범위 내인지 확인합니다.
    # 예상값: raw_events ~500,000 / raw_users ~10,000 / raw_sessions ~150,000

    import pandas as pd

    tables = ["raw_events", "raw_users", "raw_sessions"]
    expected_counts = {
        "raw_events": 500_000,
        "raw_users": 10_000,
        "raw_sessions": 150_000,
    }

    row_counts = []
    for table in tables:
        query = f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{DATASET}.{table}`"
        result = client.query(query).to_dataframe()
        actual = result["cnt"].iloc[0]
        expected = expected_counts[table]
        deviation = ((actual / expected) - 1) * 100
        status = "✅" if abs(deviation) < 20 else "⚠️"
        row_counts.append({
            "테이블": table,
            "실제 행 수": f"{actual:,}",
            "예상 행 수": f"{expected:,}",
            "편차": f"{deviation:+.1f}%",
            "상태": status,
        })

    df_counts = pd.DataFrame(row_counts)

    mo.md("## 1️⃣ 테이블별 행 수 확인")
    mo.ui.table(df_counts)
    return (df_counts,)


@app.cell
def check_date_range(DATASET, PROJECT_ID, client, mo):
    # --- 점검 2: 데이터 기간 확인 ---
    # 각 테이블의 날짜 범위가 분석 기간을 포함하는지 확인합니다.

    date_query = f"""
    SELECT
        'raw_events' AS table_name,
        MIN(event_date) AS min_date,
        MAX(event_date) AS max_date
    FROM `{PROJECT_ID}.{DATASET}.raw_events`
    UNION ALL
    SELECT
        'raw_sessions',
        MIN(session_date),
        MAX(session_date)
    FROM `{PROJECT_ID}.{DATASET}.raw_sessions`
    UNION ALL
    SELECT
        'raw_users',
        MIN(signup_date),
        MAX(signup_date)
    FROM `{PROJECT_ID}.{DATASET}.raw_users`
    """

    df_dates = client.query(date_query).to_dataframe()

    mo.md(
        f"""
        ## 2️⃣ 데이터 기간 확인

        분석 대상 기간(2026-01-01 ~ 2026-03-31)이 데이터 범위 내에 포함되어야 합니다.
        """
    )
    mo.ui.table(df_dates)
    return (df_dates,)


@app.cell
def check_platform_distribution(DATASET, PROJECT_ID, client, mo):
    # --- 점검 3: 플랫폼별 사용자 분포 ---
    # 예상 비율: iOS 55%, Android 45% (한국 시장 반영)

    import plotly.express as px

    platform_query = f"""
    SELECT
        platform,
        COUNT(DISTINCT user_id) AS user_count
    FROM `{PROJECT_ID}.{DATASET}.raw_users`
    WHERE is_active = TRUE
    GROUP BY platform
    """

    df_platform = client.query(platform_query).to_dataframe()
    total = df_platform["user_count"].sum()
    df_platform["비율"] = (df_platform["user_count"] / total * 100).round(1)

    fig_platform = px.pie(
        df_platform,
        values="user_count",
        names="platform",
        title="활성 사용자 플랫폼 분포",
        color="platform",
        color_discrete_map={"ios": "#007AFF", "android": "#34A853"},
    )

    mo.md("## 3️⃣ 플랫폼별 사용자 분포")
    mo.ui.plotly(fig_platform)
    return (df_platform,)


@app.cell
def check_daily_events(DATASET, PROJECT_ID, client, mo):
    # --- 점검 4: 일별 이벤트 수 분포 ---
    # 합성 데이터의 이벤트 수가 일별로 안정적인지, 이상치가 없는지 확인합니다.
    # 급격한 증감이 있다면 데이터 생성 스크립트 검토가 필요합니다.

    import plotly.express as px

    daily_events_query = f"""
    SELECT
        event_date,
        COUNT(*) AS event_count,
        COUNT(DISTINCT user_id) AS unique_users
    FROM `{PROJECT_ID}.{DATASET}.raw_events`
    WHERE event_date BETWEEN '2026-01-01' AND '2026-03-31'
    GROUP BY event_date
    ORDER BY event_date
    """

    df_daily = client.query(daily_events_query).to_dataframe()

    fig_daily = px.line(
        df_daily,
        x="event_date",
        y="event_count",
        title="일별 총 이벤트 수",
        labels={"event_date": "날짜", "event_count": "이벤트 수"},
    )
    fig_daily.update_layout(template="plotly_white")

    # 기초 통계로 이상치 여부 판단
    mean_events = df_daily["event_count"].mean()
    std_events = df_daily["event_count"].std()
    outliers = df_daily[
        (df_daily["event_count"] > mean_events + 3 * std_events)
        | (df_daily["event_count"] < mean_events - 3 * std_events)
    ]

    outlier_msg = (
        f"⚠️ 이상치 {len(outliers)}건 감지 (3σ 기준)"
        if len(outliers) > 0
        else "✅ 이상치 없음 (3σ 기준)"
    )

    mo.md(
        f"""
        ## 4️⃣ 일별 이벤트 수 분포

        - 일평균 이벤트 수: **{mean_events:,.0f}**건
        - 표준편차: **{std_events:,.0f}**건
        - 이상치 점검: {outlier_msg}
        """
    )
    mo.ui.plotly(fig_daily)
    return (df_daily,)


@app.cell
def check_mart_models(DATASET, PROJECT_ID, client, mo):
    # --- 점검 5: dbt mart 모델 출력 검증 ---
    # fct_daily_active_users와 fct_monthly_active_users 테이블이
    # 정상적으로 생성되었는지 확인합니다.

    import pandas as pd

    mart_checks = []

    for mart_table in ["fct_daily_active_users", "fct_monthly_active_users"]:
        try:
            query = f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{DATASET}.{mart_table}`"
            result = client.query(query).to_dataframe()
            count = result["cnt"].iloc[0]
            mart_checks.append({
                "mart 모델": mart_table,
                "행 수": f"{count:,}",
                "상태": "✅ 정상" if count > 0 else "❌ 비어 있음",
            })
        except Exception as e:
            mart_checks.append({
                "mart 모델": mart_table,
                "행 수": "—",
                "상태": f"❌ 조회 실패: {str(e)[:50]}",
            })

    df_marts = pd.DataFrame(mart_checks)

    mo.md(
        """
        ## 5️⃣ dbt Mart 모델 검증

        `dbt run` 실행 후 생성된 mart 테이블을 확인합니다.
        행 수가 0이거나 조회에 실패하면 `dbt run`을 다시 실행하세요.
        """
    )
    mo.ui.table(df_marts)
    return (df_marts,)


@app.cell
def quality_summary(mo):
    # --- 품질 점검 요약 ---

    mo.md(
        """
        ---

        ## ✅ 데이터 품질 점검 요약

        위 점검 항목들을 모두 통과하면 분석 단계(stage:6-analyze)를 진행할 수 있습니다.

        **다음 단계:**
        1. 모든 점검 항목이 ✅인지 확인
        2. 이상치나 ❌ 항목이 있다면 원인을 파악하고 데이터 재생성 또는 dbt 재실행
        3. 점검 완료 후 `marimo-dau-mau-analysis.py` 노트북에서 본격 분석 수행

        > 이 노트북은 데이터 탐색 용도이며, 최종 리포트에는 포함되지 않습니다.
        """
    )
    return


if __name__ == "__main__":
    app.run()

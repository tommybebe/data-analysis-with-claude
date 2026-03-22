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
harness 엔지니어링 분석 노트북 템플릿

이 노트북은 두 가지 목적으로 설계되었습니다:

1. **에이전트 생성 템플릿**: stage:6-analyze 단계에서 Claude가 이 구조를 참조하여
   새 분석 노트북을 생성합니다. 에이전트는 config 셀만 수정하고 나머지 패턴은 유지합니다.

2. **교육 목적**: harness와 marimo 노트북이 어떻게 연동되는지 단계별로 시연합니다.
   각 셀의 주석에 "harness 패턴" 설명이 포함되어 있습니다.

## harness 연동 흐름

```
stage:4-spec  → 이 파일 구조를 참조하여 분석 스펙 작성
stage:5-extract → dbt 실행으로 mart 데이터 준비
stage:6-analyze → ANALYSIS_CONFIG 값 채워서 노트북 완성
stage:7-report  → marimo export html/pdf, evidence JSON 검증
```

사용법:
  marimo edit examples/marimo-harness-template.py
"""

import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium")


@app.cell
def title():
    import marimo as mo

    mo.md(
        """
        # 🔧 harness 분석 노트북 템플릿

        이 노트북은 **에이전트가 생성하는 분석 노트북의 표준 구조**를 시연합니다.

        ---

        ## 이 템플릿의 역할

        `stage:6-analyze` 단계에서 Claude는 이 구조를 참조하여 분석 노트북을 생성합니다:

        ```
        [이슈 파싱 결과]
           ↓
        [ANALYSIS_CONFIG 딕셔너리 값 설정]  ← 에이전트가 수정하는 유일한 부분
           ↓
        [나머지 셀: 쿼리 → 분석 → 시각화 → evidence 생성]  ← 패턴 그대로 유지
        ```

        ### 에이전트가 설정하는 값 예시

        이슈 본문: *"2026년 1분기 iOS vs Android Stickiness 비교. 주말 효과 포함."*

        에이전트가 자동 설정하는 config:
        ```python
        ANALYSIS_CONFIG = {
            "project_id": "my-gcp-project",       # GitHub Secret에서 읽음
            "dataset": "fittrack",
            "start_date": "2026-01-01",             # 이슈에서 파싱
            "end_date": "2026-03-31",               # 이슈에서 파싱
            "segment": "platform",                  # 이슈에서 파싱
            "analysis_type": "dau_mau_stickiness",  # 이슈에서 추론
            "issue_number": 42,                     # GitHub Issue 번호
        }
        ```
        """
    )
    return (mo,)


@app.cell
def pattern_1_config():
    # ─────────────────────────────────────────────────────────────────────────
    # harness 패턴 1: CONFIG 셀 (에이전트가 수정하는 유일한 셀)
    # ─────────────────────────────────────────────────────────────────────────
    # 에이전트는 이 딕셔너리의 값만 수정합니다.
    # 모든 다운스트림 셀은 ANALYSIS_CONFIG를 참조하므로
    # 이 하나의 셀만 변경하면 전체 노트북이 업데이트됩니다.
    #
    # ⚠️ 에이전트 규약 (AGENTS.md에 명시):
    #   - 이 셀 외의 셀 구조는 수정하지 않는다
    #   - project_id는 환경변수 GCP_PROJECT_ID에서 읽는다
    #   - start_date/end_date는 이슈 본문의 "기간" 필드에서 파싱한다

    import os

    ANALYSIS_CONFIG = {
        # GCP 설정 (GitHub Actions에서는 Secret으로 제공)
        "project_id": os.getenv("GCP_PROJECT_ID", "your-gcp-project-id"),
        "dataset": "fittrack",

        # 분석 기간 (이슈에서 파싱)
        "start_date": "2026-01-01",
        "end_date": "2026-03-31",

        # 분석 파라미터 (이슈에서 파싱)
        "segment": "platform",           # 세그먼트 기준
        "analysis_type": "template_demo",  # 분석 유형 식별자

        # harness 메타데이터
        "issue_number": 0,               # GitHub Issue 번호 (에이전트가 설정)
        "evidence_path": "evidence/template-demo-evidence.json",
    }
    return (ANALYSIS_CONFIG,)


@app.cell
def pattern_2_bigquery_setup(ANALYSIS_CONFIG, mo):
    # ─────────────────────────────────────────────────────────────────────────
    # harness 패턴 2: BigQuery 클라이언트 초기화 (표준 패턴)
    # ─────────────────────────────────────────────────────────────────────────
    # 모든 분석 노트북에서 동일한 패턴을 사용합니다.
    # 로컬: gcloud auth application-default login
    # CI/CD (GitHub Actions): GOOGLE_APPLICATION_CREDENTIALS 환경변수
    #
    # mo.stop()을 활용하여 연결 실패 시 후속 셀 실행을 중단합니다.
    # 이렇게 하면 실패 원인을 즉시 파악할 수 있습니다.

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

    # 연결 실패 시 이후 셀 실행 중단 (mo.stop 패턴)
    # CI/CD에서는 이 시점에 워크플로가 오류로 종료됩니다.
    mo.stop(not connection_ok, mo.md(f"⛔ BigQuery 연결 실패로 분석 중단.\n\n{connection_msg}"))

    return (bq_client,)


@app.cell
def pattern_3_cost_efficient_load(ANALYSIS_CONFIG, bq_client, mo):
    # ─────────────────────────────────────────────────────────────────────────
    # harness 패턴 3: 비용 효율적 데이터 로드
    # ─────────────────────────────────────────────────────────────────────────
    # BigQuery on-demand 가격에서 비용의 핵심은 "스캔 바이트 수"입니다.
    # 이 패턴을 따르면 불필요한 쿼리 재실행을 방지합니다:
    #
    #   1. 전체 분석 범위의 데이터를 한 번에 로드
    #   2. 이후 필터링/집계는 메모리(pandas) 내에서 처리
    #   3. UI 위젯 변경 시 BigQuery 재조회 없이 로컬 처리
    #
    # 쿼리 비용 추정 (dry_run 패턴):
    #   query_job = bq_client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True))
    #   print(f"예상 스캔: {query_job.total_bytes_processed / 1e9:.2f} GB")

    import pandas as pd

    # 템플릿 데모: DAU 데이터 로드 (실제 노트북에서는 분석 목적에 맞는 mart 모델 사용)
    demo_query = f"""
    SELECT
        activity_date,
        platform,
        dau          AS dau_count,
        new_users,
        returning_users,
        total_sessions,
        total_revenue,
        premium_dau,
        premium_ratio
    FROM `{ANALYSIS_CONFIG["project_id"]}.{ANALYSIS_CONFIG["dataset"]}.fct_daily_active_users`
    WHERE activity_date BETWEEN '{ANALYSIS_CONFIG["start_date"]}' AND '{ANALYSIS_CONFIG["end_date"]}'
    ORDER BY activity_date, platform
    """

    # dry_run으로 비용 예상 먼저 확인
    try:
        from google.cloud import bigquery as bq_module
        dry_run_config = bq_module.QueryJobConfig(dry_run=True, use_query_cache=False)
        dry_run_job = bq_client.query(demo_query, job_config=dry_run_config)
        estimated_bytes = dry_run_job.total_bytes_processed or 0
        cost_msg = f"예상 스캔: **{estimated_bytes / 1e6:.1f} MB** (약 ₩{estimated_bytes / 1e12 * 6_000_000:.0f})"
    except Exception:
        cost_msg = "비용 추정 건너뜀"

    # 실제 데이터 로드
    df_raw = bq_client.query(demo_query).to_dataframe()
    df_raw["activity_date"] = pd.to_datetime(df_raw["activity_date"])
    df_raw["month"] = df_raw["activity_date"].dt.strftime("%Y-%m")
    df_raw["week"] = df_raw["activity_date"].dt.to_period("W").apply(
        lambda p: str(p.start_time.date())
    )

    mo.md(
        f"""
        ### 📋 데이터 로드 완료

        - **{cost_msg}**
        - 기간: {df_raw["activity_date"].min().strftime("%Y-%m-%d")} ~
          {df_raw["activity_date"].max().strftime("%Y-%m-%d")}
        - 행 수: {len(df_raw):,}행

        > 💡 **비용 절감 팁**: 위 dry_run 패턴으로 실행 전 스캔 비용을 확인하세요.
        > BigQuery on-demand는 첫 1TB/월 무료입니다.
        """
    )
    return (df_raw,)


@app.cell
def pattern_4_reactive_ui(df_raw, mo):
    # ─────────────────────────────────────────────────────────────────────────
    # harness 패턴 4: 반응형 UI (이해관계자 탐색용)
    # ─────────────────────────────────────────────────────────────────────────
    # marimo의 반응형 UI는 에이전트가 생성한 노트북을
    # 이해관계자가 직접 탐색할 수 있게 합니다.
    #
    # 에이전트가 노트북을 생성할 때 이 패턴을 포함하면:
    # - PR 리뷰어가 파라미터를 조정하며 다양한 각도로 결과 확인 가능
    # - 정적 HTML 리포트와 함께 인터랙티브 탐색 도구로 활용
    # - 후속 질문에 빠르게 답변 가능

    platform_options = ["전체"] + sorted(df_raw["platform"].unique().tolist())

    # UI 위젯 정의
    ui_platform = mo.ui.dropdown(
        options=platform_options,
        value="전체",
        label="플랫폼",
    )

    ui_granularity = mo.ui.radio(
        options={"일별": "daily", "주별": "weekly", "월별": "monthly"},
        value="주별",
        label="시간 단위",
    )

    ui_show_ma = mo.ui.checkbox(
        value=True,
        label="이동평균 표시 (일별 데이터에서만)",
    )

    mo.md("## 🎛️ 탐색 파라미터 (이해관계자용)")
    mo.hstack(
        [
            mo.vstack([mo.md("**플랫폼**"), ui_platform]),
            mo.vstack([mo.md("**시간 단위**"), ui_granularity]),
            mo.vstack([mo.md("**옵션**"), ui_show_ma]),
        ],
        gap=3,
        justify="start",
    )
    return (ui_granularity, ui_platform, ui_show_ma)


@app.cell
def pattern_5_analysis(df_raw, mo, ui_granularity, ui_platform, ui_show_ma):
    # ─────────────────────────────────────────────────────────────────────────
    # harness 패턴 5: 의존성 기반 자동 재실행
    # ─────────────────────────────────────────────────────────────────────────
    # 이 셀은 ui_platform, ui_granularity, ui_show_ma에 의존합니다.
    # 세 위젯 중 하나라도 값이 바뀌면 이 셀이 자동으로 재실행됩니다.
    # (Jupyter와의 핵심 차이: 수동 "Re-run" 불필요)
    #
    # 에이전트가 생성하는 분석 셀 구조:
    # 1. 파라미터 읽기 (위젯 .value 접근)
    # 2. 데이터 필터링 (메모리 내, BigQuery 재조회 없음)
    # 3. 집계 계산
    # 4. 차트 생성
    # 5. 요약 통계 출력

    import pandas as pd
    import plotly.graph_objects as go

    # 1. 파라미터 읽기
    platform_val = ui_platform.value
    granularity_val = ui_granularity.value
    show_ma = ui_show_ma.value and granularity_val == "daily"

    # 2. 데이터 필터링
    if platform_val == "전체":
        df_filtered = df_raw.copy()
    else:
        df_filtered = df_raw[df_raw["platform"] == platform_val].copy()

    # 3. 집계
    if granularity_val == "daily":
        time_col = "activity_date"
        df_agg = df_filtered.groupby("activity_date")["dau_count"].sum().reset_index()
    elif granularity_val == "weekly":
        time_col = "week"
        df_agg = df_filtered.groupby("week")["dau_count"].sum().reset_index()
        df_agg[time_col] = pd.to_datetime(df_agg[time_col])
    else:
        time_col = "month"
        df_agg = df_filtered.groupby("month")["dau_count"].sum().reset_index()

    df_agg = df_agg.sort_values(time_col)

    # 4. 차트 생성
    fig = go.Figure()

    if show_ma:
        # 일별 원본 (점선, 투명)
        fig.add_trace(
            go.Scatter(
                x=df_agg[time_col],
                y=df_agg["dau_count"],
                mode="lines",
                line=dict(color="#90CAF9", width=1, dash="dot"),
                opacity=0.5,
                name="일별 DAU",
                showlegend=True,
            )
        )
        # 7일 이동평균 (굵은 선)
        ma_values = df_agg["dau_count"].rolling(window=7, min_periods=1).mean()
        fig.add_trace(
            go.Scatter(
                x=df_agg[time_col],
                y=ma_values,
                mode="lines",
                line=dict(color="#1565C0", width=2.5),
                name="7일 이동평균",
            )
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=df_agg[time_col],
                y=df_agg["dau_count"],
                mode="lines+markers" if granularity_val != "daily" else "lines",
                line=dict(color="#1976D2", width=2),
                marker=dict(size=7),
                name=f"DAU ({granularity_val})",
            )
        )

    fig.update_layout(
        title=f"DAU 추이 — {platform_val} ({granularity_val})",
        xaxis_title="기간",
        yaxis_title="DAU",
        template="plotly_white",
        hovermode="x unified",
    )

    # 5. 요약 통계
    avg_dau = df_agg["dau_count"].mean()
    max_dau = df_agg["dau_count"].max()

    mo.md(
        f"""
        ## 📊 DAU 추이 분석

        | 통계 | 값 |
        |------|----|
        | 기간 평균 DAU | {avg_dau:,.0f} |
        | 최대 DAU | {max_dau:,.0f} |
        | 플랫폼 필터 | {platform_val} |
        | 시간 단위 | {granularity_val} |
        """
    )
    mo.ui.plotly(fig)
    return (df_agg, fig)


@app.cell
def pattern_6_evidence_generation(ANALYSIS_CONFIG, df_agg, mo):
    # ─────────────────────────────────────────────────────────────────────────
    # harness 패턴 6: 완료 증거 생성 (Proof of Completion)
    # ─────────────────────────────────────────────────────────────────────────
    # 에이전트 작업의 완료를 "기계적으로" 검증할 수 있는 아티팩트를 생성합니다.
    # "분석 완료했습니다"라는 텍스트 보고 대신, 구체적인 JSON 결과물이 필요합니다.
    #
    # GitHub Actions의 stage:7-report 단계에서 이 파일을 읽어
    # 분석이 실제로 완료되었는지 검증합니다:
    #
    #   cat evidence/*.json | jq '.key_metrics | length > 0'
    #   → true이면 증거 충분, false이면 재실행 트리거
    #
    # 완료 증거의 세 가지 유형:
    # 1. key_metrics: 핵심 지표 수치 (값이 존재하면 분석 완료 증거)
    # 2. data_quality: 데이터 품질 체크 결과
    # 3. generated_at: 생성 타임스탬프 (재실행 추적)

    import json
    import os
    import pandas as pd

    # 핵심 지표 산출
    avg_dau = float(df_agg["dau_count"].mean())
    max_dau = float(df_agg["dau_count"].max())
    min_dau = float(df_agg["dau_count"].min())
    total_data_points = len(df_agg)

    # 완료 증거 딕셔너리
    evidence = {
        "notebook": "marimo-harness-template.py",
        "analysis_type": ANALYSIS_CONFIG["analysis_type"],
        "issue_number": ANALYSIS_CONFIG["issue_number"],
        "period": {
            "start": ANALYSIS_CONFIG["start_date"],
            "end": ANALYSIS_CONFIG["end_date"],
        },
        # 핵심 지표: 이 섹션의 모든 값이 존재하면 분석 완료 증거
        "key_metrics": {
            "avg_dau": round(avg_dau, 0),
            "max_dau": round(max_dau, 0),
            "min_dau": round(min_dau, 0),
            "total_data_points": total_data_points,
        },
        # 데이터 품질 체크
        "data_quality": {
            "null_count": int(df_agg["dau_count"].isnull().sum()),
            "zero_count": int((df_agg["dau_count"] == 0).sum()),
            "is_valid": total_data_points > 0 and avg_dau > 0,
        },
        "generated_at": pd.Timestamp.now().isoformat(),
    }

    # 파일 저장
    evidence_path = ANALYSIS_CONFIG["evidence_path"]
    try:
        os.makedirs(os.path.dirname(evidence_path), exist_ok=True)
        with open(evidence_path, "w", encoding="utf-8") as f:
            json.dump(evidence, f, ensure_ascii=False, indent=2)
        save_status = f"✅ `{evidence_path}` 저장 완료"
    except Exception as e:
        save_status = f"⚠️ 저장 건너뜀: {e}"

    mo.md(
        f"""
        ---

        ## 🤖 harness 완료 증거

        {save_status}

        ```json
        {json.dumps(evidence, ensure_ascii=False, indent=2)}
        ```

        ### harness 검증 명령 (stage:7-report에서 실행)

        ```bash
        # 증거 파일 존재 확인
        test -f {evidence_path} && echo "✅ 증거 파일 존재" || echo "❌ 증거 파일 없음"

        # 핵심 지표 값 확인
        cat {evidence_path} | python3 -c "
        import json, sys
        e = json.load(sys.stdin)
        metrics = e.get('key_metrics', {{}})
        ok = all(v is not None and v > 0 for v in metrics.values() if isinstance(v, (int, float)))
        print('✅ 분석 완료' if ok else '❌ 지표 누락')
        "
        ```
        """
    )
    return (evidence,)


@app.cell
def pattern_7_harness_summary(mo):
    # ─────────────────────────────────────────────────────────────────────────
    # harness 패턴 요약
    # ─────────────────────────────────────────────────────────────────────────
    # 이 노트북에서 시연한 7가지 harness 패턴을 정리합니다.

    mo.md(
        """
        ---

        ## 📚 harness 노트북 패턴 요약

        이 노트북이 시연한 7가지 핵심 패턴:

        | # | 패턴 | 셀 이름 | 핵심 목적 |
        |---|------|---------|-----------|
        | 1 | Config 셀 분리 | `pattern_1_config` | 에이전트가 수정하는 유일한 셀 |
        | 2 | 연결 확인 + `mo.stop()` | `pattern_2_bigquery_setup` | 실패 시 즉시 중단, 원인 명확화 |
        | 3 | 비용 효율 로드 | `pattern_3_cost_efficient_load` | dry_run + 한 번 로드 |
        | 4 | 반응형 UI | `pattern_4_reactive_ui` | 이해관계자 인터랙티브 탐색 |
        | 5 | 의존성 기반 재실행 | `pattern_5_analysis` | 위젯 변경 → 자동 업데이트 |
        | 6 | 완료 증거 생성 | `pattern_6_evidence_generation` | 기계 검증 가능한 아티팩트 |
        | 7 | 패턴 문서화 | `pattern_7_harness_summary` | 에이전트와 사람 모두를 위한 문서 |

        ---

        ### 에이전트가 이 템플릿을 사용하는 방법

        ```python
        # stage:6-analyze에서 Claude가 실행하는 작업:
        # 1. 이 템플릿 파일을 읽음
        # 2. ANALYSIS_CONFIG 딕셔너리만 수정
        # 3. 새 파일로 저장 (analyses/<issue-number>-<topic>.py)

        # 에이전트 프롬프트 예시 (stage:6-analyze):
        # "analyses/ 디렉토리에 marimo-harness-template.py를 참조하여
        #  이슈 #42의 DAU/MAU Stickiness 분석 노트북을 생성하세요.
        #  ANALYSIS_CONFIG만 수정하고, 나머지 패턴은 유지하세요."
        ```

        ### AGENTS.md에 명시되어야 할 규약

        ```markdown
        ## marimo 노트북 규약

        - 모든 분석 노트북은 `examples/marimo-harness-template.py` 구조를 따른다
        - ANALYSIS_CONFIG 셀만 수정하고 나머지 패턴 셀은 유지한다
        - 완료 증거(evidence/ 디렉토리)를 항상 생성한다
        - mo.stop()으로 실패 시 즉시 중단하여 원인을 명확히 한다
        - 데이터는 한 번만 로드하고, 필터링은 메모리에서 처리한다
        ```

        ---

        > 이 노트북은 harness 교육 목적으로 작성되었습니다.
        > 실제 분석에는 `marimo-dau-mau-analysis.py`, `marimo-retention-cohort.py` 등을 참조하세요.
        """
    )
    return


if __name__ == "__main__":
    app.run()

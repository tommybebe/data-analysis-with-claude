# /create-notebook — marimo 분석 노트북 생성

새 분석 요청에 맞는 marimo 노트북을 프로젝트 규약에 맞게 생성합니다.
BigQuery 연결, 데이터 로드, 시각화, 결론 셀까지 기본 구조를 자동 스캐폴딩합니다.

## 입력

- `$ARGUMENTS`: 노트북 생성 요청 설명
  - 예: `DAU/MAU 트렌드 분석 지난 30일`
  - 예: `#42 3월 코호트 리텐션 분석`
  - 예: `신규 사용자 온보딩 퍼널 분석`

## 실행 절차

### 1단계: 요청 파싱
- GitHub Issue 번호 패턴(`#N`) 감지 → `gh issue view N`으로 내용 확인
- 분석 주제, 기간, 대상 지표, 기대 산출물 추출

### 2단계: 파일명 결정

| 입력 유형 | 파일명 규칙 | 예시 |
|-----------|------------|------|
| Issue 번호 | `notebooks/analysis_<번호>.py` | `analysis_42.py` |
| 주제 텍스트 | `notebooks/analysis_<snake_case_주제>.py` | `analysis_dau_mau_trend.py` |

### 3단계: 노트북 생성

다음 구조로 marimo 노트북 파일 생성:

```python
import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium")

@app.cell
def 분석_헤더(mo):
    # 노트북 제목 및 분석 개요 셀
    mo.md("""
    # <분석 제목>

    **기간**: YYYY-MM-DD ~ YYYY-MM-DD
    **분석 목적**: <목적 설명>

    ## 핵심 발견
    - (분석 완료 후 작성)
    """)
    return

@app.cell
def 환경_설정(mo):
    # 필수 라이브러리 임포트 및 BigQuery 클라이언트 초기화
    import os
    import pandas as pd
    import plotly.express as px
    from google.cloud import bigquery

    # BigQuery 클라이언트 초기화 (환경 변수로 인증)
    PROJECT_ID = os.environ.get("BQ_PROJECT_ID", "your-project-id")
    client = bigquery.Client(project=PROJECT_ID)

    mo.md(f"✅ BigQuery 연결됨: `{PROJECT_ID}`")
    return client, pd, px, PROJECT_ID

@app.cell
def 데이터_로드(client, mo):
    # BigQuery에서 데이터 로드 (dry-run으로 비용 확인 후 실행)
    query = """
    SELECT
        <columns>
    FROM `<table_reference>`
    WHERE <date_filter>
    ORDER BY <order_column>
    """
    df = client.query(query).to_dataframe()

    mo.md(f"📊 데이터 로드 완료: {len(df):,}행")
    return df

@app.cell
def 데이터_분석(df, mo):
    # 핵심 지표 계산 및 변환
    summary = df.describe()
    return summary

@app.cell
def 시각화(df, px, mo):
    # 분석 차트 생성 (축 레이블, 제목은 한국어로)
    fig = px.line(
        df,
        x="<date_column>",
        y="<metric_column>",
        title="<한국어 차트 제목>",
        labels={
            "<date_column>": "날짜",
            "<metric_column>": "<지표명>"
        }
    )
    fig.update_layout(
        xaxis_title="날짜",
        yaxis_title="<지표명>",
        legend_title="범례"
    )
    return mo.ui.plotly(fig)

@app.cell
def 결론(mo):
    # 분석 결론 및 제안 사항
    mo.md("""
    ## 결론 및 제안

    ### 주요 발견
    1. (분석 결과 작성)

    ### 제안 사항
    - (후속 조치 또는 추가 분석 제안)

    ### 다음 단계
    - [ ] (TODO)
    """)
    return

if __name__ == "__main__":
    app.run()
```

### 4단계: 비용 사전 확인
데이터 로드 쿼리를 dry-run으로 먼저 확인:
```bash
bq query --dry_run --use_legacy_sql=false "<SQL>"
```
- 1GB 이하: 쿼리 본문에 그대로 사용
- 1GB 초과: 파티션 필터 추가 후 재확인

### 5단계: 기존 mart 모델 연결
`models/marts/` 디렉토리의 기존 dbt 모델을 우선 활용:
- `fct_daily_active_users` → DAU, Stickiness 분석
- `fct_monthly_active_users` → MAU 트렌드 분석
- `fct_retention_cohort` → 코호트 리텐션 분석
- `fct_feature_engagement` → 기능 참여율 분석
- `fct_revenue_analysis` → 수익 분석
- `fct_user_segments` → 사용자 세그먼트 분석

## 노트북 규약

- **변수명/함수명**: 영어 (예: `df`, `client`, `fig`)
- **셀 함수명**: 한국어 설명 가능 (예: `데이터_분석`, `시각화`)
- **주석**: 한국어
- **차트 요소**: 제목, 축, 범례 모두 한국어
- **숫자 포맷**: 천 단위 쉼표 (예: `f"{value:,}"`)
- **비율**: 소수점 2자리 (예: `f"{rate:.2%}"`)

## 출력 형식

```
## 노트북 생성 완료

### 생성된 파일
- 📓 notebooks/analysis_<이름>.py

### 노트북 구조
- 셀 1: 분석 헤더 (제목, 기간, 핵심 발견)
- 셀 2: 환경 설정 (라이브러리, BQ 연결)
- 셀 3: 데이터 로드 (BigQuery 쿼리)
- 셀 4: 데이터 분석 (지표 계산)
- 셀 5: 시각화 (차트)
- 셀 6: 결론 및 제안

### 예상 쿼리 비용
- 예상 스캔량: X.X GB
- 예상 비용: $X.XX USD

### 다음 단계
- 노트북을 열어 플레이스홀더(<...>)를 실제 값으로 교체하세요.
- `uv run marimo edit notebooks/analysis_<이름>.py`
```

## 완료 증거

- [ ] `notebooks/` 디렉토리에 `.py` 파일 생성됨
- [ ] 파일이 유효한 marimo 앱 형식 (`import marimo`, `app = marimo.App()`)
- [ ] 최소 4개 이상의 `@app.cell` 셀 포함
- [ ] BigQuery 쿼리가 dry-run으로 비용 확인됨 (1GB 이내)

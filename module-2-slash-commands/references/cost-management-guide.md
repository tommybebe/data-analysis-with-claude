# BigQuery 비용 관리 가이드

> **대상**: "하니스 엔지니어링 for 데이터 분석" 코스의 강사 및 자기 학습자
>
> 이 가이드는 BigQuery on-demand 요금 모델에서 교육 비용을 예측 가능하게 유지하고, 예상치 못한 과금을 방지하기 위한 실용적인 지침을 제공합니다.

---

## 목차

1. [BigQuery 요금 구조 이해](#1-bigquery-요금-구조-이해)
2. [쿼리 비용 추정](#2-쿼리-비용-추정)
3. [예산 알림 설정](#3-예산-알림-설정)
4. [강사 비용 추적](#4-강사-비용-추적)
5. [리소스 정리 절차](#5-리소스-정리-절차)
6. [비용 절감 모범 사례](#6-비용-절감-모범-사례)
7. [비용 관련 자가 점검 체크리스트](#7-비용-관련-자가-점검-체크리스트)

---

## 1. BigQuery 요금 구조 이해

### 1.1 온디맨드(On-Demand) 요금 모델

이 코스는 **온디맨드 요금 모델**을 사용합니다. 쿼리가 실제로 **스캔한 데이터 바이트**에 따라 비용이 발생합니다.

| 항목 | 요금 | 비고 |
|------|------|------|
| 쿼리 처리 | **$5.00 / TB** | 매월 첫 1TB 무료 |
| 저장 (활성) | $0.02 / GB / 월 | 처음 10GB 무료 |
| 저장 (장기) | $0.01 / GB / 월 | 90일 이상 수정 없는 테이블 |
| 스트리밍 삽입 | $0.01 / 200MB | 이 코스는 배치 적재 사용 (해당 없음) |

> **핵심 포인트**: 이 코스의 합성 데이터는 약 500MB입니다. 매월 처음 1TB 쿼리 처리는 무료이므로, **교육 범위 내에서는 쿼리 비용이 거의 발생하지 않습니다.**

### 1.2 교육 환경별 예상 비용

| 환경 | 예상 월 비용 | 비고 |
|------|-------------|------|
| 자기 학습자 (1인) | **$0 ~ $2** | 1TB 무료 구간 내 수용 |
| 소규모 클래스 (학습자 10인, 공유 프로젝트) | **$0 ~ $5** | 학습자별 서비스 계정, 합계 처리량 관리 |
| 중규모 클래스 (학습자 30인, 독립 프로젝트) | **$0 ~ $10** | 프로젝트당 1TB 무료 구간 적용 |
| GitHub Actions (CI) | **$0** | 공개 레포 무료, 비공개 레포 월 2,000분 무료 |

> **GCP 신규 계정 크레딧**: 신규 GCP 계정에는 **$300 무료 크레딧(90일 유효)**이 제공됩니다. 이 코스 전체 실습 비용은 크레딧의 약 1~3% 이내로 충분히 완료할 수 있습니다.

### 1.3 비용이 발생하는 주요 시나리오

```
쿼리 비용 발생 패턴:
┌──────────────────────────────────────────────────────────┐
│ 1. bq query / dbt run → 쿼리 스캔 바이트에 비례           │
│ 2. SELECT * FROM large_table (파티션 필터 없음) → 위험    │
│ 3. 반복 실행 (GitHub Actions dbt build) → 누적 비용       │
│ 4. 개발 중 시행착오 쿼리 → 예상치 못한 누적               │
└──────────────────────────────────────────────────────────┘
```

---

## 2. 쿼리 비용 추정

### 2.1 dry-run으로 실행 전 비용 확인

BigQuery는 실제 쿼리를 실행하지 않고 스캔 바이트만 확인하는 **dry-run** 기능을 제공합니다.

#### CLI 방법

```bash
# dry-run 실행 — 실제 데이터를 읽지 않고 스캔량만 확인
bq query \
  --dry_run \
  --use_legacy_sql=false \
  'SELECT user_id, COUNT(*) as event_count
   FROM `your-project.raw.app_events`
   WHERE DATE(event_timestamp) = "2024-01-01"
   GROUP BY user_id'
```

예상 출력:
```
Query successfully validated. Assuming the tables are not modified,
running this query will process 12345678 bytes of data.
```

#### 비용 계산

```
스캔 바이트 → 비용 계산 공식:
비용(USD) = (스캔 바이트 / 1_099_511_627_776) × 5.00
         = (스캔 GB / 1024) × 5.00
```

```bash
# 스캔 바이트를 입력받아 비용 계산 (bash)
BYTES=12345678
GB=$(echo "scale=4; $BYTES / 1073741824" | bc)
COST=$(echo "scale=6; $GB / 1024 * 5" | bc)
echo "스캔량: ${GB} GB | 예상 비용: \$${COST} USD"
```

### 2.2 /check-cost 커맨드 활용

Claude Code에서 내장 `/check-cost` 커맨드를 사용하면 SQL 쿼리 또는 파일에 대한 비용을 자동으로 추정합니다.

```
# Claude Code 터미널에서 실행
/check-cost "SELECT * FROM `your-project.raw.app_events`"

# SQL 파일 경로로도 사용 가능
/check-cost analyses/01_dau_trend.sql
```

출력 예시:
```
## BigQuery 비용 확인 결과

📊 예상 스캔량: 0.43 GB (461,123,584 bytes)
💰 예상 비용:  $0.0021 USD (on-demand, $5/TB 기준)

상태: ✅ 안전 — 실행 가능
```

#### 위험도 분류 기준

| 스캔량 | 상태 | 예상 비용 | 조치 |
|--------|------|-----------|------|
| 1GB 이하 | ✅ 안전 | < $0.005 | 실행 가능 |
| 1GB ~ 10GB | ⚠️ 주의 | $0.005 ~ $0.05 | 실행 전 검토 권장 |
| 10GB ~ 100GB | 🚨 경고 | $0.05 ~ $0.50 | 쿼리 최적화 필요 |
| 100GB 초과 | ❌ 위험 | > $0.50 | 반드시 최적화 후 실행 |

### 2.3 Python으로 dry-run 자동화

반복적인 비용 확인을 자동화하려면 Python 스크립트를 사용합니다.

```python
# scripts/estimate_query_cost.py
# BigQuery 쿼리 비용을 dry-run으로 추정하는 스크립트

from google.cloud import bigquery

def estimate_query_cost(sql: str, project_id: str) -> dict:
    """
    SQL 쿼리의 예상 스캔 바이트와 비용을 dry-run으로 계산합니다.

    Args:
        sql: 비용을 추정할 BigQuery SQL 쿼리
        project_id: GCP 프로젝트 ID

    Returns:
        스캔 바이트, GB, 예상 비용(USD)을 담은 딕셔너리
    """
    client = bigquery.Client(project=project_id)

    # dry_run=True 로 설정하면 실제 쿼리를 실행하지 않음
    job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)

    job = client.query(sql, job_config=job_config)

    bytes_processed = job.total_bytes_processed
    gb_processed = bytes_processed / (1024 ** 3)

    # on-demand 요금: $5 / TB = $0.004882 / GB
    cost_usd = gb_processed / 1024 * 5.0

    return {
        "bytes": bytes_processed,
        "gb": round(gb_processed, 4),
        "cost_usd": round(cost_usd, 6),
        "is_safe": gb_processed < 1.0,        # 1GB 미만이면 안전
        "needs_review": 1.0 <= gb_processed < 10.0,  # 1~10GB는 검토 필요
    }


def format_cost_report(result: dict) -> str:
    """비용 추정 결과를 사람이 읽기 쉬운 형태로 포맷합니다."""
    if result["is_safe"]:
        status = "✅ 안전"
    elif result["needs_review"]:
        status = "⚠️ 주의"
    else:
        status = "❌ 위험"

    return (
        f"📊 예상 스캔량: {result['gb']:.3f} GB ({result['bytes']:,} bytes)\n"
        f"💰 예상 비용:  ${result['cost_usd']:.4f} USD\n"
        f"상태: {status}"
    )


if __name__ == "__main__":
    import os

    PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "your-project-id")

    # 예시: DAU 집계 쿼리 비용 추정
    sample_sql = """
    SELECT
        DATE(event_timestamp) AS event_date,
        COUNT(DISTINCT user_id) AS dau
    FROM `{project}.raw.app_events`
    WHERE DATE(event_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    GROUP BY event_date
    ORDER BY event_date
    """.format(project=PROJECT_ID)

    result = estimate_query_cost(sample_sql, PROJECT_ID)
    print(format_cost_report(result))
```

### 2.4 bq-cost-guard 훅으로 자동 차단

Claude Code의 `PreToolUse` 훅에 비용 가드를 등록하면, 비용 한도를 초과하는 쿼리를 자동으로 차단합니다.

`.claude/hooks/bq-cost-guard.sh`가 이미 구성되어 있으며, 기본 한도는 **1GB**입니다.

```bash
# 비용 한도를 환경 변수로 조정 (예: 500MB로 제한)
export BQ_COST_LIMIT_BYTES=524288000

# 또는 .env 파일에 영구 설정
echo "BQ_COST_LIMIT_BYTES=524288000" >> .env
```

---

## 3. 예산 알림 설정

### 3.1 GCP Console에서 예산 알림 설정 (GUI)

1. [GCP 콘솔 → 결제](https://console.cloud.google.com/billing) 이동
2. 결제 계정 선택 → **"예산 및 알림"** 클릭
3. **"예산 만들기"** 클릭
4. 설정 항목:
   - **이름**: `course-budget-alert`
   - **범위**: 특정 프로젝트 선택 (예: `fittrack-analysis-course`)
   - **예산 금액**: `$10` (교육용 안전 한도)
   - **알림 기준**: 50%, 90%, 100% 도달 시 이메일 발송
5. **저장** 클릭

### 3.2 gcloud CLI로 예산 알림 설정

```bash
# 결제 계정 ID 확인
BILLING_ACCOUNT_ID=$(gcloud billing accounts list --format="value(name)" | head -1)
echo "결제 계정 ID: $BILLING_ACCOUNT_ID"

# 예산 알림 JSON 파일 생성
cat > /tmp/budget_config.json << 'EOF'
{
  "displayName": "course-budget-alert",
  "budgetFilter": {
    "projects": ["projects/YOUR_PROJECT_NUMBER"],
    "services": ["services/95FF-2EF5-5EA1"]
  },
  "amount": {
    "specifiedAmount": {
      "currencyCode": "USD",
      "units": "10"
    }
  },
  "thresholdRules": [
    {"thresholdPercent": 0.5, "spendBasis": "CURRENT_SPEND"},
    {"thresholdPercent": 0.9, "spendBasis": "CURRENT_SPEND"},
    {"thresholdPercent": 1.0, "spendBasis": "CURRENT_SPEND"}
  ],
  "notificationsRule": {
    "enableProjectLevelRecipients": true
  }
}
EOF

# 프로젝트 번호 확인 (프로젝트 ID와 다름)
PROJECT_NUMBER=$(gcloud projects describe $GCP_PROJECT_ID --format="value(projectNumber)")
sed -i "s/YOUR_PROJECT_NUMBER/$PROJECT_NUMBER/" /tmp/budget_config.json

# 예산 생성 (Billing Budget API 사용)
gcloud billing budgets create \
  --billing-account=$BILLING_ACCOUNT_ID \
  --display-name="course-budget-alert" \
  --budget-amount=10USD \
  --threshold-rule=percent=0.5 \
  --threshold-rule=percent=0.9 \
  --threshold-rule=percent=1.0
```

> **참고**: `gcloud billing budgets` 명령은 `gcloud beta`에서 지원됩니다. 최신 SDK를 사용 중이라면 `gcloud beta billing budgets create` 형식으로 실행하세요.

### 3.3 BigQuery 프로젝트 수준 쿼리 비용 한도 설정

개별 쿼리가 아닌 **프로젝트 전체**에 월별 스캔 바이트 한도를 설정합니다.

```bash
# 프로젝트 수준 쿼리 비용 한도 설정 (예: 100GB/월)
# GCP Console → BigQuery → 설정 → 프로젝트 설정에서도 가능
bq update \
  --project_id=$GCP_PROJECT_ID \
  --maximum_bytes_billed=107374182400  # 100GB in bytes
```

```python
# scripts/set_project_cost_limit.py
# 프로젝트의 BigQuery 쿼리 비용 한도를 설정합니다

from google.cloud import bigquery

def set_project_query_limit(project_id: str, max_gb: float = 100.0):
    """
    BigQuery 프로젝트 수준의 최대 쿼리 스캔 바이트를 설정합니다.
    이 한도를 초과하는 쿼리는 자동으로 취소됩니다.

    Args:
        project_id: GCP 프로젝트 ID
        max_gb: 최대 허용 스캔량 (GB 단위)
    """
    client = bigquery.Client(project=project_id)
    max_bytes = int(max_gb * 1024 * 1024 * 1024)

    # 기본 쿼리 설정에 한도 적용
    job_config = bigquery.QueryJobConfig(
        maximum_bytes_billed=max_bytes
    )

    print(f"✅ 프로젝트 '{project_id}': 쿼리 한도 {max_gb:.0f}GB 설정됨")
    print(f"   ({max_bytes:,} bytes)")
    return job_config
```

### 3.4 이메일 알림 자동화 (Pub/Sub + Cloud Functions)

예산 한도 도달 시 이메일 외에 **Slack 알림**이나 **자동 쿼리 중단** 등 추가 조치를 위해 Pub/Sub와 연동합니다.

```bash
# 1. Pub/Sub 토픽 생성 (예산 알림 수신용)
gcloud pubsub topics create billing-alerts

# 2. GCP Console → 결제 → 예산 및 알림에서
#    위에서 생성한 토픽을 "예산 초과 시 Pub/Sub 주제에 알림" 옵션에 연결

# 3. 알림 구독 확인
gcloud pubsub subscriptions create billing-alert-sub \
  --topic=billing-alerts
```

---

## 4. 강사 비용 추적

### 4.1 학습자별 비용 레이블 전략

공유 GCP 프로젝트에서 학습자별 비용을 분리하려면 **BigQuery 레이블**을 활용합니다.

```bash
# 학습자별 서비스 계정 생성 시 레이블 부여 전략
# 서비스 계정 이름에 학습자 ID 포함
export LEARNER_ID="learner01"
export SA_NAME="fittrack-${LEARNER_ID}"

gcloud iam service-accounts create $SA_NAME \
  --display-name="FitTrack Learner ${LEARNER_ID}" \
  --description="코스 실습용 — 학습자 ${LEARNER_ID}"
```

```sql
-- BigQuery INFORMATION_SCHEMA으로 학습자별 쿼리 사용량 추적
-- 이 쿼리를 INFORMATION_SCHEMA가 있는 프로젝트에서 실행하세요

SELECT
  -- 서비스 계정 이름에서 학습자 ID 추출
  REGEXP_EXTRACT(user_email, r'fittrack-(\w+)@') AS learner_id,
  user_email,
  COUNT(*) AS query_count,
  SUM(total_bytes_processed) AS total_bytes,
  ROUND(SUM(total_bytes_processed) / POW(1024, 4) * 5.0, 4) AS estimated_cost_usd,
  MIN(creation_time) AS first_query,
  MAX(creation_time) AS last_query
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE
  creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  AND user_email LIKE 'fittrack-%@%'
  AND state = 'DONE'
  AND error_result IS NULL  -- 성공한 쿼리만 집계
GROUP BY learner_id, user_email
ORDER BY total_bytes DESC;
```

### 4.2 일별 쿼리 처리량 모니터링

```sql
-- 일별 전체 쿼리 처리량 및 비용 집계
-- 강사 대시보드용

SELECT
  DATE(creation_time) AS query_date,
  COUNT(*) AS total_queries,
  COUNT(DISTINCT user_email) AS active_learners,
  SUM(total_bytes_processed) / POW(1024, 3) AS total_gb_scanned,
  ROUND(SUM(total_bytes_processed) / POW(1024, 4) * 5.0, 4) AS estimated_cost_usd
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE
  creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  AND state = 'DONE'
GROUP BY query_date
ORDER BY query_date DESC;
```

### 4.3 비용 임계값 초과 쿼리 탐지

```sql
-- 고비용 쿼리 탐지 (500MB 이상 스캔한 쿼리)
-- 이상 사용 패턴 식별에 활용

SELECT
  job_id,
  user_email,
  creation_time,
  ROUND(total_bytes_processed / POW(1024, 3), 2) AS gb_scanned,
  ROUND(total_bytes_processed / POW(1024, 4) * 5.0, 6) AS cost_usd,
  SUBSTR(query, 1, 200) AS query_preview  -- 쿼리 앞 200자 미리보기
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE
  creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND state = 'DONE'
  AND total_bytes_processed > 536870912  -- 500MB 초과
ORDER BY total_bytes_processed DESC
LIMIT 20;
```

### 4.4 주간 비용 리포트 자동화

```python
# scripts/weekly_cost_report.py
# 학습자별 주간 BigQuery 사용량 리포트를 생성하여 강사에게 전송합니다

import os
from datetime import datetime, timedelta
from google.cloud import bigquery

def generate_weekly_cost_report(project_id: str) -> str:
    """
    지난 7일간 학습자별 BigQuery 사용량을 집계하여 리포트 문자열을 반환합니다.

    Args:
        project_id: GCP 프로젝트 ID

    Returns:
        Markdown 형식의 주간 비용 리포트
    """
    client = bigquery.Client(project=project_id)

    # 학습자별 사용량 집계 쿼리
    query = """
    SELECT
        REGEXP_EXTRACT(user_email, r'fittrack-(\\w+)@') AS learner_id,
        COUNT(*) AS query_count,
        ROUND(SUM(total_bytes_processed) / POW(1024, 3), 3) AS gb_scanned,
        ROUND(SUM(total_bytes_processed) / POW(1024, 4) * 5.0, 4) AS cost_usd
    FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
    WHERE
        creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
        AND user_email LIKE 'fittrack-%@%'
        AND state = 'DONE'
    GROUP BY learner_id
    ORDER BY gb_scanned DESC
    """

    results = list(client.query(query).result())

    # 리포트 생성
    today = datetime.now().strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    lines = [
        f"# 주간 BigQuery 비용 리포트",
        f"**기간**: {week_ago} ~ {today}",
        f"**프로젝트**: `{project_id}`",
        "",
        "## 학습자별 사용량",
        "",
        "| 학습자 ID | 쿼리 수 | 스캔량 (GB) | 예상 비용 (USD) |",
        "|-----------|---------|------------|----------------|",
    ]

    total_gb = 0.0
    total_cost = 0.0

    for row in results:
        learner_id = row.learner_id or "unknown"
        lines.append(
            f"| {learner_id} | {row.query_count} | "
            f"{row.gb_scanned:.3f} | ${row.cost_usd:.4f} |"
        )
        total_gb += float(row.gb_scanned or 0)
        total_cost += float(row.cost_usd or 0)

    lines.extend([
        f"| **합계** | — | **{total_gb:.3f}** | **${total_cost:.4f}** |",
        "",
        "## 비용 분석",
        f"- 전체 스캔량: {total_gb:.3f} GB",
        f"- 예상 총 비용: ${total_cost:.4f} USD",
        f"- 1TB 무료 구간 사용률: {total_gb / 1024 * 100:.2f}%",
        "",
        "> *on-demand 요금 기준: $5.00 / TB*",
    ])

    return "\n".join(lines)


if __name__ == "__main__":
    PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "your-project-id")
    report = generate_weekly_cost_report(PROJECT_ID)
    print(report)

    # 리포트 파일로 저장
    output_path = f"reports/cost-report-{datetime.now().strftime('%Y-%m-%d')}.md"
    os.makedirs("reports", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n✅ 리포트 저장됨: {output_path}")
```

### 4.5 이상 사용 탐지 및 대응

```python
# scripts/detect_cost_anomalies.py
# 비정상적인 고비용 쿼리를 탐지하고 강사에게 경고합니다

import os
from google.cloud import bigquery

# 경고 임계값 설정 (환경 변수로 조정 가능)
ALERT_THRESHOLD_GB = float(os.environ.get("ALERT_THRESHOLD_GB", "5.0"))
ALERT_THRESHOLD_QUERIES = int(os.environ.get("ALERT_THRESHOLD_QUERIES", "100"))

def detect_anomalies(project_id: str) -> list[dict]:
    """
    지난 24시간 동안의 비정상적인 쿼리 패턴을 탐지합니다.

    탐지 기준:
    - 단일 쿼리가 5GB 이상 스캔
    - 동일 학습자가 24시간 내 100회 이상 쿼리 실행

    Returns:
        이상 탐지 결과 목록
    """
    client = bigquery.Client(project=project_id)

    anomalies = []

    # 1. 고비용 단일 쿼리 탐지
    high_cost_query = f"""
    SELECT
        job_id,
        user_email,
        creation_time,
        ROUND(total_bytes_processed / POW(1024, 3), 2) AS gb_scanned,
        ROUND(total_bytes_processed / POW(1024, 4) * 5.0, 6) AS cost_usd
    FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
    WHERE
        creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
        AND state = 'DONE'
        AND total_bytes_processed > {ALERT_THRESHOLD_GB * (1024**3)}
    ORDER BY total_bytes_processed DESC
    """

    for row in client.query(high_cost_query).result():
        anomalies.append({
            "type": "high_cost_query",
            "learner": row.user_email,
            "gb": row.gb_scanned,
            "cost_usd": row.cost_usd,
            "time": str(row.creation_time),
            "message": f"⚠️ 고비용 쿼리: {row.gb_scanned}GB 스캔 (${row.cost_usd:.4f})",
        })

    # 2. 과다 쿼리 실행 탐지
    high_frequency_query = f"""
    SELECT
        user_email,
        COUNT(*) AS query_count,
        ROUND(SUM(total_bytes_processed) / POW(1024, 3), 2) AS total_gb
    FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
    WHERE
        creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
        AND state = 'DONE'
        AND user_email LIKE 'fittrack-%@%'
    GROUP BY user_email
    HAVING COUNT(*) > {ALERT_THRESHOLD_QUERIES}
    ORDER BY query_count DESC
    """

    for row in client.query(high_frequency_query).result():
        anomalies.append({
            "type": "high_frequency",
            "learner": row.user_email,
            "query_count": row.query_count,
            "total_gb": row.total_gb,
            "message": (
                f"🔄 과다 쿼리 실행: 24시간 내 {row.query_count}회 "
                f"({row.total_gb}GB 스캔)"
            ),
        })

    return anomalies


if __name__ == "__main__":
    PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "your-project-id")
    anomalies = detect_anomalies(PROJECT_ID)

    if anomalies:
        print(f"⚠️ {len(anomalies)}개의 이상 패턴이 탐지되었습니다:\n")
        for anomaly in anomalies:
            print(f"  {anomaly['message']}")
            print(f"  학습자: {anomaly['learner']}")
            print()
    else:
        print("✅ 이상 패턴 없음 — 모든 사용량이 정상 범위입니다.")
```

---

## 5. 리소스 정리 절차

코스 종료 후 또는 실습 환경 초기화 시 리소스를 정리하여 불필요한 비용 발생을 방지합니다.

### 5.1 BigQuery 데이터셋 삭제

```bash
# 개별 데이터셋 삭제 (테이블 포함)
bq rm -r -f --dataset ${GCP_PROJECT_ID}:dbt_dev
bq rm -r -f --dataset ${GCP_PROJECT_ID}:dbt_ci
bq rm -r -f --dataset ${GCP_PROJECT_ID}:raw

# 삭제 확인
bq ls --project_id=$GCP_PROJECT_ID
# 출력 없으면 모두 삭제됨
```

> ⚠️ **주의**: `-f` 플래그는 확인 없이 강제 삭제합니다. 프로덕션 환경에서는 `-f` 없이 실행하여 확인 프롬프트를 거치세요.

### 5.2 서비스 계정 키 삭제

```bash
# 서비스 계정의 모든 키 목록 확인
gcloud iam service-accounts keys list \
  --iam-account=$SA_EMAIL \
  --filter="keyType=USER_MANAGED"

# 특정 키 삭제 (KEY_ID는 위 목록에서 확인)
gcloud iam service-accounts keys delete KEY_ID \
  --iam-account=$SA_EMAIL

# 서비스 계정 자체 삭제
gcloud iam service-accounts delete $SA_EMAIL
```

### 5.3 GitHub Secrets 삭제

```bash
# GitHub CLI로 레포지토리 시크릿 삭제
gh secret delete GCP_SA_KEY --repo owner/repo-name
gh secret delete GCP_PROJECT_ID --repo owner/repo-name
gh secret delete CLAUDE_CODE_OAUTH_TOKEN --repo owner/repo-name

# 삭제 확인
gh secret list --repo owner/repo-name
```

### 5.4 dbt 개발 환경 결과물 정리 (로컬)

```bash
# dbt 빌드 결과물 정리
dbt clean  # target/, dbt_packages/ 삭제

# dbt BigQuery 테이블 삭제 (dbt_dev 데이터셋)
dbt run-operation drop_schema \
  --args "{'schema': 'dbt_dev', 'database': '${GCP_PROJECT_ID}'}"

# 또는 직접 bq rm 사용
bq rm -r -f --dataset ${GCP_PROJECT_ID}:dbt_dev
```

### 5.5 GCP 프로젝트 완전 삭제 (선택)

코스 환경을 완전히 제거하려면 GCP 프로젝트 자체를 삭제합니다. **모든 데이터와 설정이 삭제되므로 신중하게 실행하세요.**

```bash
# 프로젝트 삭제 (30일 후 완전히 제거됨)
gcloud projects delete $GCP_PROJECT_ID

# 삭제 취소 (30일 이내에만 가능)
gcloud projects undelete $GCP_PROJECT_ID
```

> **참고**: 프로젝트 삭제 후 30일 이내에는 복원이 가능합니다. 실수로 삭제한 경우 즉시 `gcloud projects undelete`를 실행하세요.

### 5.6 정리 체크리스트

코스 종료 시 아래 항목을 순서대로 완료하세요.

```
코스 종료 후 리소스 정리 체크리스트:

GCP/BigQuery:
□ BigQuery raw 데이터셋 삭제 (bq rm -r -f --dataset PROJECT:raw)
□ BigQuery dbt_dev 데이터셋 삭제
□ BigQuery dbt_ci 데이터셋 삭제
□ 서비스 계정 JSON 키 삭제 (gcloud iam service-accounts keys delete)
□ 서비스 계정 삭제 (gcloud iam service-accounts delete)
□ GCP 예산 알림 삭제 (선택 — 다음 코스에도 재사용 가능)
□ GCP 프로젝트 삭제 (선택 — 완전 종료 시)

GitHub:
□ GitHub Secrets 삭제 (GCP_SA_KEY, GCP_PROJECT_ID, CLAUDE_CODE_OAUTH_TOKEN)
□ GitHub Actions 워크플로 비활성화 (선택)
□ 레포지토리 아카이브 또는 삭제 (선택)

로컬 개발 환경:
□ .env 파일 삭제 또는 자격증명 항목 제거
□ gcp-sa-key.json 등 키 파일 삭제
□ dbt 빌드 결과물 정리 (dbt clean)
□ ~/.dbt/profiles.yml에서 프로젝트 프로파일 제거

비용 최종 확인:
□ GCP Console → 결제에서 청구 내역 최종 확인
□ 예상치 못한 청구 항목이 없는지 검토
□ 결제 계정 비활성화 (더 이상 GCP를 사용하지 않는 경우)
```

---

## 6. 비용 절감 모범 사례

### 6.1 쿼리 최적화 전략

#### 날짜 파티션 필터 활용

```sql
-- ❌ 나쁜 예: 전체 테이블 스캔 (비용 높음)
SELECT user_id, event_type, event_timestamp
FROM `project.raw.app_events`;

-- ✅ 좋은 예: 파티션 필터로 스캔 범위 제한 (비용 최소화)
SELECT user_id, event_type, event_timestamp
FROM `project.raw.app_events`
WHERE DATE(event_timestamp) BETWEEN '2024-01-01' AND '2024-01-31';
```

#### 필요한 컬럼만 선택

```sql
-- ❌ 나쁜 예: 모든 컬럼 선택
SELECT *
FROM `project.raw.app_events`
WHERE DATE(event_timestamp) = '2024-01-01';

-- ✅ 좋은 예: 분석에 필요한 컬럼만 선택
SELECT user_id, event_type, session_id
FROM `project.raw.app_events`
WHERE DATE(event_timestamp) = '2024-01-01';
```

#### mart 모델 활용 (사전 집계 데이터 사용)

```sql
-- ❌ 나쁜 예: raw 테이블에서 직접 DAU 계산
SELECT
    DATE(event_timestamp) AS date,
    COUNT(DISTINCT user_id) AS dau
FROM `project.raw.app_events`
WHERE DATE(event_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY date;

-- ✅ 좋은 예: dbt mart 모델 사용 (이미 집계된 결과)
SELECT event_date, dau
FROM `project.dbt_dev.fct_daily_active_users`
WHERE event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY);
```

### 6.2 dbt 모델 설정 최적화

```yaml
# dbt_project.yml — 개발 환경에서 데이터 샘플링으로 비용 절감
models:
  fittrack_analysis:
    staging:
      +materialized: view        # view는 저장 비용 없음, 쿼리 시마다 실행
    intermediate:
      +materialized: ephemeral   # 임시 CTE, BigQuery 테이블 생성 안 함
    marts:
      +materialized: table       # mart만 물리 테이블로 저장
      +partition_by:             # 파티션으로 쿼리 비용 절감
        field: event_date
        data_type: date
```

### 6.3 개발 환경 데이터 샘플링

```sql
-- dbt 모델에서 개발 환경 샘플링 (macros/dev_limit.sql)
-- 개발 중에는 최근 7일 데이터만 사용하여 비용 절감

{% macro dev_limit() %}
  {% if target.name == 'dev' %}
    WHERE DATE(event_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
  {% endif %}
{% endmacro %}
```

```sql
-- staging/stg_events.sql에서 개발 환경 샘플링 적용
SELECT
    event_id,
    user_id,
    event_type,
    event_timestamp,
    session_id
FROM {{ source('raw', 'app_events') }}
{{ dev_limit() }}  -- 개발 환경에서는 최근 7일만 처리
```

### 6.4 쿼리 캐싱 활용

```python
# BigQuery 쿼리 캐싱을 활용하여 중복 실행 비용 절감
# 같은 쿼리를 24시간 이내 재실행하면 캐시에서 무료로 결과 반환

from google.cloud import bigquery

client = bigquery.Client()

# 쿼리 캐시 활성화 (기본값: True)
job_config = bigquery.QueryJobConfig(
    use_query_cache=True,  # 동일 쿼리 결과를 캐시에서 반환 (비용 없음)
)

# 단, 캐시를 비활성화해야 하는 경우:
# - 실시간 데이터가 필요한 경우
# - dry-run으로 정확한 스캔량 측정이 필요한 경우
no_cache_config = bigquery.QueryJobConfig(
    use_query_cache=False,
    dry_run=True,
)
```

---

## 7. 비용 관련 자가 점검 체크리스트

각 모듈 완료 시 아래 항목을 확인하세요.

### 모듈 0 (환경 설정) 이후

```
□ GCP 프로젝트에 예산 알림($10)이 설정되어 있다
□ BigQuery 프로젝트 수준 쿼리 한도가 설정되어 있다 (권장: 100GB/월)
□ 서비스 계정이 최소 권한(dataEditor + jobUser)만 갖고 있다
□ gcp-sa-key.json이 .gitignore에 포함되어 있다
□ /check-cost 커맨드가 정상 동작한다
```

### 모듈 1 (스캐폴딩) 이후

```
□ bq-cost-guard 훅이 .claude/settings.json에 등록되어 있다
□ AGENTS.md에 "쿼리 실행 전 /check-cost 확인" 지침이 포함되어 있다
□ dbt mart 모델이 파티션으로 설정되어 있다 (fct_daily_active_users 등)
□ 개발 환경(dev) dbt 프로파일이 올바른 데이터셋(dbt_dev)을 가리키고 있다
```

### 모듈 2 (스킬/훅) 이후

```
□ /check-cost 커맨드가 dry-run 결과를 올바르게 파싱하고 있다
□ bq-cost-guard.sh가 1GB 초과 쿼리를 차단하는지 테스트했다
□ GitHub Actions 워크플로가 불필요한 dbt full-refresh를 실행하지 않는다
□ CI 환경의 dbt 타깃이 dbt_ci 데이터셋을 사용하고 있다
```

### 모듈 3 (오케스트레이션) 이후

```
□ auto-analyze.yml 워크플로가 트리거 조건 외에는 실행되지 않는다
□ GitHub Actions 실행 시간이 월 2,000분 한도 이내인지 확인했다
□ 자동화된 dbt 실행에 파티션 필터가 적용되어 있다
□ 주간 비용 리포트 스크립트(weekly_cost_report.py)를 1회 실행해보았다
```

### 모듈 4 (통합/마무리) 이후

```
□ 코스 전체 BigQuery 사용량이 1TB 이내임을 확인했다
□ 이상 사용 탐지 스크립트(detect_cost_anomalies.py)로 이상 없음을 확인했다
□ 불필요한 dbt 모델 결과가 BigQuery에 남아있지 않다
□ 리소스 정리 체크리스트(섹션 5.6)를 완료했거나 이후 일정을 잡아두었다
```

---

## 부록: 비용 관련 환경 변수 참조

| 환경 변수 | 기본값 | 설명 |
|-----------|--------|------|
| `BQ_COST_LIMIT_BYTES` | `1073741824` (1GB) | bq-cost-guard 훅의 쿼리당 스캔 한도 |
| `GCP_PROJECT_ID` | — | GCP 프로젝트 ID (필수) |
| `ALERT_THRESHOLD_GB` | `5.0` | 이상 탐지 기준: 단일 쿼리 스캔량 (GB) |
| `ALERT_THRESHOLD_QUERIES` | `100` | 이상 탐지 기준: 24시간 내 쿼리 횟수 |

---

## 참고 링크

- [BigQuery 요금 페이지](https://cloud.google.com/bigquery/pricing)
- [GCP 예산 알림 설정 공식 가이드](https://cloud.google.com/billing/docs/how-to/budgets)
- [BigQuery INFORMATION_SCHEMA 쿼리 모니터링](https://cloud.google.com/bigquery/docs/information-schema-jobs)
- [dbt 파티션 설정 (BigQuery)](https://docs.getdbt.com/reference/resource-configs/bigquery-configs#partition-clause)
- 코스 내 관련 파일:
  - `.claude/hooks/bq-cost-guard.sh` — 쿼리 비용 가드 훅
  - `.claude/commands/check-cost.md` — 비용 확인 커맨드
  - `references/gcp-bigquery-setup.md` — BigQuery 환경 설정 가이드
  - `instructor-setup-guide.md` — 강사용 설정 가이드 (섹션 8: 비용 관리)

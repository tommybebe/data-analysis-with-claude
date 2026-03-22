# 강사 설정 가이드

> 이 문서는 "하니스 엔지니어링 for 데이터 분석" 코스의 **강사(또는 자기 학습자)**가 실습 환경을 준비하기 위한 가이드입니다.
> 학습자에게 배포하는 스타터 레포와 BigQuery 데이터셋을 사전에 구성하는 전 과정을 다룹니다.

---

## 목차

1. [사전 요구사항](#1-사전-요구사항)
2. [GCP 프로젝트 및 BigQuery 설정](#2-gcp-프로젝트-및-bigquery-설정)
3. [합성 데이터 생성 및 적재](#3-합성-데이터-생성-및-적재)
   - [3.0 합성 데이터 설계 개요](#30-합성-데이터-설계-개요)
   - [3.1 환경 설정 및 스크립트 준비](#31-환경-설정-및-스크립트-준비)
   - [3.2 CLI 옵션 전체 레퍼런스](#32-cli-옵션-전체-레퍼런스)
   - [3.3 소규모 테스트 데이터 생성](#33-소규모-테스트-데이터-생성-강사-빠른-검증용)
   - [3.4 전체 규모 데이터 생성](#34-전체-규모-데이터-생성)
   - [3.5 BigQuery에 직접 적재](#35-bigquery에-직접-적재)
   - [3.6 데이터 검증 쿼리](#36-데이터-검증-쿼리)
   - [3.7 한국어 레이블 특성 심층 검증](#37-한국어-레이블-특성-심층-검증)
   - [3.8 DAU/MAU 기본 검증](#38-daumau-기본-검증)
   - [3.9 데이터 초기화 및 재생성](#39-데이터-초기화-및-재생성)
   - [3.10 스크립트 코드 구조 및 한국어 호환성 심층 가이드](#310-스크립트-코드-구조-및-한국어-호환성-심층-가이드)
4. [스타터 레포지토리 준비](#4-스타터-레포지토리-준비)
   - [4.1 레포 구조](#41-레포-구조)
     - [4.1.1 스타터 레포 파일 트리](#411-스타터-레포-파일-트리)
     - [4.1.2 필수 파일 역할 및 설계 근거](#412-필수-파일-역할-및-설계-근거)
   - [4.2 스타터 레포 생성 절차](#42-스타터-레포-생성-절차)
   - [4.3 setup.sh 작성](#43-setupsh-작성)
   - [4.4 pyproject.toml 예시](#44-pyprojecttoml-예시)
   - [4.5 profiles.yml.example](#45-profilesymlexample)
   - [4.6 .gitignore](#46-gitignore)
   - [4.7 marimo 노트북 템플릿 준비](#47-marimo-노트북-템플릿-준비)
   - [4.8 학습자 배포 절차](#48-학습자-배포-절차)
   - [4.9 학습자 필수 도구 사전 설치 가이드](#49-학습자-필수-도구-사전-설치-가이드)
     - [4.9.1 필수 도구 체크리스트](#491-필수-도구-체크리스트)
     - [4.9.2 도구별 설치 방법](#492-도구별-설치-방법)
     - [4.9.3 일괄 환경 확인 스크립트](#493-일괄-환경-확인-스크립트)
     - [4.9.4 GCP 계정 및 Claude 구독 사전 준비 안내](#494-gcp-계정-및-claude-구독-사전-준비-안내)
5. [GitHub 설정](#5-github-설정)
6. [dbt 프로젝트 검증](#6-dbt-프로젝트-검증)
7. [학습자 배포 체크리스트](#7-학습자-배포-체크리스트)
8. [BigQuery 비용 관리 가이드라인](#8-bigquery-비용-관리-가이드라인)
   - [8.1 BigQuery 요금 구조 및 무료 구간](#81-bigquery-요금-구조-및-무료-구간)
     - [8.1.1 온디맨드(On-Demand) 요금 모델](#811-온디맨드on-demand-요금-모델)
     - [8.1.2 슬롯 예약 vs 온디맨드 비교](#812-슬롯-예약-vs-온디맨드-비교)
     - [8.1.3 교육 환경별 예상 비용 요약](#813-교육-환경별-예상-비용-요약)
   - [8.2 쿼리 비용 추정 방법](#82-쿼리-비용-추정-방법)
     - [8.2.1 쿼리 실행 전 드라이 런으로 비용 추정](#821-쿼리-실행-전-드라이-런dry-run으로-비용-추정)
     - [8.2.2 Python으로 드라이 런 자동화](#822-python으로-드라이-런-자동화)
     - [8.2.3 BigQuery Console에서 쿼리 비용 확인](#823-bigquery-console에서-쿼리-비용-확인)
     - [8.2.4 bq-cost-guard 훅을 통한 자동 비용 제어](#824-bq-cost-guard-훅을-통한-자동-비용-제어)
   - [8.3 예산 알림 설정](#83-예산-알림-설정)
     - [8.3.1 GCP Console에서 예산 알림 설정](#831-gcp-console에서-예산-알림-설정-gui)
     - [8.3.2 gcloud CLI로 예산 알림 설정](#832-gcloud-cli로-예산-알림-설정)
     - [8.3.3 BigQuery 쿼리 비용 한도 설정](#833-bigquery-쿼리-비용-한도-설정-프로젝트-수준)
     - [8.3.4 서비스 계정별 예산 추적을 위한 레이블 전략](#834-서비스-계정별-예산-추적을-위한-레이블-전략)
   - [8.4 비용 모니터링 쿼리](#84-비용-모니터링-쿼리)
     - [8.4.1 일별 쿼리 처리량 및 추정 비용](#841-일별-쿼리-처리량-및-추정-비용)
     - [8.4.2 사용자별 처리량 집계](#842-사용자별-처리량-집계)
     - [8.4.3 학습자 레이블 기반 비용 분리](#843-학습자-레이블-기반-비용-분리-레이블-전략-사용-시)
     - [8.4.4 비용 임계값 초과 쿼리 탐지](#844-비용-임계값-초과-쿼리-탐지)
     - [8.4.5 월별 누적 비용 대시보드용 쿼리](#845-월별-누적-비용-대시보드용-쿼리)
   - [8.5 비용 절감 권장 사항](#85-비용-절감-권장-사항)
     - [8.5.1 쿼리 최적화 전략](#851-쿼리-최적화-전략)
     - [8.5.2 dbt 모델 설정 최적화](#852-dbt-모델-설정-최적화)
     - [8.5.3 개발 환경에서의 데이터 샘플링](#853-개발-환경에서의-데이터-샘플링)
     - [8.5.4 Claude Code 비용 훅 활용](#854-claude-code-비용-훅-활용)
   - [8.6 학습자별 사용량 모니터링](#86-학습자별-사용량-모니터링)
     - [8.6.1 공유 프로젝트에서 학습자별 모니터링](#861-공유-프로젝트에서-학습자별-모니터링)
     - [8.6.2 학습자별 독립 프로젝트 환경에서의 모니터링](#862-학습자별-독립-프로젝트-환경에서의-모니터링)
     - [8.6.3 이상 사용 탐지 및 대응](#863-이상-사용-탐지-및-대응)
     - [8.6.4 비용 리포트 자동화 (주간)](#864-비용-리포트-자동화-주간)
   - [8.7 코스 종료 후 리소스 정리](#87-코스-종료-후-리소스-정리)
     - [8.7.1 BigQuery 데이터셋 삭제](#871-bigquery-데이터셋-삭제)
     - [8.7.2 서비스 계정 키 및 계정 삭제](#872-서비스-계정-키-및-계정-삭제)
     - [8.7.3 프로젝트 삭제 (선택)](#873-프로젝트-삭제-선택--완전-정리)
     - [8.7.4 정리 체크리스트](#874-정리-체크리스트)
9. [문제 해결(트러블슈팅)](#9-문제-해결트러블슈팅)

---

## 1. 사전 요구사항

### 강사 환경

| 항목 | 요구사항 | 확인 방법 |
|------|----------|-----------|
| GCP 계정 | 프로젝트 생성 및 BigQuery 접근 권한 | `gcloud projects list` |
| `gcloud` CLI | 최신 버전 설치 | `gcloud --version` |
| Python 3.11+ | 합성 데이터 스크립트 실행 | `python3 --version` |
| uv | Python 패키지 관리 | `uv --version` |
| Node.js 18+ | Claude Code CLI 설치 | `node --version` |
| GitHub CLI (`gh`) | 레포 생성, 라벨 등록 | `gh --version` |
| dbt-core + dbt-bigquery | dbt 모델 검증 | `dbt --version` |
| Claude Code Pro/Max 구독 | Claude Code CLI 및 Agent SDK | `claude --version` |

### 비용 안내

이 코스에서 사용하는 BigQuery는 **on-demand 가격** 모델을 사용합니다.

| 리소스 | 예상 비용 | 비고 |
|--------|-----------|------|
| BigQuery 저장 | ~$0.02/월 | 합성 데이터 약 500MB 미만 |
| BigQuery 쿼리 | ~$0.50~$2.00/월 (학습자 1인 기준) | 첫 1TB/월 무료 |
| GitHub Actions | 무료 (공개 레포) 또는 월 2,000분 무료 (비공개 레포) | GitHub Free 플랜 기준 |

> **참고**: GCP 신규 계정은 $300 무료 크레딧이 제공됩니다. 교육용으로 충분한 규모입니다.

---

## 2. GCP 프로젝트 및 BigQuery 설정

### 2.0 GCP 계정 생성 (최초 설정 시)

> 이미 GCP 계정이 있다면 이 단계를 건너뛰세요.

#### 2.0.1 Google 계정으로 GCP 가입

1. [https://console.cloud.google.com](https://console.cloud.google.com) 접속
2. 기존 Google 계정으로 로그인 (또는 새 계정 생성)
3. **"시작하기"** 또는 **"무료로 시작"** 클릭
4. 국가 선택 (대한민국) 및 이용약관 동의
5. 결제 계정 설정: 신용카드/체크카드 정보 입력
   - **무료 체험**: 신규 계정에 $300 크레딧이 제공됩니다 (90일간 유효)
   - 자동 청구를 방지하려면 체험 종료 후 반드시 결제 계정을 비활성화하세요

> **교육용 비용 안내**: 이 코스의 실습은 합성 데이터(약 500MB)와 소량의 쿼리만 사용합니다.
> $300 크레딧의 약 1~5% 이내로 충분히 완료할 수 있습니다.

#### 2.0.2 gcloud CLI 설치

```bash
# macOS — Homebrew 사용
brew install --cask google-cloud-sdk

# 또는 공식 설치 스크립트 (macOS/Linux 공통)
curl https://sdk.cloud.google.com | bash
exec -l $SHELL  # 셸 재시작

# 설치 확인
gcloud --version
```

#### 2.0.3 gcloud 인증

```bash
# 브라우저 인증 (GCP 계정으로 로그인)
gcloud auth login

# Application Default Credentials 설정 (로컬 개발 및 스크립트 실행에 필요)
gcloud auth application-default login

# 인증 확인
gcloud auth list
```

예상 출력:
```
                      Credentialed Accounts
ACTIVE  ACCOUNT
*       your-email@gmail.com

To set the active account, run:
    $ gcloud config set account `ACCOUNT`
```

---

### 2.1 GCP 프로젝트 생성

```bash
# 프로젝트 생성 (프로젝트 ID는 전역 고유해야 함)
export GCP_PROJECT_ID="fittrack-analysis-course"
gcloud projects create $GCP_PROJECT_ID --name="FitTrack Analysis Course"

# 프로젝트 활성화
gcloud config set project $GCP_PROJECT_ID

# 결제 계정 연결 (필수 — BigQuery 사용을 위해)
gcloud billing accounts list
gcloud billing projects link $GCP_PROJECT_ID --billing-account=<BILLING_ACCOUNT_ID>
```

### 2.2 BigQuery API 활성화

```bash
gcloud services enable bigquery.googleapis.com --project=$GCP_PROJECT_ID
```

### 2.3 BigQuery 데이터셋 생성

이 코스는 세 개의 데이터셋을 사용합니다:

| 데이터셋 | 용도 | 접근 주체 | 데이터 계층 |
|----------|------|-----------|-------------|
| `raw` | 합성 원시 이벤트 데이터 저장 | 강사 적재 후 학습자 읽기 전용 | Bronze / Raw |
| `dbt_dev` | dbt 모델 빌드 결과 — 로컬 개발 환경 | 학습자 읽기/쓰기 | Silver / Gold |
| `dbt_ci` | dbt 모델 빌드 결과 — GitHub Actions CI | GitHub Actions 서비스 계정 | Silver / Gold |

> **`dbt_ci` 필요 이유**: `profiles.yml.example`의 `ci` 타깃이 `dbt_ci` 데이터셋에 결과를 기록합니다.
> GitHub Actions의 `dbt-ci.yml` 워크플로는 `--target ci` 옵션으로 실행되므로 이 데이터셋이 없으면 CI 파이프라인이 실패합니다.

```bash
# 1) raw 데이터셋 생성 (리전: US — 무료 티어 적용)
bq mk --dataset \
  --location=US \
  --description="FitTrack 모바일 앱 원시 이벤트 데이터 (합성)" \
  ${GCP_PROJECT_ID}:raw

# 2) dbt 개발 환경 데이터셋 생성 (로컬 dbt run --target dev 결과)
bq mk --dataset \
  --location=US \
  --description="dbt 변환 모델 결과 — 로컬 개발(dev) 환경" \
  ${GCP_PROJECT_ID}:dbt_dev

# 3) dbt CI 환경 데이터셋 생성 (GitHub Actions dbt build --target ci 결과)
bq mk --dataset \
  --location=US \
  --description="dbt 변환 모델 결과 — GitHub Actions CI 환경" \
  ${GCP_PROJECT_ID}:dbt_ci

# 생성 확인
bq ls --project_id=$GCP_PROJECT_ID
```

예상 출력:
```
  datasetId
 -----------
  dbt_ci
  dbt_dev
  raw
```

> **리전 선택 참고**: `US` 멀티 리전은 BigQuery 무료 쿼리 처리량(매월 첫 1TB)이 적용됩니다.
> 레이턴시보다 비용 최적화를 우선하므로 이 코스에서는 `US`를 사용합니다.
> 한국 시장 데이터만 다루는 프로덕션 환경이라면 `asia-northeast3`(서울)을 권장합니다.

### 2.4 서비스 계정 생성

학습자가 BigQuery에 접근할 때 사용할 서비스 계정을 생성합니다.

```bash
# 서비스 계정 생성
export SA_NAME="fittrack-analyst"
gcloud iam service-accounts create $SA_NAME \
  --display-name="FitTrack Analysis Service Account" \
  --description="코스 실습용 BigQuery 접근 서비스 계정"

# 서비스 계정 이메일 확인
export SA_EMAIL="${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
echo "서비스 계정: $SA_EMAIL"
```

### 2.5 서비스 계정 권한 부여

```bash
# BigQuery 데이터 편집자 (테이블 읽기/쓰기)
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/bigquery.dataEditor"

# BigQuery 작업 사용자 (쿼리 실행)
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/bigquery.jobUser"
```

> **보안 참고**: `bigquery.admin` 역할이 아닌 최소 권한(`dataEditor` + `jobUser`)만 부여합니다. 학습자가 프로젝트 설정을 변경하거나 다른 데이터셋에 접근하는 것을 방지합니다.

### 2.6 서비스 계정 JSON 키 생성

```bash
# JSON 키 생성
gcloud iam service-accounts keys create ./gcp-sa-key.json \
  --iam-account=$SA_EMAIL

# 키 파일 확인
cat gcp-sa-key.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'프로젝트: {d[\"project_id\"]}\n이메일: {d[\"client_email\"]}')"
```

> ⚠️ **주의**: `gcp-sa-key.json` 파일은 절대 Git에 커밋하지 마세요. `.gitignore`에 `*.json` 키 패턴을 추가하세요.

### 2.7 IAM 권한 요약 및 역할 참조

#### 최소 권한 원칙 요약

이 코스에서는 **최소 권한(principle of least privilege)** 원칙을 따릅니다.

| 역할 | 설명 | 필요 이유 |
|------|------|-----------|
| `roles/bigquery.dataEditor` | 테이블 읽기/쓰기/삭제 | dbt 모델 빌드 결과를 `dbt_dev` 데이터셋에 기록 |
| `roles/bigquery.jobUser` | 쿼리 작업 제출 및 실행 | `bq query`, dbt 실행 시 BigQuery Job 생성 |

> **부여하지 않는 역할**:
> - `roles/bigquery.admin`: 데이터셋 생성/삭제, 프로젝트 설정 변경 가능 — 불필요
> - `roles/owner` / `roles/editor`: 과도한 권한 — 절대 학습자에게 부여 금지

#### 데이터셋 수준 세밀한 권한 제어 (선택 사항)

학습자가 `raw` 데이터셋에는 읽기만 허용하고 `dbt_dev`에만 쓰기를 허용하려면:

```bash
# raw 데이터셋: 읽기 전용 (dbt sources 참조용)
bq update --dataset \
  --set_label env:course \
  ${GCP_PROJECT_ID}:raw

# 데이터셋 수준 IAM 설정 (JSON으로 권한 파일 작성)
cat > /tmp/raw_acl.json << 'EOF'
{
  "access": [
    {"role": "OWNER", "specialGroup": "projectOwners"},
    {"role": "READER", "userByEmail": "REPLACE_WITH_SA_EMAIL"}
  ]
}
EOF

# 실제 서비스 계정 이메일로 치환
sed -i "s/REPLACE_WITH_SA_EMAIL/${SA_EMAIL}/" /tmp/raw_acl.json

# ACL 적용
bq update --source /tmp/raw_acl.json ${GCP_PROJECT_ID}:raw
```

> **참고**: 위의 데이터셋 수준 권한 제어는 선택 사항입니다. 프로젝트 수준의
> `dataEditor` + `jobUser` 조합으로도 충분하며, 이것이 이 코스의 기본 설정입니다.

### 2.8 BigQuery 테이블 스키마 참조

이 섹션은 `raw` 데이터셋에 적재될 세 테이블의 스키마를 문서화합니다.
실제 테이블은 섹션 3에서 데이터 생성 스크립트로 생성됩니다.

#### 2.8.1 `raw.raw_users` 테이블

| 컬럼명 | BigQuery 타입 | 설명 | 예시 값 |
|--------|--------------|------|---------|
| `user_id` | `STRING` | 사용자 고유 식별자 (UUID v4) | `"550e8400-e29b-41d4-a716-..."` |
| `signup_timestamp` | `TIMESTAMP` | 가입 시각 (UTC) | `2025-03-15 09:23:41 UTC` |
| `signup_date` | `DATE` | 가입 일자 (UTC) | `2025-03-15` |
| `country` | `STRING` | 국가 코드 (ISO 3166-1 alpha-2) | `"KR"`, `"US"`, `"JP"` |
| `language` | `STRING` | 언어 코드 | `"ko"`, `"en"`, `"ja"` |
| `platform` | `STRING` | 앱 플랫폼 | `"ios"`, `"android"` |
| `device_type` | `STRING` | 디바이스 유형 | `"smartphone"`, `"tablet"` |
| `initial_app_version` | `STRING` | 가입 시점 앱 버전 | `"3.2.1"` |
| `subscription_tier` | `STRING` | 구독 등급 | `"free"`, `"premium"`, `"premium_plus"` |
| `age_group` | `STRING` | 연령대 (선택값, NULL 가능) | `"25-34"`, `"35-44"` |
| `referral_source` | `STRING` | 유입 채널 | `"organic"`, `"paid_search"` |
| `is_active` | `BOOLEAN` | 활성 사용자 여부 | `true`, `false` |
| `last_active_date` | `DATE` | 마지막 활동 일자 (NULL 가능) | `2026-03-20` |
| `_loaded_at` | `TIMESTAMP` | 적재 시각 (dbt freshness 검사용) | `2026-03-21 00:00:00 UTC` |

#### 2.8.2 `raw.raw_sessions` 테이블

| 컬럼명 | BigQuery 타입 | 설명 | 예시 값 |
|--------|--------------|------|---------|
| `session_id` | `STRING` | 세션 고유 식별자 (UUID v4) | `"a3f7b2c1-..."` |
| `user_id` | `STRING` | 사용자 식별자 (raw_users 참조) | `"550e8400-..."` |
| `session_start` | `TIMESTAMP` | 세션 시작 시각 (UTC) | `2025-06-10 14:22:00 UTC` |
| `session_end` | `TIMESTAMP` | 세션 종료 시각 (NULL = 비정상 종료) | `2025-06-10 14:35:42 UTC` |
| `session_date` | `DATE` | 세션 시작 일자 (파티션 키) | `2025-06-10` |
| `session_duration_seconds` | `INTEGER` | 세션 지속 시간(초), NULL 가능 | `822` |
| `platform` | `STRING` | 앱 플랫폼 | `"ios"`, `"android"` |
| `app_version` | `STRING` | 앱 버전 | `"3.2.1"` |
| `device_model` | `STRING` | 디바이스 모델명 | `"iPhone 16 Pro"` |
| `os_version` | `STRING` | OS 버전 | `"iOS 18.3"` |
| `ip_country` | `STRING` | 접속 국가 (IP 기반) | `"KR"` |
| `event_count` | `INTEGER` | 세션 내 이벤트 수 | `12` |
| `screen_count` | `INTEGER` | 세션 내 화면 조회 수 | `5` |
| `_loaded_at` | `TIMESTAMP` | 적재 시각 | `2026-03-21 00:00:00 UTC` |

#### 2.8.3 `raw.raw_events` 테이블

| 컬럼명 | BigQuery 타입 | 설명 | 예시 값 |
|--------|--------------|------|---------|
| `event_id` | `STRING` | 이벤트 고유 식별자 (UUID v4) | `"b7c3d1e2-..."` |
| `event_timestamp` | `TIMESTAMP` | 이벤트 발생 시각 (UTC) | `2025-06-10 14:23:15 UTC` |
| `event_date` | `DATE` | 이벤트 발생 일자 (파티션 키) | `2025-06-10` |
| `user_id` | `STRING` | 사용자 식별자 (raw_users 참조) | `"550e8400-..."` |
| `session_id` | `STRING` | 세션 식별자 (raw_sessions 참조) | `"a3f7b2c1-..."` |
| `event_type` | `STRING` | 이벤트 유형 (아래 허용값 참조) | `"workout_start"` |
| `platform` | `STRING` | 앱 플랫폼 | `"ios"`, `"android"` |
| `app_version` | `STRING` | 앱 버전 | `"3.2.1"` |
| `device_model` | `STRING` | 디바이스 모델명 | `"Galaxy S25"` |
| `event_properties` | `JSON` | 이벤트별 부가 속성 (BigQuery JSON 네이티브 타입) | `{"screen": "home"}` |
| `_loaded_at` | `TIMESTAMP` | 적재 시각 | `2026-03-21 00:00:00 UTC` |

> **`event_properties` 타입**: `--load-to-bigquery` 스크립트 방식으로 적재하면 BigQuery `JSON` 네이티브 타입으로 저장됩니다.
> 이 경우 `JSON_VALUE(event_properties, '$.key')` 함수로 직접 파싱 가능합니다.
> `bq load --autodetect` 방식은 이 컬럼을 `STRING`으로 로드하며, 섹션 3.5의 명시적 스키마 파일에서도 `JSON` 타입으로 지정해야 합니다.

**`event_type` 허용값**:
`app_open`, `app_close`, `screen_view`, `workout_start`, `workout_complete`,
`goal_set`, `goal_achieved`, `social_share`, `purchase`, `push_notification_open`

### 2.9 예산 알림 설정 (비용 관리)

BigQuery on-demand 요금은 쿼리 처리량 기준으로 청구됩니다.
실수로 대규모 풀 스캔 쿼리가 실행될 경우를 대비하여 예산 알림을 설정합니다.

#### GCP Console에서 예산 설정

1. [GCP Console → 결제 → 예산 및 알림](https://console.cloud.google.com/billing/budgets) 이동
2. **"예산 만들기"** 클릭
3. 설정값:
   - **범위**: 특정 프로젝트 선택 → `fittrack-analysis-course`
   - **예산 유형**: 지정된 금액
   - **금액**: `$10` (학습자 1인 기준 월 최대 예상 비용의 5배 안전 마진)
   - **알림 임계값**: 50%, 90%, 100%
   - **이메일 수신인**: 강사 이메일

#### gcloud로 예산 설정 (CLI 방식)

```bash
# 결제 계정 ID 확인
BILLING_ACCOUNT_ID=$(gcloud billing accounts list --format="value(name)" --filter="open=true" | head -1)
echo "결제 계정: $BILLING_ACCOUNT_ID"

# 예산 생성 (gcloud beta billing budgets create)
gcloud beta billing budgets create \
  --billing-account=$BILLING_ACCOUNT_ID \
  --display-name="FitTrack Course Budget" \
  --budget-amount=10USD \
  --threshold-rule=percent=0.5 \
  --threshold-rule=percent=0.9 \
  --threshold-rule=percent=1.0
```

> **참고**: `gcloud beta billing budgets` 명령어는 `gcloud components install beta`가 필요합니다.
> CLI 설정이 불편하다면 GCP Console UI에서 설정하는 것을 권장합니다.

#### bq-cost-guard 훅 사전 확인

코스 실습에서는 Claude Code 훅(`bq-cost-guard.sh`)이 쿼리 실행 전 비용을 추정합니다.
이 훅은 모듈 2에서 학습자가 직접 구성하지만, 강사는 사전에 동작 방식을 이해해 두세요:

```bash
# 쿼리 비용 추정 (dry-run 모드)
bq query --use_legacy_sql=false --dry_run "
SELECT COUNT(*) FROM \`${GCP_PROJECT_ID}.raw.raw_events\`
"
# 출력 예: "Query successfully validated. Assuming the tables are not modified,
#           running this query will process 52428800 bytes."
# 50MB → 약 $0.0003 (1TB당 $5 기준)
```

### 2.10 GCP 설정 최종 검증

모든 설정이 완료된 후 아래 명령어로 전체를 검증합니다.

```bash
# ────────────────────────────────────────────
# GCP 설정 검증 스크립트
# ────────────────────────────────────────────

echo "=== 1. 프로젝트 확인 ==="
gcloud config get-value project
# 예상: fittrack-analysis-course

echo ""
echo "=== 2. BigQuery API 활성화 확인 ==="
gcloud services list --enabled --filter="name:bigquery.googleapis.com"
# 예상: bigquery.googleapis.com 이 목록에 있어야 함

echo ""
echo "=== 3. 데이터셋 목록 확인 ==="
bq ls --project_id=$GCP_PROJECT_ID
# 예상: raw, dbt_dev, dbt_ci 세 데이터셋이 보여야 함

echo ""
echo "=== 4. 서비스 계정 확인 ==="
gcloud iam service-accounts describe $SA_EMAIL
# 예상: displayName: FitTrack Analysis Service Account

echo ""
echo "=== 5. IAM 바인딩 확인 ==="
gcloud projects get-iam-policy $GCP_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:$SA_EMAIL" \
  --format="table(bindings.role)"
# 예상:
# ROLE
# roles/bigquery.dataEditor
# roles/bigquery.jobUser

echo ""
echo "=== 6. 서비스 계정으로 BigQuery 접근 테스트 ==="
GOOGLE_APPLICATION_CREDENTIALS="./gcp-sa-key.json" \
bq query --use_legacy_sql=false \
  "SELECT 'GCP BigQuery 설정 완료' AS status, CURRENT_TIMESTAMP() AS verified_at"
# 예상: status = 'GCP BigQuery 설정 완료', verified_at = 현재 시각
```

모든 검증이 통과하면 GCP 설정이 완료된 것입니다.
다음 단계(섹션 3)에서 합성 데이터를 생성하고 BigQuery에 적재합니다.

---

## 3. 합성 데이터 생성 및 적재

### 3.0 합성 데이터 설계 개요

이 코스의 합성 데이터는 **B2C 모바일 피트니스 앱 "FitTrack"**의 사용자 행동 로그를 시뮬레이션합니다.
데이터 분석 실습에 필요한 현실적인 패턴과 **한국 시장 특성**을 반영하도록 설계되었습니다.

#### 데이터 테이블 구조 요약

| 테이블 | 예상 행 수 | 핵심 컬럼 |
|--------|------------|-----------|
| `raw.raw_users` | ~10,000 | `user_id`, `signup_timestamp`, `country`, `language`, `platform`, `subscription_tier` |
| `raw.raw_sessions` | ~150,000 | `session_id`, `user_id`, `session_start`, `session_end`, `session_duration_seconds` |
| `raw.raw_events` | ~500,000 | `event_id`, `event_timestamp`, `user_id`, `session_id`, `event_type`, `event_properties` |

#### 한국 시장 특성 반영 항목

| 특성 | 값 | 설계 근거 |
|------|----|-----------|
| 국가 분포 | KR 40%, US 25%, JP 15%, TW 8%, TH 7%, VN 5% | 한국 출시 앱의 실제 글로벌 분포 패턴 |
| 플랫폼 비율 | iOS 55%, Android 45% | 한국 스마트폰 시장 점유율 반영 |
| 언어 코드 | `language = "ko"` (KR 사용자) | ISO 639-1 언어 코드, dbt 필터링 실습용 |
| 기기 모델 | Galaxy S25, Galaxy A55 등 Galaxy 시리즈 중심 | 한국 Android 시장 삼성전자 점유율 반영 |
| 구매 가격 | KRW(원화) 기준 (9,900원, 79,900원 등) | `event_properties.price_krw` 컬럼 |
| 소셜 공유 | `kakao`, `instagram`, `twitter`, `facebook` | 카카오 포함 한국 소셜미디어 환경 |
| 활동 시간대 | 오전 7-9시(KST), 오후 6-10시(KST) 피크 | UTC로 저장, KST 오프셋(+9h) 고려 |
| 이탈 패턴 | 가입 후 90일 전후로 이탈 급증 | 모바일 앱 리텐션 실제 패턴 시뮬레이션 |

#### 코스 실습과의 연계

| 모듈 | 사용 데이터 | 실습 분석 |
|------|------------|-----------|
| 모듈 1 | `raw_users` (국가·언어 필터) | AGENTS.md 컨텍스트 작성 실습 |
| 모듈 2 | `raw_events` (전체) | DAU/MAU 분석, 비용 가드 실습 |
| 모듈 3 | `raw_sessions`, `raw_events` | 코호트 리텐션 분석 자동화 |
| 모듈 4 | 전체 테이블 | 복합 분석 시나리오 (심화) |

---

### 3.1 환경 설정 및 스크립트 준비

#### 의존성 설치

```bash
# CSV 생성에 필요한 패키지 (기본)
uv pip install numpy pandas

# Parquet 형식 출력이 필요한 경우 추가 설치
uv pip install pyarrow

# BigQuery 직접 적재가 필요한 경우 추가 설치
# 참고: 스크립트는 google-cloud-bigquery만 사용합니다 (pandas-gbq 불필요)
uv pip install google-cloud-bigquery
```

> **uv를 사용하지 않는 경우**: `pip install numpy pandas` 또는
> `pip install numpy pandas pyarrow google-cloud-bigquery`
>
> **`pandas-gbq` vs `google-cloud-bigquery`**: `generate_synthetic_data.py`는
> `google.cloud.bigquery.Client.load_table_from_dataframe()`을 사용하므로
> `google-cloud-bigquery` 패키지만 있으면 충분합니다. `pandas-gbq`는 별도로 필요하지 않습니다.

#### 스크립트 위치 확인

```bash
# 스타터 레포 기준
ls -la scripts/generate_synthetic_data.py

# 또는 코스 리소스에서 직접 실행
ls -la examples/generate_synthetic_data.py
```

---

### 3.2 CLI 옵션 전체 레퍼런스

`generate_synthetic_data.py`가 지원하는 모든 옵션입니다. 강사는 실습 환경에 맞게 조정하세요.

```
옵션                     기본값           설명
─────────────────────────────────────────────────────────────────
--num-users N            10,000          생성할 사용자 수
--start-date YYYY-MM-DD  2025-01-01      데이터 시작 일자
--end-date   YYYY-MM-DD  2026-03-31      데이터 종료 일자 (현재 기준)
--output-dir PATH        ./output        CSV/Parquet 출력 디렉토리
--format     csv|parquet|both  csv       출력 파일 형식
--events-per-session N   8               세션당 평균 이벤트 수 (최소 2)
--seed N                 42              난수 시드 (재현 가능성 보장)
--load-to-bigquery       (플래그)        BigQuery에 직접 적재
--project-id ID          없음 (필수)     GCP 프로젝트 ID
--dataset    NAME        raw             BigQuery 데이터셋 이름
```

**재현성 보장**: `--seed 42`(기본값)를 사용하면 동일 환경에서 항상 동일한 데이터가 생성됩니다.
학습자 간 결과 비교 및 강사 데모에 일관성을 유지합니다.

---

### 3.3 소규모 테스트 데이터 생성 (강사 빠른 검증용)

BigQuery 적재 전에 로컬에서 데이터 품질을 빠르게 확인합니다.
1,000명 × 3개월 데이터는 수 초 내에 생성됩니다.

```bash
# 소규모 테스트 데이터 생성 (1,000명, 최근 3개월)
python examples/generate_synthetic_data.py \
  --num-users 1000 \
  --start-date 2026-01-01 \
  --end-date 2026-03-31 \
  --output-dir ./output-test/

# 생성된 파일 크기 확인
ls -lh output-test/
# 예상 출력:
# raw_users.csv      ~100KB  (~1,000행)
# raw_sessions.csv   ~1.5MB  (~15,000행)
# raw_events.csv     ~5MB    (~50,000행)
```

#### 로컬 검증 Python 스크립트

생성된 CSV 파일의 핵심 통계를 빠르게 확인합니다:

```python
import pandas as pd

# 테이블 로드
users = pd.read_csv("output-test/raw_users.csv")
sessions = pd.read_csv("output-test/raw_sessions.csv")
events = pd.read_csv("output-test/raw_events.csv")

# 행 수 확인
print(f"사용자: {len(users):,}명")
print(f"세션: {len(sessions):,}개")
print(f"이벤트: {len(events):,}개")

# 한국어 레이블 확인
print("\n--- 국가별 사용자 분포 ---")
print(users["country"].value_counts(normalize=True).mul(100).round(1).to_string())

print("\n--- 언어 코드 분포 ---")
print(users["language"].value_counts().to_string())

print("\n--- 플랫폼 분포 (한국 시장 특성: iOS ~55%) ---")
print(users["platform"].value_counts(normalize=True).mul(100).round(1).to_string())

print("\n--- 구독 등급 분포 ---")
print(users["subscription_tier"].value_counts().to_string())

print("\n--- 이벤트 유형 분포 ---")
print(events["event_type"].value_counts().to_string())

# KR 사용자의 언어 코드가 'ko'인지 확인
kr_users = users[users["country"] == "KR"]
print(f"\n--- KR 사용자 언어 코드 검증 ---")
print(f"KR 사용자 수: {len(kr_users)}명")
print(f"language='ko' 비율: {(kr_users['language'] == 'ko').mean() * 100:.1f}%")

# 한국어 소셜 공유 (카카오) 확인
kakao_events = events[
    events["event_type"] == "social_share"
].copy()
kakao_events["share_target"] = kakao_events["event_properties"].apply(
    lambda x: eval(x).get("share_target") if pd.notna(x) else None
)
print(f"\n--- 소셜 공유 채널 분포 (카카오 포함) ---")
print(kakao_events["share_target"].value_counts().to_string())

# KRW 가격 확인
purchase_events = events[events["event_type"] == "purchase"].copy()
purchase_events["item"] = purchase_events["event_properties"].apply(
    lambda x: eval(x) if pd.notna(x) else {}
)
print(f"\n--- 구매 이벤트 샘플 (KRW 가격 포함) ---")
print(purchase_events["event_properties"].head(3).to_string())
```

예상 출력 (1,000명, `--seed 42`):
```
사용자: 1,000명
세션: 약 14,000~16,000개
이벤트: 약 45,000~55,000개

--- 국가별 사용자 분포 ---
KR    40.1%
US    25.2%
JP    14.8%
TW     8.1%
TH     7.0%
VN     4.8%

--- 언어 코드 분포 ---
ko     401
en     252
ja     148
zh-TW   81
th      70
vi      48

--- 플랫폼 분포 (한국 시장 특성: iOS ~55%) ---
ios       55.2%
android   44.8%

--- KR 사용자 언어 코드 검증 ---
KR 사용자 수: 401명
language='ko' 비율: 100.0%

--- 소셜 공유 채널 분포 (카카오 포함) ---
kakao      25~28%
instagram  24~27%
twitter    24~26%
facebook   22~25%
```

---

### 3.4 전체 규모 데이터 생성

코스 실습용 전체 데이터셋을 생성합니다 (10,000명, 약 15개월).
생성 시간: 약 5~15분 (로컬 머신 사양에 따라 다름).

```bash
# 전체 규모 CSV 생성
python examples/generate_synthetic_data.py \
  --num-users 10000 \
  --start-date 2025-01-01 \
  --end-date 2026-03-31 \
  --output-dir ./output/ \
  --format csv

# 생성 완료 후 파일 크기 확인
ls -lh output/
# 예상 출력:
# raw_users.csv      ~1.2MB  (~10,000행)
# raw_sessions.csv   ~18MB   (~150,000행)
# raw_events.csv     ~60MB   (~500,000행)
```

#### CSV + Parquet 동시 생성 (BigQuery 적재 방식 선택 시 유용)

```bash
# CSV와 Parquet 모두 생성
python examples/generate_synthetic_data.py \
  --format both \
  --output-dir ./output/

# Parquet 파일은 CSV 대비 약 70-80% 더 작음 (압축 효과)
ls -lh output/*.parquet
# 예상 출력:
# raw_users.parquet      ~400KB
# raw_sessions.parquet   ~4MB
# raw_events.parquet     ~12MB
```

---

### 3.5 BigQuery에 직접 적재

#### 방법 1: 스크립트 직접 적재 (권장)

```bash
# BigQuery 적재에 필요한 패키지 설치 (google-cloud-bigquery만 필요)
uv pip install google-cloud-bigquery

# BigQuery에 직접 적재 (전체 규모)
python examples/generate_synthetic_data.py \
  --load-to-bigquery \
  --project-id $GCP_PROJECT_ID \
  --dataset raw \
  --num-users 10000 \
  --start-date 2025-01-01 \
  --end-date 2026-03-31

# 예상 출력:
# ⬆️  <project>.raw.raw_users 적재 중... (10,000행)
#    ✅ raw_users 적재 완료
# ⬆️  <project>.raw.raw_sessions 적재 중... (~150,000행)
#    ✅ raw_sessions 적재 완료
# ⬆️  <project>.raw.raw_events 적재 중... (~500,000행)
#    ✅ raw_events 적재 완료
```

#### 방법 2: CSV → BigQuery 수동 적재 (방법 1 실패 시)

로컬에서 CSV 파일을 먼저 생성한 후, `bq load` 명령어로 적재합니다.

```bash
# 1단계: CSV 생성
python examples/generate_synthetic_data.py --output-dir ./output/

# 2단계: raw_users 적재
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  --autodetect \
  ${GCP_PROJECT_ID}:raw.raw_users \
  ./output/raw_users.csv

# 3단계: raw_sessions 적재
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  --autodetect \
  ${GCP_PROJECT_ID}:raw.raw_sessions \
  ./output/raw_sessions.csv

# 4단계: raw_events 적재
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  --autodetect \
  ${GCP_PROJECT_ID}:raw.raw_events \
  ./output/raw_events.csv
```

> **스키마 자동 감지 주의**: `--autodetect`는 TIMESTAMP 타입을 STRING으로 잘못 감지할 수 있습니다.
> 스키마 오류 발생 시 아래 명시적 스키마 파일을 사용하세요.
>
> **`event_properties` 타입 주의**: `--load-to-bigquery` 스크립트 방식은 이 컬럼을 `JSON` 네이티브 타입으로
> 적재합니다. `bq load --autodetect`나 명시적 스키마 `STRING` 방식은 `JSON_VALUE()` 함수로 직접
> 파싱 가능한 JSON 네이티브 타입이 아닌 문자열로 저장됩니다.
> **섹션 3.7의 `JSON_VALUE()` 검증 쿼리는 스크립트 방식(`--load-to-bigquery`)으로 적재한 경우에만 올바르게 동작합니다.**
> CSV `bq load` 방식을 사용하는 경우 `event_properties` 쿼리 시 `JSON_VALUE()` 대신 `JSON_EXTRACT_SCALAR()`를
> 사용하거나, STRING 필드에 `PARSE_JSON()` 래퍼를 추가하세요.

```bash
# 명시적 스키마로 raw_events 적재 (스키마 오류 시)
# event_properties를 JSON 네이티브 타입으로 적재 → JSON_VALUE() 쿼리 정상 동작
cat > /tmp/events_schema.json << 'EOF'
[
  {"name": "event_id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "user_id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "session_id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "event_type", "type": "STRING", "mode": "REQUIRED"},
  {"name": "event_timestamp", "type": "TIMESTAMP", "mode": "REQUIRED"},
  {"name": "event_date", "type": "DATE", "mode": "REQUIRED"},
  {"name": "platform", "type": "STRING", "mode": "REQUIRED"},
  {"name": "app_version", "type": "STRING", "mode": "REQUIRED"},
  {"name": "device_model", "type": "STRING", "mode": "NULLABLE"},
  {"name": "event_properties", "type": "JSON", "mode": "NULLABLE"},
  {"name": "_loaded_at", "type": "TIMESTAMP", "mode": "REQUIRED"}
]
EOF

bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  --schema /tmp/events_schema.json \
  ${GCP_PROJECT_ID}:raw.raw_events \
  ./output/raw_events.csv
```

#### 적재 결과 확인

```bash
# 테이블 목록 확인
bq ls ${GCP_PROJECT_ID}:raw

# 예상 출력:
#      tableId      Type    Labels   Time Partitioning   Clustered Fields
#  --------------- ------- -------- ------------------- ------------------
#   raw_events      TABLE
#   raw_sessions    TABLE
#   raw_users       TABLE
```

---

### 3.6 데이터 검증 쿼리

적재된 데이터가 정상인지 확인합니다.

#### 기본 행 수 및 날짜 범위 확인

```bash
# 테이블별 행 수 확인
bq query --use_legacy_sql=false "
SELECT
  'raw_users'    AS table_name, COUNT(*) AS row_count FROM \`${GCP_PROJECT_ID}.raw.raw_users\`
UNION ALL
SELECT
  'raw_sessions', COUNT(*) FROM \`${GCP_PROJECT_ID}.raw.raw_sessions\`
UNION ALL
SELECT
  'raw_events',   COUNT(*) FROM \`${GCP_PROJECT_ID}.raw.raw_events\`
ORDER BY 1
"
```

예상 출력:
```
table_name     row_count
raw_events     498,234
raw_sessions   149,871
raw_users       10,000
```

```bash
# 이벤트 데이터 날짜 범위 확인
bq query --use_legacy_sql=false "
SELECT
  MIN(event_timestamp) AS earliest_event,
  MAX(event_timestamp) AS latest_event,
  COUNT(DISTINCT event_date) AS total_days,
  COUNT(DISTINCT user_id) AS unique_users
FROM \`${GCP_PROJECT_ID}.raw.raw_events\`
"
```

---

### 3.7 한국어 레이블 특성 심층 검증

이 코스의 핵심 특성인 **한국어 레이블 데이터**가 올바르게 생성되었는지 확인합니다.

#### 국가·언어 코드 분포 확인

```bash
# 국가별 사용자 수 및 비율 (KR이 ~40%여야 함)
bq query --use_legacy_sql=false "
SELECT
  country,
  language,
  COUNT(*) AS user_count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct
FROM \`${GCP_PROJECT_ID}.raw.raw_users\`
GROUP BY country, language
ORDER BY user_count DESC
"
```

예상 출력:
```
country  language  user_count  pct
KR       ko         4,005      40.1
US       en         2,512      25.1
JP       ja         1,483      14.8
TW       zh-TW        812       8.1
TH       th           698       7.0
VN       vi           490       4.9
```

#### KR 사용자 언어 코드 일관성 검증

```bash
# KR 사용자는 반드시 language = 'ko'여야 함
bq query --use_legacy_sql=false "
SELECT
  country,
  language,
  COUNT(*) AS cnt
FROM \`${GCP_PROJECT_ID}.raw.raw_users\`
WHERE country = 'KR' AND language != 'ko'
"
# 예상: 0건 (이 쿼리 결과가 비어 있어야 정상)
```

#### 플랫폼 분포 확인 (한국 시장 특성)

```bash
# 플랫폼 분포 (한국 시장: iOS ~55%, Android ~45%)
bq query --use_legacy_sql=false "
SELECT
  platform,
  COUNT(*) AS event_count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct
FROM \`${GCP_PROJECT_ID}.raw.raw_events\`
GROUP BY platform
ORDER BY event_count DESC
"
```

예상 출력:
```
platform  event_count  pct
ios       276,043      55.5
android   221,191      44.5
```

#### 카카오 소셜 공유 이벤트 확인

```bash
# social_share 이벤트에서 카카오 비중 확인
bq query --use_legacy_sql=false "
SELECT
  JSON_VALUE(event_properties, '$.share_target') AS share_target,
  COUNT(*) AS cnt,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct
FROM \`${GCP_PROJECT_ID}.raw.raw_events\`
WHERE event_type = 'social_share'
GROUP BY share_target
ORDER BY cnt DESC
"
```

예상 출력 (각 채널 약 25% 균등 분포):
```
share_target  cnt     pct
kakao         3,412   25.8
instagram     3,387   25.6
twitter       3,302   25.0
facebook      3,128   23.6
```

#### KRW 구매 이벤트 확인

```bash
# purchase 이벤트의 상품명 및 KRW 가격 분포
bq query --use_legacy_sql=false "
SELECT
  JSON_VALUE(event_properties, '$.item_name') AS item_name,
  JSON_VALUE(event_properties, '$.price_krw') AS price_krw,
  COUNT(*) AS purchase_count
FROM \`${GCP_PROJECT_ID}.raw.raw_events\`
WHERE event_type = 'purchase'
GROUP BY item_name, price_krw
ORDER BY purchase_count DESC
"
```

예상 출력:
```
item_name          price_krw  purchase_count
premium_monthly    9900       ~1,200
workout_pack       4900       ~1,200
premium_annual     79900      ~1,200
theme_bundle       2900       ~1,200
```

#### 활동 시간대 검증 (KST 기준 피크 타임)

```bash
# UTC → KST 변환 후 시간대별 활동 분포 확인
# KST 오전 7-9시 (UTC 22-00시), 오후 6-10시 (UTC 09-13시)에 피크가 있어야 함
bq query --use_legacy_sql=false "
SELECT
  EXTRACT(HOUR FROM DATETIME(event_timestamp, 'Asia/Seoul')) AS hour_kst,
  COUNT(*) AS event_count
FROM \`${GCP_PROJECT_ID}.raw.raw_events\`
GROUP BY hour_kst
ORDER BY hour_kst
"
```

#### 이탈 패턴 확인 (가입 후 90일 이탈 패턴)

```bash
# 가입 후 경과일별 활성 사용자 비율 (90일 근방에서 이탈 증가해야 함)
bq query --use_legacy_sql=false "
SELECT
  is_active,
  COUNT(*) AS user_count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct
FROM \`${GCP_PROJECT_ID}.raw.raw_users\`
GROUP BY is_active
"
# 예상: is_active=true 약 65-70%, is_active=false 약 30-35%
```

---

### 3.8 DAU/MAU 기본 검증

dbt mart 모델이 기대하는 결과를 생성할 수 있는지, 원시 데이터로 간단한 DAU/MAU를 직접 쿼리합니다.

```bash
# 최근 30일 DAU 트렌드 확인
bq query --use_legacy_sql=false "
SELECT
  event_date,
  COUNT(DISTINCT user_id) AS dau
FROM \`${GCP_PROJECT_ID}.raw.raw_events\`
WHERE event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY event_date
ORDER BY event_date DESC
LIMIT 10
"
```

```bash
# 월별 MAU 트렌드 확인
bq query --use_legacy_sql=false "
SELECT
  FORMAT_DATE('%Y-%m', event_date) AS month,
  COUNT(DISTINCT user_id) AS mau
FROM \`${GCP_PROJECT_ID}.raw.raw_events\`
GROUP BY month
ORDER BY month DESC
"
```

```bash
# DAU/MAU 비율(스티키니스) 확인 — 최근 완전한 달 기준
bq query --use_legacy_sql=false "
WITH
dau AS (
  SELECT event_date, COUNT(DISTINCT user_id) AS dau
  FROM \`${GCP_PROJECT_ID}.raw.raw_events\`
  WHERE FORMAT_DATE('%Y-%m', event_date) = FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH))
  GROUP BY event_date
),
mau AS (
  SELECT COUNT(DISTINCT user_id) AS mau
  FROM \`${GCP_PROJECT_ID}.raw.raw_events\`
  WHERE FORMAT_DATE('%Y-%m', event_date) = FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH))
)
SELECT
  ROUND(AVG(dau.dau), 0) AS avg_dau,
  mau.mau,
  ROUND(AVG(dau.dau) / mau.mau, 3) AS dau_mau_ratio
FROM dau, mau
GROUP BY mau.mau
"
# 정상 범위: DAU/MAU 비율 0.15 ~ 0.30 (합성 데이터 기준)
```

---

### 3.9 데이터 초기화 및 재생성

#### BigQuery 테이블 삭제 및 재생성

실습 데이터를 초기 상태로 리셋하거나, 다른 파라미터로 재생성할 때 사용합니다.

```bash
# 기존 테이블 삭제
bq rm -f ${GCP_PROJECT_ID}:raw.raw_events
bq rm -f ${GCP_PROJECT_ID}:raw.raw_sessions
bq rm -f ${GCP_PROJECT_ID}:raw.raw_users

# 재생성 (기본 설정)
python examples/generate_synthetic_data.py \
  --load-to-bigquery \
  --project-id $GCP_PROJECT_ID \
  --dataset raw
```

#### 다른 시드로 재생성 (학습자별 고유 데이터 제공 시)

```bash
# 학습자별 고유 데이터 생성 예시 (시드값을 다르게 지정)
# 학습자 A: --seed 100
python examples/generate_synthetic_data.py \
  --seed 100 \
  --load-to-bigquery \
  --project-id learner-a-project \
  --dataset raw

# 학습자 B: --seed 200
python examples/generate_synthetic_data.py \
  --seed 200 \
  --load-to-bigquery \
  --project-id learner-b-project \
  --dataset raw
```

> **참고**: 시드를 다르게 해도 전체적인 분포(KR 40%, iOS 55% 등)는 동일하게 유지됩니다.
> 실제 수치만 소폭 달라집니다.

#### 데이터 재생성 전체 자동화 스크립트

```bash
#!/usr/bin/env bash
# reset-and-reload-data.sh
# 합성 데이터 초기화 및 재적재 자동화 스크립트

set -euo pipefail

GCP_PROJECT_ID="${GCP_PROJECT_ID:?GCP_PROJECT_ID 환경변수를 설정하세요}"
DATASET="raw"
SCRIPT_PATH="examples/generate_synthetic_data.py"

echo "⚠️  ${GCP_PROJECT_ID}.${DATASET} 데이터셋의 모든 테이블을 삭제하고 재생성합니다."
read -p "계속하시겠습니까? (y/N): " confirm
[[ "$confirm" == "y" || "$confirm" == "Y" ]] || { echo "취소되었습니다."; exit 0; }

echo ""
echo "🗑️  기존 테이블 삭제 중..."
bq rm -f --table ${GCP_PROJECT_ID}:${DATASET}.raw_events   && echo "  ✅ raw_events 삭제"
bq rm -f --table ${GCP_PROJECT_ID}:${DATASET}.raw_sessions && echo "  ✅ raw_sessions 삭제"
bq rm -f --table ${GCP_PROJECT_ID}:${DATASET}.raw_users    && echo "  ✅ raw_users 삭제"

echo ""
echo "🔄 합성 데이터 재생성 및 적재 시작..."
python "$SCRIPT_PATH" \
  --load-to-bigquery \
  --project-id "$GCP_PROJECT_ID" \
  --dataset "$DATASET"

echo ""
echo "✅ 데이터 재생성 완료!"
echo "   테이블 목록:"
bq ls ${GCP_PROJECT_ID}:${DATASET}
```

---

### 3.10 스크립트 코드 구조 및 한국어 호환성 심층 가이드

이 섹션은 강사가 `generate_synthetic_data.py`의 내부 구조를 이해하고, 필요 시 커스터마이징하거나
트러블슈팅할 수 있도록 코드 아키텍처와 한국어 호환성 설계를 상세히 설명합니다.

---

#### 3.10.1 스크립트 아키텍처 개요

```
generate_synthetic_data.py
│
├── 상수 정의 (전역, 모듈 상단)
│   ├── COUNTRY_DISTRIBUTION       — 국가별 사용자 비율 (KR 40%)
│   ├── COUNTRY_LANGUAGE_MAP       — 국가 → 언어 코드 매핑 (KR → "ko")
│   ├── PLATFORM_WEIGHTS           — iOS/Android 비율 (한국 시장: iOS 55%)
│   ├── SUBSCRIPTION_TIERS         — 구독 등급 분포
│   ├── AGE_GROUPS                 — 연령대 분포
│   ├── HOUR_WEIGHTS               — 시간대별 활동 분포 (KST 기준)
│   ├── DEVICE_MODELS              — 기기 모델 목록 (Galaxy 시리즈 포함)
│   └── EVENT_TYPES / EVENT_TYPE_BASE_WEIGHTS — 이벤트 유형 및 발생 비율
│
├── 유틸리티 함수
│   ├── generate_uuid(seed_str)    — 재현 가능한 UUID 생성 (시드 기반)
│   ├── weighted_choice(rng, opts) — 가중치 기반 랜덤 선택
│   ├── compute_churn_probability()— 이탈 확률 계산 (시그모이드 함수)
│   └── compute_daily_activity_probability() — 일일 활동 확률 계산
│
├── SyntheticDataGenerator 클래스
│   ├── __init__()                 — 생성기 초기화 (사용자 수, 기간, 시드 등)
│   ├── generate_all()             — 전체 데이터 생성 순서 제어
│   ├── _generate_users()          — raw_users 테이블 생성
│   ├── _generate_sessions()       — raw_sessions 테이블 생성 (일자별 순회)
│   ├── _generate_events()         — raw_events 테이블 생성 (세션별 순회)
│   ├── _derive_session_screen_count() — screen_count 역산 (events 기반)
│   ├── _create_event_record()     — 개별 이벤트 레코드 생성
│   ├── _generate_event_properties()   — 이벤트별 추가 속성 생성 (KRW 가격 포함)
│   ├── _print_summary()           — 생성 완료 후 통계 출력
│   ├── _add_loaded_at()           — dbt 신선도 검사용 _loaded_at 컬럼 추가
│   ├── save_to_csv()              — CSV 저장
│   ├── save_to_parquet()          — Parquet 저장 (pyarrow 필요)
│   ├── save()                     — 형식 선택 저장 (csv/parquet/both)
│   └── load_to_bigquery()         — BigQuery 직접 적재 (google-cloud-bigquery 필요)
│
└── main()                         — CLI 인터페이스 (argparse)
```

---

#### 3.10.2 한국어 호환성 구현 상세

`generate_synthetic_data.py`가 "한국어 호환" 데이터를 생성하는 방식을 레이어별로 설명합니다.

##### 레이어 1: 국가·언어 코드 (raw_users 기반 필터링)

```python
# 국가 분포: KR 40% 비중으로 한국 시장 주도적 앱 시뮬레이션
COUNTRY_DISTRIBUTION = {"KR": 0.40, "US": 0.25, "JP": 0.15, "TW": 0.08, "TH": 0.07, "VN": 0.05}

# 국가 → 언어 코드 1:1 매핑 (dbt 모델에서 language = 'ko' 필터링 실습용)
COUNTRY_LANGUAGE_MAP = {
    "KR": "ko",   # ← BigQuery에서 WHERE language = 'ko' 필터로 KR 사용자 격리 가능
    "US": "en",
    "JP": "ja",
    "TW": "zh-TW",
    ...
}
```

**실습 연계**: dbt `stg_users.sql`에서 `WHERE language = 'ko'` 또는 `country = 'KR'`로
한국 사용자만 집계하는 필터 실습이 가능합니다.

##### 레이어 2: 한국 시장 디바이스 분포

```python
# 플랫폼 비율: 한국 스마트폰 시장 점유율 반영 (iOS 55%, Android 45%)
PLATFORM_WEIGHTS = {"ios": 0.55, "android": 0.45}

# Android 기기 모델: 삼성전자 Galaxy 시리즈 중심 (한국 Android 시장 점유율 반영)
DEVICE_MODELS = {
    "android": [
        "Galaxy S25 Ultra", "Galaxy S25", "Galaxy S24 Ultra", "Galaxy S24",
        "Galaxy A55", "Galaxy A35",  # ← 중저가 라인업 포함
        "Galaxy Z Flip 6", "Galaxy Z Fold 6",  # ← 폴더블 포함
        ...
    ],
}
```

##### 레이어 3: KRW(원화) 가격 데이터

```python
# purchase 이벤트 event_properties에 포함되는 KRW 가격
items = [
    {"item": "premium_monthly", "price": 9900},   # 월 구독 9,900원
    {"item": "premium_annual",  "price": 79900},  # 연 구독 79,900원
    {"item": "workout_pack",    "price": 4900},   # 운동 팩 4,900원
    {"item": "theme_bundle",    "price": 2900},   # 테마 번들 2,900원
]
return {"item_name": selected["item"], "price_krw": int(selected["price"])}
```

**실습 연계**: BigQuery에서 `JSON_VALUE(event_properties, '$.price_krw')`로 KRW 가격을
추출하는 SQL 실습이 가능합니다.

##### 레이어 4: 한국 소셜 미디어 (카카오)

```python
# social_share 이벤트의 공유 채널에 카카오 포함
share_targets = ["kakao", "instagram", "twitter", "facebook"]
return {"share_target": self.rng.choice(share_targets)}
```

**실습 연계**: `WHERE JSON_VALUE(event_properties, '$.share_target') = 'kakao'`로
카카오 공유 이벤트만 집계하는 퍼널 분석 실습이 가능합니다.

##### 레이어 5: KST 활동 시간대 패턴

```python
# UTC 기준 시간대 가중치 — KST(UTC+9) 피크 타임 반영
# KST 오전 7-9시 = UTC 22-00시 전날 → HOUR_WEIGHTS[22-23] 높음
# KST 오후 6-10시 = UTC 09-13시    → HOUR_WEIGHTS[09-13] 높음
HOUR_WEIGHTS = np.array([
    0.3, 0.2, 0.1, 0.05, 0.03, 0.02,   # UTC 00-05 (KST 09-14) ← 낮 피크
    0.04, 0.06, 0.10, 0.15, 0.18, 0.20, # UTC 06-11 (KST 15-20) ← 오후 피크
    ...
    0.05, 0.07, 0.10, 0.25, 0.35, 0.32, # UTC 18-23 (KST 03-08) ← 오전 피크
])
```

**BigQuery 검증**: `EXTRACT(HOUR FROM DATETIME(event_timestamp, 'Asia/Seoul'))`으로
KST 기준 피크 타임(7-9시, 18-22시)을 확인할 수 있습니다.

---

#### 3.10.3 UTF-8 인코딩 및 한국어 텍스트 호환성

현재 데이터셋은 영문 필드값을 사용하지만, 한국어 텍스트를 포함하도록 확장하는 경우를 위해
인코딩 처리를 명시합니다.

**현재 한국어 호환성 확보 방법**:

```python
# event_properties JSON 직렬화 시 ensure_ascii=False 사용
# → 한국어 문자열(유니코드)을 이스케이프 없이 그대로 저장
event_properties_json = json.dumps(event_properties, ensure_ascii=False)
# 예: {"workout_type": "런닝"} → '{"workout_type": "런닝"}' (이스케이프 없음)
# ensure_ascii=True 시: '{"workout_type": "\\ub7f0\\ub2dd"}' (이스케이프됨)
```

**CSV 파일 저장 인코딩**:

```python
# pandas DataFrame.to_csv()의 기본 인코딩은 UTF-8
# 한국어 문자가 포함된 경우 명시적으로 encoding='utf-8-sig' 권장 (Excel 호환)
df.to_csv("output.csv", index=False, encoding="utf-8")  # 현재 스크립트 방식
# Excel에서 열리도록 하려면:
# df.to_csv("output.csv", index=False, encoding="utf-8-sig")
```

**BigQuery 적재 시 인코딩**:

```bash
# bq load 기본값은 UTF-8 처리
# 한국어 문자가 포함된 CSV 파일 적재 시 --encoding 플래그로 명시 가능
bq load --encoding=UTF-8 --source_format=CSV ...
```

> **현재 데이터셋 인코딩 상태**: `generate_synthetic_data.py`가 생성하는 데이터에는
> ASCII 범위의 영문 텍스트만 포함되어 있습니다 (한국어 한글 문자 없음).
> 한국어 UI 레이블(예: screen_name에 한국어 화면명)을 추가하려면 `_generate_event_properties()`
> 메서드의 `screens` 리스트를 수정하고, CSV 저장 시 `encoding="utf-8-sig"`를 사용하세요.

---

#### 3.10.4 데이터 생성 파라미터 커스터마이징 가이드

강사가 코스 시나리오에 맞게 데이터 특성을 조정하는 방법입니다.

##### 한국 시장 비중 조정 (KR 사용자 비율 변경)

```python
# generate_synthetic_data.py 상단의 상수 수정 예시
# KR 비중을 60%로 높여 한국 특화 분석 심화 시나리오

COUNTRY_DISTRIBUTION = {"KR": 0.60, "US": 0.20, "JP": 0.10, "TW": 0.05, "TH": 0.03, "VN": 0.02}
```

##### 유료 구독 비율 조정 (매출 분석 실습용)

```python
# 프리미엄 사용자 비율을 높여 매출 분석 데이터 풍부화
SUBSCRIPTION_TIERS = {"free": 0.40, "premium": 0.40, "premium_plus": 0.20}
```

##### KRW 가격 항목 추가

```python
# _generate_event_properties() 메서드의 purchase 처리 부분에 항목 추가
items = [
    {"item": "premium_monthly",   "price": 9900},
    {"item": "premium_annual",    "price": 79900},
    {"item": "workout_pack",      "price": 4900},
    {"item": "theme_bundle",      "price": 2900},
    # 새 항목 추가 예시:
    {"item": "personal_training", "price": 29900},  # 퍼스널 트레이닝 29,900원
    {"item": "nutrition_plan",    "price": 14900},  # 식단 플랜 14,900원
]
```

##### 한국어 screen_name 추가 (선택 사항)

```python
# _generate_event_properties()의 screen_view 처리 부분에 한국어 화면명 추가
screens = [
    "home",              # 홈 화면
    "workout_list",      # 운동 목록
    "workout_detail",    # 운동 상세
    "profile",           # 프로필
    "settings",          # 설정
    "social_feed",       # 소셜 피드
    "leaderboard",       # 리더보드
    "goals",             # 목표
    # 한국어 레이블 추가 시 (ensure_ascii=False로 저장 가능):
    # "홈", "운동목록", "프로필", "설정", "소셜피드"
]
```

> **주의**: 한국어 screen_name 추가 시 CSV 저장 시 `encoding='utf-8-sig'`를 사용하고,
> BigQuery 스키마에서 해당 컬럼이 STRING 타입인지 확인하세요.

---

#### 3.10.5 성능 및 생성 시간 가이드

| 규모 | 사용자 수 | 기간 | 예상 세션 수 | 예상 이벤트 수 | 생성 시간 (M2 MacBook Pro) |
|------|-----------|------|--------------|----------------|--------------------------|
| 소규모 (테스트) | 1,000 | 3개월 | ~15,000 | ~50,000 | 약 20~30초 |
| 중규모 | 5,000 | 6개월 | ~100,000 | ~350,000 | 약 2~4분 |
| 전체 규모 (코스 기본) | 10,000 | 15개월 | ~150,000 | ~500,000 | 약 5~10분 |
| 대규모 (심화 실습) | 50,000 | 12개월 | ~700,000 | ~2,500,000 | 약 30~60분 |

> **병목 지점**: `_generate_sessions()` 메서드는 날짜 × 사용자 수 이중 루프로 동작합니다.
> 전체 규모(10,000명 × 450일)에서 약 450만 번 반복합니다.
> 대규모 데이터가 필요한 경우 `--num-users`와 `--start-date`/`--end-date` 기간을 분리 생성 후
> CSV를 병합하는 방법을 고려하세요.

---

#### 3.10.6 한국어 호환 데이터 완결성 체크리스트

BigQuery 적재 후 데이터가 코스 실습 목적에 맞게 생성되었는지 확인하는 최종 체크리스트입니다.

```bash
# ─────────────────────────────────────────────────────────────────
# 한국어 호환 데이터 완결성 검증 스크립트
# 사용법: bash verify_korean_data.sh
# 전제조건: GCP_PROJECT_ID 환경변수 설정 완료
# ─────────────────────────────────────────────────────────────────

set -euo pipefail
PROJECT="${GCP_PROJECT_ID:?GCP_PROJECT_ID를 설정하세요}"
PASS=0; FAIL=0

check() {
    local label="$1"
    local query="$2"
    local expected="$3"
    local result
    result=$(bq query --use_legacy_sql=false --format=csv --quiet "$query" | tail -1)
    if echo "$result" | grep -qE "$expected"; then
        echo "  ✅ $label"
        PASS=$((PASS+1))
    else
        echo "  ❌ $label (예상: $expected, 실제: $result)"
        FAIL=$((FAIL+1))
    fi
}

echo "=== 1. 테이블 존재 및 행 수 확인 ==="
check "raw_users 10,000행 이상" \
    "SELECT COUNT(*) FROM \`${PROJECT}.raw.raw_users\`" \
    "^[1-9][0-9]{4,}"

check "raw_sessions 100,000행 이상" \
    "SELECT COUNT(*) FROM \`${PROJECT}.raw.raw_sessions\`" \
    "^[1-9][0-9]{5,}"

check "raw_events 400,000행 이상" \
    "SELECT COUNT(*) FROM \`${PROJECT}.raw.raw_events\`" \
    "^[3-9][0-9]{5,}"

echo ""
echo "=== 2. 한국어 호환성 검증 ==="
check "KR 사용자 비율 35~45%" \
    "SELECT ROUND(COUNTIF(country='KR')*100.0/COUNT(*),0) FROM \`${PROJECT}.raw.raw_users\`" \
    "^(3[5-9]|4[0-5])"

check "KR 사용자 language='ko' 100%" \
    "SELECT COUNT(*) FROM \`${PROJECT}.raw.raw_users\` WHERE country='KR' AND language!='ko'" \
    "^0$"

check "iOS 비율 50~60%" \
    "SELECT ROUND(COUNTIF(platform='ios')*100.0/COUNT(*),0) FROM \`${PROJECT}.raw.raw_users\`" \
    "^(5[0-9]|60)"

check "Galaxy 기기 존재 확인" \
    "SELECT COUNT(*) FROM \`${PROJECT}.raw.raw_sessions\` WHERE device_model LIKE 'Galaxy%'" \
    "^[1-9]"

echo ""
echo "=== 3. KRW 가격 데이터 검증 ==="
check "purchase 이벤트 존재" \
    "SELECT COUNT(*) FROM \`${PROJECT}.raw.raw_events\` WHERE event_type='purchase'" \
    "^[1-9]"

check "price_krw 필드 존재 및 유효값 (9900 또는 79900)" \
    "SELECT COUNT(*) FROM \`${PROJECT}.raw.raw_events\` WHERE event_type='purchase' AND JSON_VALUE(event_properties,'\$.price_krw') IN ('9900','79900','4900','2900')" \
    "^[1-9]"

echo ""
echo "=== 4. 카카오 소셜 공유 검증 ==="
check "social_share kakao 이벤트 존재" \
    "SELECT COUNT(*) FROM \`${PROJECT}.raw.raw_events\` WHERE event_type='social_share' AND JSON_VALUE(event_properties,'\$.share_target')='kakao'" \
    "^[1-9]"

echo ""
echo "=== 5. KST 시간대 피크 검증 ==="
check "KST 오후 6-10시(UTC 09-13시) 활동 존재" \
    "SELECT COUNT(*) FROM \`${PROJECT}.raw.raw_events\` WHERE EXTRACT(HOUR FROM event_timestamp) BETWEEN 9 AND 13" \
    "^[1-9]"

echo ""
echo "=== 6. dbt 신선도 검사 컬럼 확인 ==="
check "_loaded_at 컬럼 NULL 없음 (users)" \
    "SELECT COUNT(*) FROM \`${PROJECT}.raw.raw_users\` WHERE _loaded_at IS NULL" \
    "^0$"

echo ""
echo "─────────────────────────────────"
echo "검증 결과: ✅ ${PASS}개 통과 / ❌ ${FAIL}개 실패"
if [ "$FAIL" -eq 0 ]; then
    echo "🎉 모든 검증 통과 — BigQuery 적재가 정상적으로 완료되었습니다!"
else
    echo "⚠️  위의 실패 항목을 확인하고 데이터 재생성을 검토하세요 (섹션 3.9 참조)."
fi
```

**체크리스트 항목 요약:**

| 검증 항목 | 기대값 | 실패 시 조치 |
|-----------|--------|-------------|
| raw_users 행 수 | ≥ 10,000 | `--num-users 10000` 재실행 |
| raw_sessions 행 수 | ≥ 100,000 | 전체 기간 재실행 확인 |
| raw_events 행 수 | ≥ 400,000 | 이벤트 생성 완료 여부 확인 |
| KR 사용자 비율 | 35~45% | `COUNTRY_DISTRIBUTION` 상수 확인 |
| KR language='ko' 일관성 | 100% | `COUNTRY_LANGUAGE_MAP` 확인 |
| iOS 비율 | 50~60% | `PLATFORM_WEIGHTS` 확인 |
| Galaxy 기기 존재 | ≥ 1건 | `DEVICE_MODELS["android"]` 확인 |
| KRW 가격 데이터 | ≥ 1건 | `_generate_event_properties()` 확인 |
| 카카오 소셜 공유 | ≥ 1건 | `share_targets` 리스트 확인 |
| _loaded_at NULL 없음 | 0건 | `_add_loaded_at()` 호출 여부 확인 |

---

#### 3.10.7 일반적인 문제 해결 (한국어 데이터 관련)

| 증상 | 원인 | 해결 방법 |
|------|------|-----------|
| `JSON_VALUE()` 쿼리 오류 | `event_properties`가 STRING 타입으로 로드됨 | `--load-to-bigquery` 방식 사용 또는 `PARSE_JSON()` 래퍼 추가 |
| KR 비율이 40%가 아닌 경우 | 난수 시드 차이 | `--seed 42`(기본값) 명시 실행 |
| `pandas` ImportError | 패키지 미설치 | `uv pip install numpy pandas` 재실행 |
| BigQuery 인증 오류 | ADC 미설정 | `gcloud auth application-default login` 재실행 |
| CSV 로드 시 한국어 깨짐 | 인코딩 불일치 | `bq load --encoding=UTF-8` 명시 |
| `pyarrow` ImportError | Parquet 저장 시 패키지 미설치 | `uv pip install pyarrow` 설치 |
| 세션 생성 속도 느림 | 10,000명 × 450일 대규모 루프 | 규모 축소(`--num-users 5000`) 또는 기간 단축 고려 |

---

## 4. 스타터 레포지토리 준비

### 4.1 레포 구조

#### 4.1.1 스타터 레포 파일 트리

스타터 레포에는 다음이 **포함**됩니다:

```
fittrack-analysis/
├── .gitignore                  # 커밋 제외 파일 목록 (SA 키, profiles.yml 등)
├── pyproject.toml              # Python 의존성 (uv 호환)
├── uv.lock                     # 의존성 잠금 파일 (재현 가능한 환경)
├── setup.sh                    # 로컬 환경 자동 설정 스크립트
├── README.md                   # 프로젝트 소개 및 빠른 시작 가이드
│
├── dbt_project.yml             # dbt 프로젝트 설정 (프로필명·모델 경로·구체화 규칙)
├── packages.yml                # dbt 패키지 의존성 (dbt-utils, dbt-expectations)
├── profiles.yml.example        # dbt 프로필 템플릿 (실제 사용 시 ~/.dbt/profiles.yml로 복사)
│
├── models/
│   ├── staging/
│   │   ├── sources.yml         # BigQuery 소스 정의 (raw 데이터셋 참조)
│   │   ├── schema.yml          # staging 모델 문서·테스트 정의
│   │   ├── stg_events.sql      # 이벤트 스테이징 (타입 캐스팅, NULL 처리)
│   │   ├── stg_users.sql       # 사용자 스테이징
│   │   └── stg_sessions.sql    # 세션 스테이징
│   ├── intermediate/
│   │   ├── schema.yml          # intermediate 모델 문서·테스트 정의
│   │   ├── int_user_daily_activity.sql  # 사용자별 일별 활동 집계
│   │   └── int_user_metrics.sql         # 사용자 메트릭 (총 이벤트·세션 수)
│   └── marts/
│       ├── schema.yml          # mart 모델 문서·테스트 정의
│       ├── fct_daily_active_users.sql    # DAU 집계 (파티션 테이블)
│       ├── fct_monthly_active_users.sql  # MAU 집계 (파티션 테이블)
│       ├── fct_retention_cohort.sql      # 코호트 리텐션
│       └── fct_feature_engagement.sql    # 기능별 참여도 지표
│
├── notebooks/
│   ├── README.md               # 노트북 사용 방법 안내
│   ├── explore_template.py     # 데이터 탐색 템플릿 (모듈 2용, TODO 섹션 포함)
│   └── analysis_template.py    # DAU/MAU 분석 리포트 템플릿 (모듈 2·3용)
│
└── scripts/
    └── generate_synthetic_data.py  # 합성 데이터 생성 (로컬 파일 또는 BQ 직접 적재)
```

다음은 **포함하지 않습니다** (학습자가 직접 작성):

| 항목 | 작성 시점 | 이유 |
|------|-----------|------|
| `AGENTS.md` | 모듈 1 | 에이전트 컨텍스트 설계가 코스의 핵심 학습 목표 |
| `.claude/settings.json` | 모듈 2 | 훅·권한 설정 구성 경험이 학습 목표 |
| `.claude/commands/*.md` | 모듈 2 | 커스텀 슬래시 커맨드 작성이 학습 목표 |
| `.claude/hooks/*.sh` | 모듈 2 | 훅 스크립트 설계·구현이 학습 목표 |
| `.github/workflows/*.yml` | 모듈 3 | GitHub Actions YAML 작성이 학습 목표 |
| `.github/ISSUE_TEMPLATE/*.yml` | 모듈 3 | 이슈 템플릿 설계가 학습 목표 |
| 실제 분석 노트북 (`.py`) | 모듈 2·3 | 에이전트가 자동 생성하는 산출물 |
| GitHub Issue 라벨 | 모듈 3 | 라벨 등록 자동화 스크립트 작성이 학습 목표 |

> **설계 원칙**: 스타터 레포는 "데이터 인프라(dbt 모델, 데이터)"를 제공하되, "하니스(AGENTS.md, 훅, 워크플로)"는 학습자가 직접 구축하도록 의도적으로 비워둡니다.
> 학습자는 기존 분석 작업 기반 위에서 에이전트 자동화 계층을 추가하는 경험을 합니다.

#### 4.1.2 필수 파일 역할 및 설계 근거

스타터 레포에 포함된 각 파일의 역할과 포함 이유를 정리합니다.

**루트 설정 파일**

| 파일 | 역할 | 학습자가 수정해야 하는가? |
|------|------|--------------------------|
| `.gitignore` | SA 키, `profiles.yml`, `.venv/`, `target/` 등 민감 파일·빌드 산출물 제외 | 필요 시 추가 가능 |
| `pyproject.toml` | Python 의존성 전체 목록 (dbt, marimo, google-cloud-bigquery 등) | 선택 사항 |
| `uv.lock` | 의존성 버전 고정 — 모든 학습자가 동일한 환경을 재현 | 수정 금지 (uv가 자동 관리) |
| `setup.sh` | uv, Claude Code CLI, marimo 설치 여부 확인 및 자동 설치 | 수정 불필요 |
| `README.md` | 빠른 시작 절차 (clone → setup.sh → profiles.yml 수정 → dbt debug) | 수정 불필요 |

**dbt 설정 파일**

| 파일 | 역할 | 학습자가 수정해야 하는가? |
|------|------|--------------------------|
| `dbt_project.yml` | dbt 프로젝트명, 모델 경로, 계층별 구체화 방식(view/table) 정의 | 수정 불필요 |
| `packages.yml` | `dbt-utils`, `dbt-expectations` 패키지 버전 고정 | 수정 불필요 |
| `profiles.yml.example` | BigQuery 연결 템플릿 (dev/ci 타깃 포함) — 학습자가 복사하여 사용 | **반드시 복사 후 수정** |

**dbt 모델 (models/)**

| 계층 | 파일 | 구체화 방식 | 역할 |
|------|------|-------------|------|
| staging | `stg_events.sql` | VIEW | 원시 이벤트 데이터 클렌징·타입 정규화 |
| staging | `stg_users.sql` | VIEW | 사용자 데이터 클렌징 |
| staging | `stg_sessions.sql` | VIEW | 세션 데이터 클렌징 |
| intermediate | `int_user_daily_activity.sql` | VIEW | 사용자별 일별 이벤트·세션 집계 |
| intermediate | `int_user_metrics.sql` | VIEW | 사용자 총 메트릭 집계 |
| marts | `fct_daily_active_users.sql` | TABLE (파티션) | DAU 집계 — 에이전트가 주로 쿼리하는 테이블 |
| marts | `fct_monthly_active_users.sql` | TABLE (파티션) | MAU 집계 |
| marts | `fct_retention_cohort.sql` | TABLE (파티션) | 코호트별 리텐션율 |
| marts | `fct_feature_engagement.sql` | TABLE (파티션) | 기능별 참여도 지표 |

> **비용 설계 의도**: staging과 intermediate를 VIEW로 구체화하면 dbt 실행 시 중간 테이블을 저장하지 않아 BigQuery 스토리지 비용이 절감됩니다. 실제 데이터 스캔은 mart TABLE 구체화 시 1회만 발생합니다.

**스크립트 및 노트북**

| 파일 | 역할 |
|------|------|
| `scripts/generate_synthetic_data.py` | FitTrack 앱 합성 이벤트 데이터 생성 (로컬 Parquet 또는 BigQuery 직접 적재) |
| `notebooks/explore_template.py` | 데이터 탐색 marimo 노트북 골격 — 학습자가 TODO 섹션을 채우며 사용 |
| `notebooks/analysis_template.py` | DAU/MAU 분석 리포트 marimo 노트북 골격 — 에이전트가 이를 기반으로 노트북 생성 |

### 4.2 스타터 레포 생성 절차

코스 레포(`data-analysis-with-claude`)를 로컬에 클론한 상태에서 시작합니다.

```bash
# -------------------------------------------------------
# [전제 조건] 코스 레포가 로컬에 존재해야 합니다.
# git clone https://github.com/<org>/data-analysis-with-claude
# cd data-analysis-with-claude
# -------------------------------------------------------

# 1. GitHub에 스타터 레포 생성 (공개 또는 비공개)
gh repo create fittrack-analysis-starter \
  --public \
  --description "하니스 엔지니어링 for 데이터 분석 — 스타터 레포"

# 2. 로컬에 클론 및 이동
gh repo clone fittrack-analysis-starter
cd fittrack-analysis-starter

# -------------------------------------------------------
# 3. 루트 설정 파일 복사
# -------------------------------------------------------
cp ../initialize/examples/dbt-models/dbt_project.yml .
cp ../initialize/examples/dbt-models/packages.yml .
cp ../initialize/examples/dbt-models/profiles.yml.example .

# -------------------------------------------------------
# 4. dbt 모델 전체 복사 (staging + intermediate + marts)
# -------------------------------------------------------
mkdir -p models/staging models/intermediate models/marts

# staging 레이어
cp ../initialize/examples/dbt-models/staging/*.sql models/staging/
cp ../initialize/examples/dbt-models/staging/*.yml models/staging/

# intermediate 레이어
cp ../initialize/examples/dbt-models/intermediate/*.sql models/intermediate/
cp ../initialize/examples/dbt-models/intermediate/*.yml models/intermediate/

# marts 레이어
cp ../initialize/examples/dbt-models/marts/*.sql models/marts/
cp ../initialize/examples/dbt-models/marts/*.yml models/marts/

# -------------------------------------------------------
# 5. 합성 데이터 생성 스크립트 복사
# -------------------------------------------------------
mkdir -p scripts
cp ../initialize/examples/generate_synthetic_data.py scripts/

# -------------------------------------------------------
# 6. marimo 노트북 템플릿 복사 (섹션 4.7 참조)
# -------------------------------------------------------
mkdir -p notebooks

# 7. pyproject.toml 작성 (섹션 4.4 내용으로 생성)
# 8. setup.sh 작성 (섹션 4.3 내용으로 생성) 및 실행 권한 부여
chmod +x setup.sh

# -------------------------------------------------------
# 9. 초기 커밋
# -------------------------------------------------------
git add .
git commit -m "feat: 스타터 레포 초기 구성 (dbt 모델, 노트북 템플릿, 설정 파일)"
git push origin main
```

> **확인**: `git ls-files | sort` 로 커밋된 파일 목록을 확인하세요.
> `gcp-sa-key.json`, `profiles.yml`이 포함되지 않았는지 반드시 검증합니다.

### 4.3 setup.sh 작성

로컬 도구를 자동 설치하는 스크립트를 작성합니다.

```bash
#!/usr/bin/env bash
# setup.sh — FitTrack 분석 프로젝트 로컬 환경 설정
set -euo pipefail

echo "🚀 FitTrack Analysis 개발 환경을 설정합니다..."
echo ""

# -------------------------------------------------------
# 1. uv 설치 확인 및 설치
# -------------------------------------------------------
if ! command -v uv &> /dev/null; then
    echo "📦 uv를 설치합니다..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
else
    echo "✅ uv가 이미 설치되어 있습니다: $(uv --version)"
fi

# -------------------------------------------------------
# 2. Python 가상환경 및 의존성 설치
# -------------------------------------------------------
echo "📦 Python 의존성을 설치합니다..."
uv sync

# -------------------------------------------------------
# 3. dbt 설정
# -------------------------------------------------------
if [ ! -f profiles.yml ]; then
    echo "📋 profiles.yml.example을 profiles.yml로 복사합니다."
    echo "   GCP_PROJECT_ID를 실제 프로젝트 ID로 교체해주세요."
    cp profiles.yml.example profiles.yml
fi

# -------------------------------------------------------
# 4. Claude Code CLI 확인
# -------------------------------------------------------
if ! command -v claude &> /dev/null; then
    echo "📦 Claude Code CLI를 설치합니다..."
    npm install -g @anthropic-ai/claude-code
else
    echo "✅ Claude Code CLI가 이미 설치되어 있습니다: $(claude --version)"
fi

# -------------------------------------------------------
# 5. marimo 확인
# -------------------------------------------------------
echo "📦 marimo 설치 확인..."
uv run marimo --version

echo ""
echo "✅ 설정 완료!"
echo ""
echo "다음 단계:"
echo "  1. profiles.yml에서 GCP_PROJECT_ID를 실제 프로젝트 ID로 교체"
echo "  2. GCP 서비스 계정 키 설정 (instructor-setup-guide.md 참조)"
echo "  3. dbt debug로 BigQuery 연결 확인"
echo "     uv run dbt debug"
```

### 4.4 pyproject.toml 예시

```toml
[project]
name = "fittrack-analysis"
version = "0.1.0"
description = "FitTrack B2C 모바일 앱 DAU/MAU 분석 — 하니스 엔지니어링 실습 프로젝트"
requires-python = ">=3.11"
dependencies = [
    "dbt-core>=1.8",
    "dbt-bigquery>=1.8",
    "marimo>=0.9",
    "numpy>=1.26",
    "pandas>=2.1",
    "altair>=5.0",
    "google-cloud-bigquery>=3.20",
    "pandas-gbq>=0.23",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### 4.5 profiles.yml.example

학습자는 이 파일을 `~/.dbt/profiles.yml`로 복사한 뒤 실제 값으로 수정합니다.
로컬(dev)과 GitHub Actions CI(ci) 두 가지 타깃이 포함됩니다.

```yaml
# profiles.yml.example
# BigQuery on-demand 연결 설정
# 사용법:
#   cp profiles.yml.example ~/.dbt/profiles.yml
#   profiles.yml에서 환경 변수 설정 (BQ_PROJECT_ID, GOOGLE_APPLICATION_CREDENTIALS)
#
# ⚠️ profiles.yml은 절대 Git에 커밋하지 마세요. (.gitignore에 등록되어 있음)

fittrack_analysis:
  target: dev  # 기본 실행 환경

  outputs:
    # ============================================================
    # 로컬 개발 환경 (서비스 계정 키 파일 사용)
    # ============================================================
    dev:
      type: bigquery
      method: service-account

      # GCP 프로젝트 ID — 환경 변수로 관리
      # export BQ_PROJECT_ID="your-gcp-project-id"
      project: "{{ env_var('BQ_PROJECT_ID') }}"

      # dbt 모델 결과가 저장될 BigQuery 데이터셋
      dataset: dbt_dev

      # 서비스 계정 키 파일 경로
      # export GOOGLE_APPLICATION_CREDENTIALS="./gcp-sa-key.json"
      keyfile: "{{ env_var('GOOGLE_APPLICATION_CREDENTIALS') }}"

      location: US        # BigQuery 데이터 위치 (무료 쿼리 1TB/월 적용)
      timeout_seconds: 300
      threads: 4          # 동시 실행 모델 수 (on-demand는 4 이하 권장)
      retries: 3

      # 비용 제어: 단일 쿼리 최대 스캔 바이트 (1GB)
      # 초과 시 쿼리 실패 → 의도치 않은 대용량 스캔 방지
      maximum_bytes_billed: 1073741824  # 1GB

    # ============================================================
    # GitHub Actions CI 환경 (서비스 계정 JSON을 Secret으로 주입)
    # ============================================================
    ci:
      type: bigquery
      method: service-account-json

      project: "{{ env_var('BQ_PROJECT_ID') }}"
      dataset: dbt_ci      # CI 전용 데이터셋 (2.3절에서 생성)
      location: US
      timeout_seconds: 300
      threads: 2           # CI는 병렬도 낮게 설정 (비용 절감)
      retries: 1

      # GitHub Secret GCP_SA_KEY의 JSON 내용을 환경 변수로 주입
      # 워크플로에서: echo "${{ secrets.GCP_SA_KEY }}" > /tmp/sa.json 후 참조
      keyfile_json: "{{ env_var('GCP_SA_KEY_JSON') }}"

      maximum_bytes_billed: 1073741824  # 1GB
```

> **학습자 안내**: `profiles.yml`은 로컬 개발 전용이며, CI는 GitHub Actions 워크플로 내에서 환경 변수로 자동 주입됩니다. `profiles.yml`을 Git에 커밋하면 GCP 프로젝트 ID가 노출되므로 `.gitignore`에 등록되어 있습니다.

### 4.6 .gitignore

```gitignore
# 환경 및 의존성
.venv/
__pycache__/
*.pyc

# dbt
target/
dbt_packages/
logs/

# GCP 인증 — 절대 커밋 금지!
gcp-sa-key.json
*-sa-key.json
*.credentials.json

# dbt 프로필 (로컬 설정 포함)
profiles.yml

# marimo 내보내기 산출물
*.html
*.pdf

# Claude Code 로컬 설정
.claude/settings.local.json

# OS
.DS_Store
Thumbs.db

# 합성 데이터 출력
output/
```

### 4.7 marimo 노트북 템플릿 준비

스타터 레포에는 학습자가 모듈 2와 3에서 작성할 노트북의 **시작 골격(skeleton)** 파일을 포함합니다.
참조 구현(`examples/`)과 달리 분석 로직은 채워져 있지 않으며, 학습자가 직접 채워야 할 TODO 섹션만 있습니다.

#### 4.7.1 디렉토리 구조

스타터 레포에 `notebooks/` 디렉토리를 만들고 두 개의 템플릿을 추가합니다.

```
fittrack-analysis/
└── notebooks/
    ├── README.md                        # 노트북 사용 방법 안내
    ├── explore_template.py              # 데이터 탐색 템플릿 (모듈 2용)
    └── analysis_template.py            # DAU/MAU 분석 리포트 템플릿 (모듈 3용)
```

#### 4.7.2 `notebooks/README.md` 작성

다음 내용으로 `notebooks/README.md` 파일을 생성합니다:

**파일 구성**

| 파일 | 용도 | 해당 모듈 |
|------|------|-----------|
| `explore_template.py` | 데이터 탐색 및 품질 점검 | 모듈 2 |
| `analysis_template.py` | DAU/MAU 분석 리포트 | 모듈 2, 3 |

**marimo 노트북 실행 방법:**

```bash
# 편집 모드 (셀 추가/수정 가능)
uv run marimo edit notebooks/explore_template.py

# 실행 모드 (결과만 확인)
uv run marimo run notebooks/analysis_template.py
```

**HTML/PDF 내보내기:**

```bash
# HTML 리포트 내보내기
uv run marimo export html notebooks/analysis_template.py -o reports/dau-mau-report.html

# PDF 내보내기
uv run marimo export pdf notebooks/analysis_template.py -o reports/dau-mau-report.pdf
```

> **참고**: 에이전트는 `/analyze` 스킬 실행 시 이 파일을 기반으로 분석 노트북을 생성합니다.
> `AGENTS.md`에 이 경로를 명시해야 에이전트가 올바른 파일을 찾을 수 있습니다.

#### 4.7.3 `notebooks/explore_template.py` 작성

```python
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
FitTrack 데이터 탐색 노트북 — 학습자 템플릿

dbt 모델 실행 후 데이터 품질과 기본 분포를 확인하는 탐색적 분석 노트북입니다.
모듈 2에서 /analyze 스킬의 기반 노트북으로 활용합니다.

사용법:
  uv run marimo edit notebooks/explore_template.py
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

        **분석 목적**: dbt 모델 실행 결과의 데이터 품질을 점검하고 분포를 파악합니다.

        **점검 항목**:
        1. 원본 테이블 행 수 및 기간 확인
        2. 플랫폼별 사용자 분포
        3. 일별 이벤트 수 분포
        4. dbt mart 모델 출력 검증
        """
    )
    return (mo,)


@app.cell
def setup():
    # BigQuery 클라이언트 초기화
    # 환경 변수 GOOGLE_APPLICATION_CREDENTIALS 또는 BQ_PROJECT_ID 사용
    import os
    import pandas as pd
    from google.cloud import bigquery

    # TODO: GCP_PROJECT_ID를 환경 변수에서 읽거나 직접 입력
    project_id = os.getenv("BQ_PROJECT_ID", "YOUR_PROJECT_ID")
    client = bigquery.Client(project=project_id)

    return client, os, pd, project_id


@app.cell
def check_raw_tables(client, project_id):
    # TODO: raw 데이터셋의 테이블 행 수와 날짜 범위를 확인하는 쿼리를 작성하세요
    # 힌트: INFORMATION_SCHEMA.TABLES 또는 COUNT(*) 쿼리를 활용합니다
    import marimo as mo

    mo.md("### TODO: raw 테이블 행 수 확인 쿼리 작성")
    return


@app.cell
def check_platform_distribution(client, project_id):
    # TODO: 플랫폼별(iOS/Android) 사용자 분포를 확인하는 쿼리를 작성하세요
    import marimo as mo

    mo.md("### TODO: 플랫폼별 사용자 분포 쿼리 작성")
    return


@app.cell
def check_dbt_marts(client, project_id):
    # TODO: analytics 데이터셋의 mart 테이블에서 DAU/MAU 집계 결과를 확인하세요
    import marimo as mo

    mo.md("### TODO: dbt mart 모델 출력 검증 쿼리 작성")
    return


if __name__ == "__main__":
    app.run()
```

#### 4.7.4 `notebooks/analysis_template.py` 작성

```python
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
FitTrack DAU/MAU 분석 리포트 — 학습자 템플릿

이슈 기반 7단계 워크플로의 stage:6-analyze 단계에서
에이전트가 이 파일을 기반으로 분석 노트북을 작성합니다.

사용법:
  uv run marimo edit notebooks/analysis_template.py

HTML 내보내기:
  uv run marimo export html notebooks/analysis_template.py \\
    -o reports/dau-mau-report.html
"""

import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium")


@app.cell
def title():
    import marimo as mo

    # TODO: 이슈 제목과 분석 기간을 반영하여 제목을 업데이트하세요
    mo.md(
        """
        # 📊 FitTrack 앱 DAU/MAU 분석 리포트

        **분석 기간**: TODO
        **분석 대상**: FitTrack 모바일 앱 사용자
        **분석 요청 이슈**: TODO (GitHub Issues 링크)

        ---

        ## 분석 개요

        TODO: 이슈에서 정의한 분석 질문과 목적을 여기에 요약하세요.

        ### 메트릭 정의
        - **DAU**: 해당 일자에 1회 이상 이벤트를 발생시킨 고유 사용자 수
        - **MAU**: 해당 월에 1회 이상 이벤트를 발생시킨 고유 사용자 수
        - **Stickiness**: DAU / MAU × 100 (%)
        """
    )
    return (mo,)


@app.cell
def setup():
    import os
    import pandas as pd
    import plotly.express as px
    from google.cloud import bigquery

    # BigQuery 프로젝트 ID (환경 변수에서 읽기)
    project_id = os.getenv("BQ_PROJECT_ID", "YOUR_PROJECT_ID")
    client = bigquery.Client(project=project_id)

    return client, os, pd, project_id, px


@app.cell
def load_dau_data(client, project_id):
    # TODO: fct_daily_active_users 테이블에서 DAU 데이터를 불러오는 쿼리를 작성하세요
    # 힌트: analytics.fct_daily_active_users 테이블 활용
    import marimo as mo

    mo.md("### TODO: DAU 데이터 로드 쿼리 작성")
    return


@app.cell
def load_mau_data(client, project_id):
    # TODO: fct_monthly_active_users 테이블에서 MAU 데이터를 불러오는 쿼리를 작성하세요
    import marimo as mo

    mo.md("### TODO: MAU 데이터 로드 쿼리 작성")
    return


@app.cell
def visualize_dau_trend(pd, px):
    # TODO: DAU 트렌드 시각화를 작성하세요 (plotly 권장)
    import marimo as mo

    mo.md("### TODO: DAU 트렌드 시각화")
    return


@app.cell
def calculate_stickiness(pd):
    # TODO: Stickiness(DAU/MAU) 계산 및 플랫폼별 비교를 작성하세요
    import marimo as mo

    mo.md("### TODO: Stickiness 계산 및 시각화")
    return


@app.cell
def summary():
    import marimo as mo

    mo.md(
        """
        ## 분석 요약 및 인사이트

        TODO: 분석 결과에서 도출한 핵심 인사이트를 3~5개 항목으로 정리하세요.

        1. **DAU 트렌드**: TODO
        2. **MAU 트렌드**: TODO
        3. **Stickiness**: TODO
        4. **플랫폼별 차이**: TODO
        5. **권장 액션**: TODO
        """
    )
    return


if __name__ == "__main__":
    app.run()
```

#### 4.7.5 노트북 디렉토리 생성 및 파일 복사

```bash
# 스타터 레포 루트에서 실행
mkdir -p notebooks reports

# 템플릿 파일 생성 (위의 내용을 직접 작성하거나 코스 리소스에서 복사)
# 참조 구현은 examples/ 디렉토리에 있음:
#   examples/marimo-data-exploration.py → notebooks/explore_template.py의 참고
#   examples/marimo-dau-mau-analysis.py → notebooks/analysis_template.py의 참고

# reports/ 디렉토리는 .gitignore에 포함 (자동 생성 아티팩트)
echo "reports/" >> .gitignore

# 노트북 동작 확인 (프로젝트 ID 설정 후)
export BQ_PROJECT_ID="$GCP_PROJECT_ID"
uv run marimo run notebooks/explore_template.py
```

> **강사 참고**: `examples/` 디렉토리의 완성된 노트북은 학습자에게 공개하지 않는 것을 권장합니다.
> 모듈 2~3 완료 후 참조용으로 제공하거나, `examples/` 디렉토리를 스타터 레포에서 제외하세요.

---

### 4.8 학습자 배포 절차

스타터 레포를 완성한 후 학습자에게 배포하는 두 가지 방법 중 하나를 선택합니다.

#### 방법 A: GitHub Template Repository (권장)

학습자가 버튼 하나로 개인 레포를 생성할 수 있어 가장 간편합니다.

**강사 설정 단계:**

```bash
# 1. 스타터 레포를 Template Repository로 지정
gh repo edit fittrack-analysis-starter --template

# 2. 또는 웹 UI에서 설정:
#    GitHub 레포 → Settings → General
#    → "Template repository" 체크박스 활성화
```

**학습자 안내 메시지 (이메일/슬랙 등):**

```
안녕하세요!

하니스 엔지니어링 for 데이터 분석 코스에 오신 것을 환영합니다.

[1단계] 스타터 레포 생성
아래 링크에서 "Use this template" → "Create a new repository"를 클릭하세요:
https://github.com/<강사-계정>/fittrack-analysis-starter

  - Repository name: fittrack-analysis (권장)
  - Visibility: Private (권장)

[2단계] 로컬 클론 및 환경 설정
git clone https://github.com/<본인-계정>/fittrack-analysis
cd fittrack-analysis
chmod +x setup.sh
./setup.sh

[3단계] BigQuery 연결 설정
profiles.yml을 열어 <YOUR_GCP_PROJECT_ID>를 아래 값으로 교체하세요:
  GCP_PROJECT_ID: <강사가 제공한 값 또는 개인 GCP 프로젝트 ID>

[4단계] GCP 서비스 계정 키 배치
강사에게서 받은 gcp-sa-key.json 파일을 레포 루트에 복사하세요.
(이 파일은 .gitignore에 등록되어 있어 Git에 커밋되지 않습니다)

[5단계] dbt 연결 확인
export GOOGLE_APPLICATION_CREDENTIALS="./gcp-sa-key.json"
export BQ_PROJECT_ID="<YOUR_GCP_PROJECT_ID>"
uv run dbt debug
# → "All checks passed!" 가 출력되면 설정 완료

[6단계] GitHub Secrets 등록
GitHub Actions 워크플로 실행을 위해 레포의 Secrets를 등록하세요.
(instructor-setup-guide.md 섹션 5.1 참조)

준비가 완료되면 모듈 0부터 시작하세요!
```

**진행 확인 방법:**

```bash
# 학습자가 스타터 레포를 올바르게 포크했는지 확인
# (GitHub Organization 사용 시)
gh repo list <organization> --source --json name,createdAt \
  --jq '.[] | select(.name | startswith("fittrack-analysis"))'
```

#### 방법 B: Fork (개인 실습 / 소규모)

조직 계정 없이 개인 GitHub 계정으로 운영할 때 사용합니다.

```bash
# 학습자별 절차:
# 1. 강사 레포 페이지에서 "Fork" 클릭
# 2. 본인 계정으로 포크 생성
# 3. 포크된 레포를 로컬 클론

git clone https://github.com/<본인-계정>/fittrack-analysis-starter
cd fittrack-analysis-starter
./setup.sh
```

> **주의**: Fork 방식은 강사 레포의 변경 사항이 학습자 레포에 자동 전파되지 않습니다.
> 중간에 버그를 수정해야 할 경우 Template Repository 방식이 관리가 더 용이합니다.

#### 4.8.1 BigQuery 자격 증명 배포 옵션

학습자에게 BigQuery에 접근하는 방법은 세 가지입니다:

| 옵션 | 설명 | 권장 시나리오 |
|------|------|---------------|
| **A. 강사 GCP 프로젝트 공유** | 강사가 하나의 GCP 프로젝트를 만들고, 학습자별 서비스 계정을 발급 | 소규모 강의 (5인 이하), 비용 중앙 관리 |
| **B. 학습자 개인 GCP 프로젝트** | 학습자 각자가 GCP 계정을 생성하고 섹션 2의 설정을 직접 수행 | 대규모 강의, 자기 학습 |
| **C. 혼합: 공용 데이터 + 개인 환경** | 강사가 읽기 전용 공용 BigQuery 데이터셋을 공유하고, 학습자는 개인 프로젝트에서 쿼리 | 비용 예측이 어려운 경우 |

**옵션 A 설정 (강사 GCP 프로젝트 공유):**

```bash
# 학습자별 서비스 계정 생성 (예: 학습자 3명)
for student in student01 student02 student03; do
  # 서비스 계정 생성
  gcloud iam service-accounts create "${student}-sa" \
    --display-name "${student} FitTrack SA" \
    --project "$GCP_PROJECT_ID"

  SA_EMAIL="${student}-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

  # 권한 부여 (읽기 + 쿼리 실행만, 테이블 생성 없음)
  gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/bigquery.dataViewer"

  gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/bigquery.jobUser"

  # dbt가 analytics 데이터셋에 쓸 수 있도록 별도 권한 부여
  bq add-iam-policy-binding \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/bigquery.dataEditor" \
    "${GCP_PROJECT_ID}:analytics"

  # 키 생성
  gcloud iam service-accounts keys create "./keys/${student}-sa-key.json" \
    --iam-account="$SA_EMAIL"

  echo "✅ ${student} 서비스 계정 키 생성 완료: ./keys/${student}-sa-key.json"
done
```

**학습자에게 전달할 파일:**
- `gcp-sa-key.json` (각자에 맞는 키 파일)
- `GCP_PROJECT_ID` 값 (강사 프로젝트 ID)

#### 4.8.2 GitHub Secrets 학습자 셀프 등록 가이드

학습자가 본인 레포에 Secrets를 등록하는 단계별 안내:

```bash
# 학습자 레포 루트에서 실행
# (gh auth login이 완료된 상태여야 합니다)

# 1. GCP 서비스 계정 키 등록
gh secret set GCP_SA_KEY < ./gcp-sa-key.json

# 2. BigQuery 프로젝트 ID 등록 (반드시 BQ_PROJECT_ID로 등록)
#    - 강사 프로젝트 공유(옵션 A): 강사에게 받은 ID 사용
#    - 개인 프로젝트(옵션 B): 본인의 GCP 프로젝트 ID
gh secret set BQ_PROJECT_ID --body "your-gcp-project-id"

# 3. Claude Code 토큰 등록
#    로컬에서 claude setup-token 실행 후 출력된 토큰 사용
claude setup-token
gh secret set CLAUDE_CODE_TOKEN --body "claude-token-here"

# 4. GitHub PAT 등록
#    https://github.com/settings/tokens 에서 Fine-grained PAT 생성
#    (필요 권한: Contents, Pull Requests, Issues - Read/Write)
gh secret set GITHUB_PAT --body "ghp_xxxx..."

# 등록 확인
gh secret list
```

#### 4.8.3 배포 후 학습자 온보딩 확인 체크리스트

```bash
# 강사가 학습자 레포 상태를 일괄 확인하는 스크립트 (옵션)
#!/usr/bin/env bash
# check-student-setup.sh

STUDENTS=("student01" "student02" "student03")  # 학습자 GitHub 계정 목록
REPO_NAME="fittrack-analysis"

for student in "${STUDENTS[@]}"; do
  echo "=== ${student} ==="

  # 레포 존재 확인
  if gh repo view "${student}/${REPO_NAME}" &>/dev/null; then
    echo "  ✅ 레포 생성됨"
  else
    echo "  ❌ 레포 없음 — 스타터 레포 생성 필요"
    continue
  fi

  # Secrets 등록 확인 (이름만 확인, 값은 비공개)
  secrets=$(gh secret list --repo "${student}/${REPO_NAME}" --json name --jq '.[].name' 2>/dev/null)
  for secret in GCP_SA_KEY BQ_PROJECT_ID ANTHROPIC_API_KEY CLAUDE_CODE_TOKEN GITHUB_PAT; do
    if echo "$secrets" | grep -q "^${secret}$"; then
      echo "  ✅ Secret ${secret} 등록됨"
    else
      echo "  ❌ Secret ${secret} 미등록"
    fi
  done

  echo ""
done
```

> **강사 권한 요건**: 위 확인 스크립트는 학습자 레포에 대한 Collaborator 이상의 접근 권한이 필요합니다.
> GitHub Organization을 사용하는 경우 Organization Admin 권한으로 확인할 수 있습니다.

---

### 4.9 학습자 필수 도구 사전 설치 가이드

> 이 섹션은 **학습자 배포 자료**로도 활용할 수 있습니다. 코스 시작 전 학습자에게 공유하여
> 환경 설정을 미리 완료하도록 안내하세요.

모듈 0을 시작하기 전에 아래 도구가 모두 설치되어 있어야 합니다.

#### 4.9.1 필수 도구 체크리스트

| 도구 | 최소 버전 | 용도 | 설치 확인 명령 |
|------|-----------|------|----------------|
| **macOS/Linux 터미널** | — | CLI 명령 실행 | 기본 설치됨 |
| **Git** | 2.30+ | 버전 관리, 레포 클론 | `git --version` |
| **Node.js** | 18+ | Claude Code CLI 실행 환경 | `node --version` |
| **Python** | 3.11+ | uv가 자동 관리 (직접 설치 불필요) | `python3 --version` |
| **uv** | 0.4+ | Python 가상환경·패키지 관리 | `uv --version` |
| **Claude Code CLI** | 최신 | AI 에이전트 실행 | `claude --version` |
| **gcloud CLI** | 최신 | GCP 인증·BigQuery 접근 | `gcloud --version` |
| **GitHub CLI (`gh`)** | 2.40+ | 레포 생성, Secrets 등록, PR 작업 | `gh --version` |

> **Windows 사용자**: WSL2(Ubuntu 22.04 이상)를 통해 Linux 환경을 사용하는 것을 강력히 권장합니다.
> WSL2 설치 방법: `wsl --install` (PowerShell 관리자 모드)

---

#### 4.9.2 도구별 설치 방법

##### Git

Git은 대부분의 macOS/Linux에 기본 설치되어 있습니다.

```bash
# macOS — Xcode Command Line Tools 포함
git --version
# → 없으면 자동으로 설치 안내 팝업이 뜸

# macOS — Homebrew 사용 (최신 버전 권장)
brew install git

# Ubuntu/Debian
sudo apt-get update && sudo apt-get install git -y
```

##### Node.js

Claude Code CLI는 Node.js 런타임이 필요합니다.

```bash
# macOS — Homebrew
brew install node@20  # LTS 버전 권장

# macOS/Linux — nvm (Node Version Manager, 여러 버전 관리 가능)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
exec $SHELL  # 셸 재시작
nvm install 20
nvm use 20

# Ubuntu/Debian — NodeSource 공식 저장소
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# 설치 확인
node --version   # v20.x.x 이상
npm --version    # 10.x.x 이상
```

##### uv (Python 패키지 관리자)

이 코스는 pip/conda 대신 **uv**를 사용합니다. uv는 Python 가상환경 생성과 패키지 설치를 단일 명령으로 처리하며 속도가 빠릅니다.

```bash
# macOS/Linux — 공식 설치 스크립트 (권장)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 셸 재시작 또는 PATH 갱신
export PATH="$HOME/.local/bin:$PATH"
# 또는: source ~/.bashrc (bash) / source ~/.zshrc (zsh)

# macOS — Homebrew
brew install uv

# 설치 확인
uv --version   # 0.4.x 이상
```

> **uv가 처음이라면**: `uv sync`는 `pyproject.toml`을 읽어 의존성을 설치합니다.
> `uv run <명령>`은 가상환경 내에서 명령을 실행합니다 (`source .venv/bin/activate` 없이도 동작).

##### Claude Code CLI

Claude Code는 **Claude Pro 또는 Max 구독**이 필요합니다.
구독이 없으면 CLI를 설치해도 사용할 수 없습니다.

```bash
# npm으로 전역 설치 (Node.js 설치 후)
npm install -g @anthropic-ai/claude-code

# 설치 확인
claude --version

# 최초 인증 (브라우저가 열림 — Anthropic 계정으로 로그인)
claude
```

> **구독 확인**: [https://claude.ai/settings](https://claude.ai/settings) → Billing 탭에서 Pro/Max 구독 상태 확인

##### gcloud CLI (Google Cloud SDK)

BigQuery 인증 및 `bq` CLI 명령 실행에 필요합니다.

```bash
# macOS — Homebrew (권장)
brew install --cask google-cloud-sdk

# macOS/Linux — 공식 설치 스크립트
curl https://sdk.cloud.google.com | bash
exec -l $SHELL  # 셸 재시작

# 설치 확인
gcloud --version

# GCP 계정 인증
gcloud auth login                        # 브라우저에서 Google 계정 로그인
gcloud auth application-default login    # 로컬 개발 도구용 ADC 설정
gcloud config set project <YOUR_GCP_PROJECT_ID>
```

> **Ubuntu/Debian**: [공식 문서](https://cloud.google.com/sdk/docs/install#deb)의 APT 저장소 설치 방법 사용

##### GitHub CLI (`gh`)

레포 생성, Secrets 등록, PR 생성, 라벨 관리에 사용합니다.

```bash
# macOS — Homebrew
brew install gh

# Ubuntu/Debian
(type -p wget >/dev/null || (sudo apt update && sudo apt-get install wget -y)) \
  && sudo mkdir -p -m 755 /etc/apt/keyrings \
  && wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg \
     | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
  && sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
  && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
     | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
  && sudo apt update && sudo apt install gh -y

# 설치 확인
gh --version

# GitHub 인증 (브라우저 또는 PAT 사용)
gh auth login
# → GitHub.com 선택 → HTTPS 선택 → 브라우저로 인증
```

---

#### 4.9.3 일괄 환경 확인 스크립트

모든 도구가 올바르게 설치되었는지 한 번에 확인하는 스크립트입니다.
학습자에게 이 스크립트를 제공하여 코스 시작 전 환경을 검증하도록 안내하세요.

```bash
#!/usr/bin/env bash
# check-prereqs.sh — 코스 사전 요구사항 확인 스크립트
#
# 사용법:
#   chmod +x check-prereqs.sh
#   ./check-prereqs.sh

set -euo pipefail

PASS=0
FAIL=0

# 컬러 출력 설정
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'  # No Color

check() {
    local name="$1"
    local cmd="$2"
    local min_ver="${3:-}"

    if eval "$cmd" &>/dev/null; then
        local ver
        ver=$(eval "$cmd" 2>&1 | head -1)
        echo -e "${GREEN}✅ ${name}${NC}: ${ver}"
        ((PASS++))
    else
        echo -e "${RED}❌ ${name}${NC}: 설치되지 않음"
        if [ -n "$min_ver" ]; then
            echo -e "   ${YELLOW}→ 최소 버전: ${min_ver}${NC}"
        fi
        ((FAIL++))
    fi
}

echo "🔍 코스 사전 요구사항 확인 중..."
echo "========================================"

# 필수 도구 확인
check "Git"          "git --version"         "2.30+"
check "Node.js"      "node --version"        "18+"
check "npm"          "npm --version"         "9+"
check "uv"           "uv --version"          "0.4+"
check "Claude Code"  "claude --version"      "최신"
check "gcloud"       "gcloud --version"      "최신"
check "gh (GitHub)"  "gh --version"          "2.40+"

echo "========================================"

# Python 확인 (uv가 관리하므로 참고용)
if command -v python3 &>/dev/null; then
    py_ver=$(python3 --version 2>&1)
    echo -e "${GREEN}ℹ️  Python${NC}: ${py_ver} (uv가 자동 관리 — 직접 설치 불필요)"
fi

echo ""

# 결과 요약
if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}🎉 모든 도구가 설치되어 있습니다! (${PASS}개)${NC}"
    echo "   이제 setup.sh를 실행하여 프로젝트 환경을 구성하세요."
else
    echo -e "${RED}⚠️  ${FAIL}개 도구가 누락되었습니다.${NC} (성공: ${PASS}개)"
    echo "   누락된 도구를 설치한 후 다시 실행하세요."
    echo "   → 설치 방법: instructor-setup-guide.md 섹션 4.9.2 참조"
    exit 1
fi
```

이 스크립트를 스타터 레포에 포함하거나, 학습자에게 별도로 공유할 수 있습니다.

---

#### 4.9.4 GCP 계정 및 Claude 구독 사전 준비 안내

도구 설치와 별개로, 다음 계정/구독이 코스 시작 전에 준비되어 있어야 합니다.

| 항목 | 준비 방법 | 비용 |
|------|-----------|------|
| **GitHub 계정** | [github.com](https://github.com) 가입 | 무료 |
| **GCP 계정 + 결제 설정** | [console.cloud.google.com](https://console.cloud.google.com) → 무료 체험 시작 | $300 크레딧 제공 (신규 계정) |
| **Claude Pro/Max 구독** | [claude.ai/settings](https://claude.ai/settings) → Billing | Pro: 월 $20 / Max: 월 $100 |
| **Anthropic API 키** | [console.anthropic.com](https://console.anthropic.com) → API Keys | 사용량 기반 과금 |

> **비용 안내**:
> - BigQuery: 합성 데이터(~500MB) 저장 + 코스 실습 쿼리는 GCP $300 크레딧으로 충분합니다.
>   코스 전체를 완료해도 크레딧의 1~5% 이내로 예상됩니다.
> - Claude API: GitHub Actions 워크플로에서 Claude Agent SDK가 사용합니다.
>   모듈 3 실습에서 분석 1회당 약 $0.01~$0.05 수준입니다.

---

## 5. GitHub 설정

### 5.1 GitHub Secrets 등록

학습자 레포(또는 포크)에 다음 Secrets를 등록합니다.

#### 필수 Secrets

| Secret 이름 | 값 | 용도 |
|-------------|---|------|
| `GCP_SA_KEY` | 서비스 계정 JSON 키 내용 전체 | BigQuery 인증 (dbt 빌드, 데이터 적재, GitHub Actions) |
| `BQ_PROJECT_ID` | GCP 프로젝트 ID (예: `fittrack-analysis-course`) | dbt 프로필(`BQ_PROJECT_ID` 환경 변수)·bq CLI 프로젝트 지정 |
| `ANTHROPIC_API_KEY` | Anthropic API 키 | GitHub Actions에서 Claude Agent SDK 실행 |
| `CLAUDE_CODE_TOKEN` | Claude Code 인증 토큰 | GitHub Actions에서 Claude Code CLI 실행 |

> **⚠️ 주의**: 프로젝트 ID Secret 이름은 반드시 `BQ_PROJECT_ID`를 사용하세요.
> `dbt-ci.yml`과 `auto-analyze.yml` 워크플로 모두 `secrets.BQ_PROJECT_ID`를 참조합니다.
> `GCP_PROJECT_ID`로 등록하면 워크플로가 실패합니다.

#### GitHub 인증 Secrets (택 1)

**방법 A: Personal Access Token (PAT)**

| Secret 이름 | 값 | 용도 |
|-------------|---|------|
| `GITHUB_PAT` | `ghp_xxxx...` (Fine-grained PAT) | Actions 내 Git 작업 (브랜치, PR 생성) |

```bash
# PAT 생성 시 필요한 권한:
# - Repository: Contents (Read and Write)
# - Repository: Pull Requests (Read and Write)
# - Repository: Issues (Read and Write)
# - Repository: Metadata (Read)
```

**방법 B: GitHub App**

| Secret 이름 | 값 | 용도 |
|-------------|---|------|
| `APP_ID` | GitHub App ID | App 인증 |
| `APP_PRIVATE_KEY` | GitHub App 비밀 키 (PEM) | App 인증 |

> **권장**: 개인 학습 시에는 PAT(방법 A)이 설정이 간단합니다. 조직/팀 단위로 운영할 경우 GitHub App(방법 B)을 권장합니다.

#### Secret 등록 방법 (CLI)

```bash
# GCP 서비스 계정 키 등록 (JSON 파일 내용 전체를 Secret 값으로 사용)
gh secret set GCP_SA_KEY < ./gcp-sa-key.json

# BigQuery 프로젝트 ID 등록 (워크플로에서 BQ_PROJECT_ID로 참조)
gh secret set BQ_PROJECT_ID --body "$GCP_PROJECT_ID"

# Anthropic API 키 등록
gh secret set ANTHROPIC_API_KEY --body "<YOUR_ANTHROPIC_API_KEY>"

# Claude Code 토큰 등록
# (로컬에서 claude setup-token으로 생성한 토큰)
gh secret set CLAUDE_CODE_TOKEN --body "<YOUR_CLAUDE_CODE_TOKEN>"

# GitHub PAT 등록 (방법 A 선택 시)
gh secret set GITHUB_PAT --body "ghp_xxxx..."

# 등록된 Secrets 확인 (값은 표시되지 않음)
gh secret list
```

#### Secret 등록 방법 (웹 UI)

1. GitHub 레포 → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret** 클릭
3. Name과 Value를 입력하고 **Add secret** 클릭

### 5.2 Claude Code 인증 토큰 생성

GitHub Actions에서 Claude Agent SDK를 실행하려면 비대화형 인증이 필요합니다.

```bash
# 로컬에서 토큰 생성
claude setup-token

# 출력된 토큰을 CLAUDE_CODE_TOKEN Secret으로 등록
```

> **상세 절차**: `examples/claude-agent-sdk-setup-guide.md`의 "3. `claude setup-token` 인증 흐름" 섹션을 참조하세요.

### 5.3 GitHub Actions 권한 설정

레포의 GitHub Actions 워크플로에 충분한 권한을 부여합니다.

1. GitHub 레포 → **Settings** → **Actions** → **General**
2. **Workflow permissions** 섹션에서:
   - ✅ **Read and write permissions** 선택
   - ✅ **Allow GitHub Actions to create and approve pull requests** 체크

### 5.4 GitHub Issue 라벨 사전 등록 (선택)

> **참고**: 라벨 등록은 모듈 3에서 학습자가 직접 수행합니다. 강사가 사전에 등록하려면 아래 스크립트를 사용하세요.

```bash
# 라벨 일괄 등록 스크립트 실행
bash examples/github-actions/label-setup.sh <owner>/<repo>

# 등록 확인
gh label list --repo <owner>/<repo>
```

등록되는 라벨 (총 11개):

| 라벨 | 색상 | 용도 |
|------|------|------|
| `auto-analyze` | 🟢 녹색 | 워크플로 진입 트리거 |
| `stage:1-problem` ~ `stage:7-pr` | 🔵 파란색 | 각 단계 진행 표시 |
| `done` | 🟢 녹색 | 분석 완료 |
| `status:error` | 🔴 빨간색 | 에러 발생 |
| `status:retry` | 🟡 노란색 | 재시도 대기 |

---

## 6. dbt 프로젝트 검증

스타터 레포의 dbt 모델이 BigQuery에 정상적으로 실행되는지 검증합니다.

### 6.1 BigQuery 연결 확인

```bash
cd fittrack-analysis-starter

# profiles.yml 설정
cp profiles.yml.example profiles.yml
# <YOUR_GCP_PROJECT_ID>를 실제 프로젝트 ID로 교체

# 환경 변수 설정 (서비스 계정 키 경로)
export GOOGLE_APPLICATION_CREDENTIALS="./gcp-sa-key.json"
export BQ_PROJECT_ID="$GCP_PROJECT_ID"

# 연결 확인
uv run dbt debug
```

예상 출력의 마지막 줄:

```
All checks passed!
```

### 6.2 dbt 모델 실행

```bash
# 전체 모델 실행
uv run dbt run

# 예상 출력:
# Completed successfully
#
# Done. PASS=6 WARN=0 ERROR=0 SKIP=0 TOTAL=6
```

실행되는 모델 6개:
1. `stg_events` — 이벤트 스테이징
2. `stg_users` — 사용자 스테이징
3. `stg_sessions` — 세션 스테이징
4. `fct_daily_active_users` — DAU 집계
5. `fct_monthly_active_users` — MAU 집계
6. `fct_retention_cohort` — 리텐션 코호트

### 6.3 dbt 테스트 실행

```bash
# 데이터 테스트 실행
uv run dbt test

# 예상 출력:
# Completed successfully
#
# Done. PASS=N WARN=0 ERROR=0 SKIP=0 TOTAL=N
```

주요 테스트 항목:
- `unique` / `not_null`: 기본 키 무결성
- `accepted_values`: 이벤트 유형, 플랫폼 등 허용값 검증
- `relationships`: 외래 키 참조 무결성 (events → users, sessions → users)

### 6.4 결과 데이터 확인

```bash
# DAU 결과 확인
bq query --use_legacy_sql=false "
SELECT *
FROM \`${GCP_PROJECT_ID}.analytics.fct_daily_active_users\`
ORDER BY activity_date DESC
LIMIT 10
"

# MAU 결과 확인
bq query --use_legacy_sql=false "
SELECT *
FROM \`${GCP_PROJECT_ID}.analytics.fct_monthly_active_users\`
ORDER BY activity_month DESC
LIMIT 6
"
```

---

## 7. 학습자 배포 체크리스트

학습자에게 스타터 레포를 배포하기 전 최종 확인 체크리스트입니다.

### 레포지토리

- [ ] 스타터 레포가 GitHub에 생성되어 있다
  - **검증**: `gh repo view <owner>/<repo>` 실행 시 레포 정보 출력
- [ ] `README.md`에 빠른 시작 가이드가 포함되어 있다
  - **검증**: 레포 메인 페이지에서 setup.sh 실행 절차 확인
- [ ] `.gitignore`에 GCP 키 파일, 프로필, 데이터 출력 디렉토리가 포함되어 있다
  - **검증**: `cat .gitignore | grep "gcp-sa-key"` 결과 확인
- [ ] `setup.sh`가 실행 가능하고 정상 동작한다
  - **검증**: 클린 환경에서 `./setup.sh` 실행 후 `dbt --version`, `marimo --version` 출력 확인

### BigQuery 데이터

- [ ] `raw` 데이터셋에 3개 테이블이 존재한다 (`raw_users`, `raw_sessions`, `raw_events`)
  - **검증**: `bq ls ${GCP_PROJECT_ID}:raw` 실행 시 3개 테이블 출력
- [ ] 행 수가 기대 범위 내에 있다 (users ~10K, sessions ~150K, events ~500K)
  - **검증**: 섹션 3.3의 행 수 확인 쿼리 실행
- [ ] 날짜 범위가 2025-01-01 ~ 2026-03-31이다
  - **검증**: 섹션 3.3의 날짜 범위 확인 쿼리 실행
- [ ] 플랫폼 분포가 iOS ~55%, Android ~45%이다
  - **검증**: 섹션 3.3의 플랫폼 분포 확인 쿼리 실행

### dbt 프로젝트

- [ ] `dbt debug`가 `All checks passed!`를 출력한다
  - **검증**: `uv run dbt debug` 실행
- [ ] `dbt run`이 6개 모델 모두 PASS한다
  - **검증**: `uv run dbt run` 실행 후 `PASS=6 ERROR=0` 확인
- [ ] `dbt test`가 모든 테스트 PASS한다
  - **검증**: `uv run dbt test` 실행 후 `ERROR=0` 확인
- [ ] `analytics` 데이터셋에 mart 테이블이 생성된다
  - **검증**: `bq ls ${GCP_PROJECT_ID}:analytics` 실행 시 3개 테이블 출력

### GCP 접근

- [ ] 서비스 계정이 `bigquery.dataEditor` + `bigquery.jobUser` 역할을 갖고 있다
  - **검증**: `gcloud projects get-iam-policy $GCP_PROJECT_ID --filter="bindings.members:$SA_EMAIL" --flatten="bindings"` 실행
- [ ] 서비스 계정 JSON 키가 유효하다 (만료되지 않았는지 확인)
  - **검증**: `gcloud iam service-accounts keys list --iam-account=$SA_EMAIL` 실행

### GitHub Secrets (학습자 레포에 등록)

- [ ] `GCP_SA_KEY` — 서비스 계정 JSON 키 (전체 JSON 내용)
- [ ] `BQ_PROJECT_ID` — GCP 프로젝트 ID (`GCP_PROJECT_ID`가 아닌 `BQ_PROJECT_ID` 사용)
- [ ] `ANTHROPIC_API_KEY` — Anthropic API 키
- [ ] `CLAUDE_CODE_TOKEN` — Claude Code 인증 토큰
- [ ] `GITHUB_PAT` 또는 `APP_ID` + `APP_PRIVATE_KEY` — GitHub 인증

> **참고**: Secrets 값은 등록 후 확인할 수 없으므로, 등록 직전에 값이 올바른지 반드시 검증하세요.

---

## 8. BigQuery 비용 관리 가이드라인

이 섹션은 **강사 관점**에서 코스 운영 중 발생하는 BigQuery 비용을 체계적으로 관리하는 방법을 다룹니다. 온디맨드(On-Demand) 가격 모델을 기반으로 하며, 학습자가 실습 중 예상치 못한 과금을 방지하는 전략을 포함합니다.

---

### 8.1 BigQuery 요금 구조 및 무료 구간

#### 8.1.1 온디맨드(On-Demand) 요금 모델

이 코스는 **온디맨드 가격 모델**을 사용합니다. 슬롯 예약 없이 실행되며, **처리한 데이터 양에 따라 과금**됩니다.

| 항목 | 요금 | 비고 |
|------|------|------|
| 쿼리 처리 | **$6.25 / TB** | 매월 첫 1TB 무료 |
| 스토리지 (활성) | $0.020 / GB / 월 | 90일 미접근 시 장기 스토리지 요금 |
| 스토리지 (장기) | $0.010 / GB / 월 | 90일 미접근 테이블 자동 적용 |
| 스트리밍 삽입 | $0.010 / 200MB | 이 코스에서는 사용 안 함 |
| 무료 구간 | **1TB 쿼리 / 10GB 스토리지** | 매월 초기화 |

> **참고**: 이 코스의 합성 데이터셋은 약 200~500MB 규모입니다. 학습자 1인이 매월 수행하는 실습 쿼리의 총 처리량은 대부분 **100GB 미만**으로, 무료 구간(1TB) 안에서 해결됩니다.

#### 8.1.2 슬롯 예약 vs 온디맨드 비교

**슬롯 예약(Slot Reservation)** 은 BigQuery의 정액제 모델입니다. 일정 수의 슬롯(처리 단위)을 예약하고, 쿼리 처리량과 무관하게 월정액을 지불합니다.

| 항목 | 온디맨드 | 슬롯 예약 (Standard) |
|------|----------|----------------------|
| 과금 방식 | 처리 TB당 $6.25 | 슬롯 시간당 ~$0.04 (100슬롯 기준 ~$288/월) |
| 무료 구간 | 매월 1TB 무료 | 없음 |
| 적합한 용도 | 소규모 실습, 불규칙적 사용 | 대용량 프로덕션 워크로드 |
| **코스 적합도** | ✅ **권장** | ❌ 교육용으로는 과도한 비용 |

> **결론**: 이 코스에서는 **슬롯 예약을 사용하지 않습니다**. 온디맨드 모델이 학습 규모에 적합하며, 무료 구간 덕분에 추가 비용이 발생하지 않는 경우가 대부분입니다.
>
> 단, 기업 환경에서 슬롯 예약을 이미 사용하는 경우, 해당 예약 범위 내에서 코스를 운영하면 추가 비용이 발생하지 않습니다.

#### 8.1.3 교육 환경별 예상 비용 요약

| 시나리오 | 예상 월 비용 (학습자 1인) | 비고 |
|----------|--------------------------|------|
| 자기 학습 (소규모) | **$0** | 무료 구간 내 |
| 팀 코스 5인 | **$0~$1** | 무료 구간 공유 불가, 1인당 독립 |
| 팀 코스 20인 | **$0~$3/인** | 각자 GCP 프로젝트 사용 시 |
| 공유 프로젝트 20인 | **$5~$20** | 무료 구간이 프로젝트 단위로 적용 |

> **교육 팁**: 가능하면 학습자별로 **독립 GCP 프로젝트**를 사용하게 하여 각자 무료 구간 혜택을 받도록 합니다. GCP 신규 계정은 $300 크레딧도 제공됩니다.

---

### 8.2 쿼리 비용 추정 방법

#### 8.2.1 쿼리 실행 전 드라이 런(Dry Run)으로 비용 추정

BigQuery는 쿼리를 실제 실행하기 전에 **처리할 데이터 크기를 추정**할 수 있는 드라이 런 기능을 제공합니다.

```bash
# 드라이 런: 실제 데이터를 처리하지 않고 처리량만 추정
bq query \
  --use_legacy_sql=false \
  --dry_run \
  'SELECT * FROM `your-project.raw.events` WHERE DATE(event_time) = "2024-01-01"'

# 출력 예시:
# Query successfully validated. Assuming the tables are not modified,
# running this query will process 45678901 bytes of data.
```

```bash
# 처리량을 GB/TB 단위로 변환하는 함수 (bash)
estimate_bq_cost() {
  # 입력: 바이트 수
  local bytes=$1
  local gb=$(echo "scale=4; $bytes / 1073741824" | bc)   # 바이트 → GB
  local tb=$(echo "scale=6; $bytes / 1099511627776" | bc) # 바이트 → TB
  local cost=$(echo "scale=6; $tb * 6.25" | bc)           # TB × $6.25

  echo "처리량: ${gb} GB (${tb} TB)"
  echo "예상 비용: \$${cost} USD"
  if (( $(echo "$tb < 0.001" | bc -l) )); then
    echo "→ 무료 구간 소진량 매우 적음 (안전)"
  fi
}

# 사용 예: 드라이 런 결과에서 바이트 추출 후 계산
estimate_bq_cost 45678901
```

#### 8.2.2 Python으로 드라이 런 자동화

```python
from google.cloud import bigquery

def estimate_query_cost(project_id: str, query: str) -> dict:
    """
    쿼리 실행 전 처리량과 예상 비용을 추정합니다.

    Args:
        project_id: GCP 프로젝트 ID
        query: 추정할 BigQuery SQL 쿼리

    Returns:
        처리량(bytes, GB, TB)과 예상 비용($) 딕셔너리
    """
    client = bigquery.Client(project=project_id)

    # 드라이 런 설정
    job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)

    # 드라이 런 실행 (실제 데이터 처리 없음)
    job = client.query(query, job_config=job_config)

    bytes_processed = job.total_bytes_processed
    gb_processed = bytes_processed / (1024 ** 3)
    tb_processed = bytes_processed / (1024 ** 4)

    # 온디맨드 요금: $6.25/TB (첫 1TB 무료)
    PRICE_PER_TB = 6.25
    FREE_TIER_TB = 1.0

    billable_tb = max(0, tb_processed - FREE_TIER_TB)
    estimated_cost_usd = billable_tb * PRICE_PER_TB

    return {
        "bytes": bytes_processed,
        "gb": round(gb_processed, 4),
        "tb": round(tb_processed, 6),
        "estimated_cost_usd": round(estimated_cost_usd, 6),
        "within_free_tier": tb_processed < FREE_TIER_TB,
    }


# 사용 예시
if __name__ == "__main__":
    result = estimate_query_cost(
        project_id="your-project-id",
        query="SELECT COUNT(*) FROM `your-project.raw.events`",
    )
    print(f"처리량: {result['gb']} GB ({result['tb']} TB)")
    print(f"예상 비용: ${result['estimated_cost_usd']:.4f} USD")
    print(f"무료 구간 이내: {result['within_free_tier']}")
```

#### 8.2.3 BigQuery Console에서 쿼리 비용 확인

GCP 콘솔의 BigQuery Studio에서도 쿼리 편집기 우측 상단에 처리량이 실시간으로 표시됩니다:

1. [BigQuery Studio](https://console.cloud.google.com/bigquery) 접속
2. 쿼리 편집기에 SQL 입력
3. 우측 상단의 **"이 쿼리는 X MB를 처리합니다"** 확인
4. 실행 전 비용이 허용 범위인지 판단

#### 8.2.4 `bq-cost-guard` 훅을 통한 자동 비용 제어

이 코스의 Claude Code 설정에는 `bq-cost-guard.sh` 훅이 포함되어 있습니다. 이 훅은 BigQuery 쿼리 실행 전 드라이 런을 수행하여 임계값을 초과하면 경고를 출력합니다.

```bash
# .claude/hooks/bq-cost-guard.sh 동작 원리
# - 환경 변수 BQ_COST_LIMIT_GB (기본값: 10GB)를 임계값으로 사용
# - 드라이 런 결과가 임계값 초과 시 Claude에게 경고 반환
# - 학습자가 실수로 대용량 쿼리를 실행하는 것을 사전 방지
export BQ_COST_LIMIT_GB=10   # 쿼리당 최대 허용 처리량 (GB)
```

> **강사 팁**: 학습자에게 훅을 비활성화하는 방법을 가르치기 전에, 훅의 **목적**을 먼저 이해시키세요. 비용 인식이 데이터 엔지니어링의 핵심 역량입니다.

---

### 8.3 예산 알림 설정

GCP 예산 알림은 월 지출이 지정한 임계값에 도달하면 이메일을 발송합니다. 학습자별 독립 프로젝트를 사용하거나, 공유 프로젝트의 총 비용을 모니터링할 때 유용합니다.

#### 8.3.1 GCP Console에서 예산 알림 설정 (GUI)

1. [GCP Billing Console](https://console.cloud.google.com/billing) 접속
2. 결제 계정 선택 → **"예산 및 알림"** 클릭
3. **"예산 만들기"** 클릭
4. 설정 항목:

| 항목 | 권장 설정 | 비고 |
|------|-----------|------|
| 예산 이름 | `data-analysis-course-budget` | 식별 가능한 이름 |
| 프로젝트 | 코스 전용 프로젝트 | 공유 프로젝트 또는 개별 프로젝트 |
| 서비스 | BigQuery | 다른 서비스 제외 |
| 예산 유형 | 월별 지정 금액 | |
| 예산 금액 | $5.00 (학습자 1인) / $50.00 (팀 코스) | 상황에 따라 조정 |
| 알림 임계값 | 50%, 80%, 100%, 120% | 초과 전 조기 경보 |

5. **"Pub/Sub 주제로 알림 전송"** (선택사항): 자동화된 대응을 위한 고급 설정

#### 8.3.2 gcloud CLI로 예산 알림 설정

```bash
# 결제 계정 ID 확인
BILLING_ACCOUNT=$(gcloud billing accounts list --format='value(name)' | head -1)
echo "결제 계정 ID: $BILLING_ACCOUNT"

# 예산 생성 (gcloud beta billing budgets)
gcloud billing budgets create \
  --billing-account="$BILLING_ACCOUNT" \
  --display-name="data-analysis-course-budget" \
  --budget-amount=10USD \
  --threshold-rule=percent=0.5 \
  --threshold-rule=percent=0.8 \
  --threshold-rule=percent=1.0 \
  --filter-projects="projects/${GCP_PROJECT_ID}"

# 예산 목록 확인
gcloud billing budgets list --billing-account="$BILLING_ACCOUNT"
```

> **참고**: `gcloud billing budgets` 명령은 `gcloud beta` 컴포넌트가 필요할 수 있습니다. `gcloud components install beta`로 설치하세요.

#### 8.3.3 BigQuery 쿼리 비용 한도 설정 (프로젝트 수준)

특정 프로젝트에서 단일 쿼리가 처리할 수 있는 최대 데이터량을 제한할 수 있습니다:

```bash
# 프로젝트의 사용자별 일일 처리량 한도 설정 (바이트 단위)
# 10GB = 10 * 1024^3 = 10737418240 bytes
gcloud services enable bigquery.googleapis.com --project=$GCP_PROJECT_ID

# BigQuery 설정에서 사용자별 일일 처리량 한도 설정
# (Console → BigQuery → 프로젝트 설정 → 사용자 일일 한도)
# 권장: 개발/학습 환경에서 10GB/일/사용자

# 또는 API를 통해 설정:
bq update --project_id=$GCP_PROJECT_ID \
  --default_query_job_config='{"query": {"maximumBytesBilled": "10737418240"}}'
```

#### 8.3.4 서비스 계정별 예산 추적을 위한 레이블 전략

여러 학습자가 같은 프로젝트를 공유할 때, BigQuery 작업에 레이블을 추가하면 학습자별 비용 분리가 가능합니다:

```python
from google.cloud import bigquery

def run_labeled_query(
    project_id: str,
    query: str,
    student_id: str,
    module_id: str,
) -> bigquery.QueryJob:
    """
    학습자 ID와 모듈 ID 레이블을 포함하여 쿼리를 실행합니다.
    INFORMATION_SCHEMA.JOBS에서 레이블로 필터링하여 비용을 추적할 수 있습니다.
    """
    client = bigquery.Client(project=project_id)

    job_config = bigquery.QueryJobConfig(
        labels={
            "student_id": student_id,   # 예: "student_01"
            "module_id": module_id,     # 예: "module_2"
            "course": "harness-engineering",
        }
    )

    return client.query(query, job_config=job_config)
```

---

### 8.4 비용 모니터링 쿼리

강사가 정기적으로 실행하여 비용 현황을 파악하는 쿼리 모음입니다.

#### 8.4.1 일별 쿼리 처리량 및 추정 비용

```sql
-- 최근 7일간 일별 처리량 및 추정 비용 조회
SELECT
  DATE(creation_time) AS query_date,
  COUNT(*)            AS query_count,
  -- 처리량을 GB 단위로 변환
  ROUND(SUM(total_bytes_processed) / POW(1024, 3), 2)  AS total_gb_processed,
  -- 비용 추정: $6.25/TB, 단 무료 구간(1TB/월)은 이미 소진된 것으로 가정
  ROUND(SUM(total_bytes_processed) / POW(1024, 4) * 6.25, 4) AS estimated_cost_usd
FROM `region-US`.INFORMATION_SCHEMA.JOBS
WHERE
  creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND state = 'DONE'
  AND error_result IS NULL  -- 오류 쿼리 제외 (과금 없음)
GROUP BY 1
ORDER BY 1 DESC
```

#### 8.4.2 사용자별 처리량 집계

```sql
-- 사용자(이메일)별 총 처리량 및 쿼리 횟수 (이번 달)
SELECT
  user_email,
  COUNT(*)  AS query_count,
  ROUND(SUM(total_bytes_processed) / POW(1024, 3), 2) AS total_gb_processed,
  ROUND(SUM(total_bytes_processed) / POW(1024, 4) * 6.25, 4) AS estimated_cost_usd,
  -- 가장 큰 단일 쿼리
  ROUND(MAX(total_bytes_processed) / POW(1024, 3), 2) AS max_single_query_gb
FROM `region-US`.INFORMATION_SCHEMA.JOBS
WHERE
  creation_time >= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), MONTH)
  AND state = 'DONE'
  AND error_result IS NULL
GROUP BY 1
ORDER BY total_gb_processed DESC
```

#### 8.4.3 학습자 레이블 기반 비용 분리 (레이블 전략 사용 시)

```sql
-- 레이블(student_id, module_id)을 기준으로 학습자별/모듈별 비용 집계
SELECT
  labels.value   AS student_id,
  COUNT(*)       AS query_count,
  ROUND(SUM(total_bytes_processed) / POW(1024, 3), 2)  AS total_gb_processed,
  ROUND(SUM(total_bytes_processed) / POW(1024, 4) * 6.25, 4) AS estimated_cost_usd
FROM `region-US`.INFORMATION_SCHEMA.JOBS,
  UNNEST(labels) AS labels
WHERE
  labels.key = 'student_id'
  AND creation_time >= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), MONTH)
  AND state = 'DONE'
GROUP BY 1
ORDER BY total_gb_processed DESC
```

#### 8.4.4 비용 임계값 초과 쿼리 탐지

```sql
-- 단일 쿼리 중 1GB 이상 처리한 쿼리 목록 (과도한 쿼리 식별용)
SELECT
  job_id,
  user_email,
  creation_time,
  ROUND(total_bytes_processed / POW(1024, 3), 2) AS gb_processed,
  ROUND(total_bytes_processed / POW(1024, 4) * 6.25, 4) AS estimated_cost_usd,
  -- 쿼리 앞 200자만 표시
  SUBSTR(query, 1, 200) AS query_preview
FROM `region-US`.INFORMATION_SCHEMA.JOBS
WHERE
  creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  AND total_bytes_processed > 1073741824  -- 1GB 초과
  AND state = 'DONE'
ORDER BY total_bytes_processed DESC
LIMIT 20
```

#### 8.4.5 월별 누적 비용 대시보드용 쿼리

```sql
-- 이번 달 누적 처리량과 무료 구간 소진 현황
WITH monthly_usage AS (
  SELECT
    SUM(total_bytes_processed) AS total_bytes
  FROM `region-US`.INFORMATION_SCHEMA.JOBS
  WHERE
    creation_time >= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), MONTH)
    AND state = 'DONE'
    AND error_result IS NULL
)
SELECT
  -- 총 처리량
  ROUND(total_bytes / POW(1024, 3), 2) AS total_gb_processed,
  ROUND(total_bytes / POW(1024, 4), 4) AS total_tb_processed,
  -- 무료 구간(1TB) 소진 비율
  ROUND(total_bytes / POW(1024, 4) * 100, 2) AS free_tier_used_pct,
  -- 무료 구간 초과 여부
  CASE
    WHEN total_bytes < POW(1024, 4) THEN '✅ 무료 구간 이내'
    ELSE '⚠️ 무료 구간 초과 — 과금 발생'
  END AS free_tier_status,
  -- 예상 청구 금액
  ROUND(
    GREATEST(0, total_bytes / POW(1024, 4) - 1.0) * 6.25, 4
  ) AS estimated_bill_usd
FROM monthly_usage
```

> **실행 방법**: 위 쿼리는 `region-US`로 고정되어 있습니다. 다른 리전을 사용하는 경우 `region-asia-northeast1` (서울) 등으로 변경하세요.

---

### 8.5 비용 절감 권장 사항

#### 8.5.1 쿼리 최적화 전략

| 전략 | 효과 | 구현 방법 |
|------|------|-----------|
| **파티션 필터 사용** | 처리량 80~99% 감소 가능 | `WHERE DATE(event_time) = '2024-01-01'` |
| **SELECT * 금지** | 필요한 컬럼만 처리 | 명시적 컬럼 목록 사용 |
| **쿼리 캐시 활용** | 반복 쿼리 비용 0 | 동일 쿼리 자동 캐시 (24시간) |
| **미리보기 사용** | 비용 0 | Console에서 "미리보기" 탭 사용 (100행) |
| **LIMIT 조기 적용** | 완전한 절감 아님 | BigQuery는 LIMIT 전에 전체 스캔 가능 |
| **테이블 파티셔닝** | 스캔 범위 제한 | `event_time`으로 일별 파티셔닝 |

> **중요**: BigQuery에서 `LIMIT 10`을 사용해도 `WHERE` 없이는 전체 테이블을 스캔합니다. **파티션 필터가 가장 효과적인 비용 절감 수단**입니다.

#### 8.5.2 dbt 모델 설정 최적화

```yaml
# dbt_project.yml — 개발 환경에서 행 수 제한
models:
  fittrack_analysis:
    +materialized: view  # 기본값: view (쿼리 시점에 처리)

    staging:
      +materialized: view

    intermediate:
      +materialized: ephemeral  # 개발 시 임시 CTE로 처리

    marts:
      +materialized: table  # 최종 마트만 테이블로 구체화
```

```sql
-- dbt 모델에 파티셔닝 설정 (bigquery_partition_by 설정)
-- fct_daily_active_users.sql 예시
{{
  config(
    materialized='table',
    partition_by={
      "field": "activity_date",        -- 파티션 기준 컬럼
      "data_type": "date",
      "granularity": "day"
    },
    cluster_by=["platform", "country"] -- 클러스터링으로 추가 최적화
  )
}}

SELECT
  DATE(event_time) AS activity_date,
  -- ...
```

#### 8.5.3 개발 환경에서의 데이터 샘플링

```sql
-- 개발 중 전체 테이블 대신 최근 7일 샘플로 쿼리
-- 합성 데이터 기준: 약 180일 데이터 중 7일만 사용 → ~96% 비용 절감
SELECT
  user_id,
  event_name,
  event_time
FROM `{{ env_var('BQ_PROJECT_ID') }}.raw.events`
WHERE
  -- 파티션 필터: 최근 7일만 스캔
  DATE(event_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
  -- 개발 환경에서는 추가 샘플링
  {% if target.name == 'dev' %}
    AND MOD(ABS(FARM_FINGERPRINT(user_id)), 10) = 0  -- 10% 샘플
  {% endif %}
```

#### 8.5.4 Claude Code 비용 훅 활용

학습자가 Claude에게 BigQuery 쿼리 생성을 요청할 때, `bq-cost-guard` 훅이 자동으로 비용을 확인합니다:

```bash
# .claude/hooks/bq-cost-guard.sh 확인
# 훅이 활성화되어 있는지 확인
cat .claude/settings.json | grep -A5 "bq-cost-guard"

# 임계값 조정 (기본값: 10GB)
# .claude/settings.json에서 환경 변수로 설정
export BQ_COST_LIMIT_GB=5  # 더 엄격한 임계값 적용
```

---

### 8.6 학습자별 사용량 모니터링

#### 8.6.1 공유 프로젝트에서 학습자별 모니터링

학습자가 공유 GCP 프로젝트를 사용하는 경우, 강사가 다음 절차로 학습자별 사용량을 추적합니다:

**방법 1: 사용자 이메일 기반 모니터링**

```bash
# 특정 학습자의 금주 처리량 확인
STUDENT_EMAIL="student01@example.com"

bq query --use_legacy_sql=false "
SELECT
  user_email,
  DATE(creation_time)   AS query_date,
  COUNT(*)              AS query_count,
  ROUND(SUM(total_bytes_processed) / POW(1024, 3), 2) AS gb_processed
FROM \`region-US\`.INFORMATION_SCHEMA.JOBS
WHERE
  user_email = '${STUDENT_EMAIL}'
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND state = 'DONE'
GROUP BY 1, 2
ORDER BY 2 DESC
"
```

**방법 2: 서비스 계정 기반 모니터링 (학습자별 서비스 계정 사용 시)**

```bash
# 학습자별 서비스 계정 생성
for i in $(seq -w 1 20); do
  SA_NAME="student${i}-sa"
  SA_EMAIL="${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

  # 서비스 계정 생성
  gcloud iam service-accounts create "$SA_NAME" \
    --display-name="학습자 ${i} 서비스 계정" \
    --project="$GCP_PROJECT_ID"

  # 필요 권한 부여 (BigQuery 작업 실행 + 데이터 읽기/쓰기)
  gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/bigquery.jobUser"

  gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/bigquery.dataEditor"
done

echo "서비스 계정 생성 완료: student01-sa ~ student20-sa"
```

```sql
-- 서비스 계정 이메일로 학습자별 처리량 조회
SELECT
  -- 서비스 계정 이름에서 학습자 번호 추출
  REGEXP_EXTRACT(user_email, r'student(\d+)-sa') AS student_num,
  user_email,
  COUNT(*)   AS query_count,
  ROUND(SUM(total_bytes_processed) / POW(1024, 3), 2) AS total_gb_processed,
  ROUND(SUM(total_bytes_processed) / POW(1024, 4) * 6.25, 4) AS estimated_cost_usd
FROM `region-US`.INFORMATION_SCHEMA.JOBS
WHERE
  creation_time >= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), MONTH)
  AND state = 'DONE'
  AND user_email LIKE 'student%@%'
GROUP BY 1, 2
ORDER BY total_gb_processed DESC
```

#### 8.6.2 학습자별 독립 프로젝트 환경에서의 모니터링

학습자별로 독립 GCP 프로젝트를 사용하는 경우, 강사가 직접 각 프로젝트를 조회할 수 없습니다. 대신 다음 방법을 권장합니다:

**학습자 자가 보고 템플릿**

학습자들이 주간 리뷰 때 다음 명령어로 자신의 사용량을 확인하고 보고합니다:

```bash
# 학습자용 비용 확인 스크립트 (check-my-usage.sh)
#!/bin/bash

# 이번 달 사용량 요약
echo "=== 이번 달 BigQuery 사용량 요약 ==="
bq query --use_legacy_sql=false --format=pretty "
SELECT
  COUNT(*) AS total_queries,
  ROUND(SUM(total_bytes_processed) / POW(1024, 3), 2) AS total_gb,
  ROUND(SUM(total_bytes_processed) / POW(1024, 4) * 100, 2) AS free_tier_used_pct,
  CASE
    WHEN SUM(total_bytes_processed) < POW(1024, 4) THEN '무료 구간 이내'
    ELSE '무료 구간 초과'
  END AS status
FROM \`region-US\`.INFORMATION_SCHEMA.JOBS
WHERE
  creation_time >= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), MONTH)
  AND state = 'DONE'
  AND error_result IS NULL
"
```

**이 스크립트를 스타터 레포에 포함**:

```bash
# 스타터 레포의 scripts/ 디렉토리에 추가
cp check-my-usage.sh starter-repo/scripts/check-my-usage.sh
chmod +x starter-repo/scripts/check-my-usage.sh
```

#### 8.6.3 이상 사용 탐지 및 대응

```bash
# 강사용: 프로젝트 전체에서 비용 이상 징후 자동 탐지
# 단일 사용자가 하루에 5GB 이상 처리한 경우 경고

bq query --use_legacy_sql=false "
SELECT
  user_email,
  DATE(creation_time) AS query_date,
  COUNT(*)            AS query_count,
  ROUND(SUM(total_bytes_processed) / POW(1024, 3), 2) AS gb_processed,
  -- 가장 큰 쿼리 미리보기
  STRING_AGG(SUBSTR(query, 1, 100) ORDER BY total_bytes_processed DESC LIMIT 1)
    AS largest_query_preview
FROM \`region-US\`.INFORMATION_SCHEMA.JOBS
WHERE
  creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND state = 'DONE'
GROUP BY 1, 2
HAVING SUM(total_bytes_processed) > 5368709120  -- 5GB 초과
ORDER BY gb_processed DESC
"
```

#### 8.6.4 비용 리포트 자동화 (주간)

```python
#!/usr/bin/env python3
"""
weekly_cost_report.py
주간 학습자별 BigQuery 비용 리포트를 생성하여 이메일로 발송합니다.
강사 서버에서 cron으로 매주 월요일에 실행합니다.
"""

from google.cloud import bigquery
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText


def generate_weekly_report(project_id: str) -> str:
    """지난 주 학습자별 사용량 리포트 텍스트를 생성합니다."""
    client = bigquery.Client(project=project_id)

    # 지난 주 범위 계산
    today = datetime.utcnow().date()
    week_start = today - timedelta(days=today.weekday() + 7)  # 지난 월요일
    week_end = week_start + timedelta(days=6)                  # 지난 일요일

    query = f"""
    SELECT
      user_email,
      COUNT(*)   AS query_count,
      ROUND(SUM(total_bytes_processed) / POW(1024, 3), 2)  AS gb_processed,
      ROUND(SUM(total_bytes_processed) / POW(1024, 4) * 6.25, 4) AS est_cost_usd
    FROM `region-US`.INFORMATION_SCHEMA.JOBS
    WHERE
      DATE(creation_time) BETWEEN '{week_start}' AND '{week_end}'
      AND state = 'DONE'
      AND error_result IS NULL
    GROUP BY 1
    ORDER BY gb_processed DESC
    """

    rows = list(client.query(query).result())

    # 리포트 텍스트 생성
    report_lines = [
        f"📊 BigQuery 주간 사용량 리포트 ({week_start} ~ {week_end})",
        "=" * 60,
        f"{'사용자':<35} {'쿼리 수':>8} {'처리량(GB)':>12} {'예상 비용($)':>12}",
        "-" * 60,
    ]
    for row in rows:
        report_lines.append(
            f"{row.user_email:<35} {row.query_count:>8} "
            f"{row.gb_processed:>12.2f} {row.est_cost_usd:>12.4f}"
        )
    report_lines.append("=" * 60)

    total_gb = sum(r.gb_processed for r in rows)
    total_cost = sum(r.est_cost_usd for r in rows)
    report_lines.append(f"{'합계':<35} {'':>8} {total_gb:>12.2f} {total_cost:>12.4f}")

    return "\n".join(report_lines)


if __name__ == "__main__":
    report = generate_weekly_report(project_id="your-project-id")
    print(report)
```

---

### 8.7 코스 종료 후 리소스 정리

코스가 끝나면 불필요한 비용을 방지하기 위해 리소스를 정리합니다.

#### 8.7.1 BigQuery 데이터셋 삭제

```bash
# 1. 삭제 전 데이터셋 목록 확인
bq ls --project_id=$GCP_PROJECT_ID

# 2. 코스용 데이터셋 일괄 삭제 (모든 테이블 포함)
for dataset in raw analytics; do
  echo "삭제 중: ${GCP_PROJECT_ID}:${dataset}"
  bq rm -r -f "${GCP_PROJECT_ID}:${dataset}"
done

# 3. 다중 학습자 데이터셋 삭제 (20인 기준)
for i in $(seq -w 1 20); do
  bq rm -r -f "${GCP_PROJECT_ID}:raw_student${i}" 2>/dev/null || true
  bq rm -r -f "${GCP_PROJECT_ID}:analytics_student${i}" 2>/dev/null || true
done

echo "데이터셋 정리 완료"
```

#### 8.7.2 서비스 계정 키 및 계정 삭제

```bash
# 서비스 계정 목록 확인
gcloud iam service-accounts list --project=$GCP_PROJECT_ID

# 코스용 서비스 계정 키 삭제
SA_EMAIL="bq-harness-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

# 해당 서비스 계정의 모든 키 삭제
for KEY_ID in $(gcloud iam service-accounts keys list \
    --iam-account=$SA_EMAIL \
    --format='value(name)' \
    --filter='keyType=USER_MANAGED'); do
  echo "키 삭제: $KEY_ID"
  gcloud iam service-accounts keys delete "$KEY_ID" \
    --iam-account=$SA_EMAIL --quiet
done

# 학습자별 서비스 계정 삭제 (다중 학습자 환경)
for i in $(seq -w 1 20); do
  SA="student${i}-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  gcloud iam service-accounts delete "$SA" --quiet 2>/dev/null || true
done

# 강사용 서비스 계정 삭제 (선택)
gcloud iam service-accounts delete "$SA_EMAIL" --quiet
```

#### 8.7.3 프로젝트 삭제 (선택 — 완전 정리)

```bash
# ⚠️ 주의: 프로젝트 삭제 시 모든 리소스가 영구 삭제됩니다 (30일 유예 후)
# 재사용 계획이 있으면 이 단계를 건너뛰고 데이터셋만 삭제하세요

# 삭제 전 프로젝트 확인
gcloud projects describe $GCP_PROJECT_ID

# 프로젝트 삭제 (30일 유예 기간 후 완전 삭제)
gcloud projects delete $GCP_PROJECT_ID

echo "프로젝트 삭제 요청됨. 30일 이내에 취소 가능: https://console.cloud.google.com/iam-admin/projects"
```

#### 8.7.4 정리 체크리스트

| 항목 | 완료 여부 | 명령어 |
|------|-----------|--------|
| BigQuery 데이터셋 삭제 | ☐ | `bq rm -r -f ${GCP_PROJECT_ID}:raw` |
| 학습자별 데이터셋 삭제 | ☐ | `bq rm -r -f ${GCP_PROJECT_ID}:raw_student*` |
| 서비스 계정 키 삭제 | ☐ | `gcloud iam service-accounts keys delete` |
| 예산 알림 삭제 | ☐ | GCP Console → 예산 및 알림 |
| GitHub Secrets 삭제 | ☐ | `gh secret delete GCP_SA_KEY` |
| 학습자 포크 아카이브 | ☐ | GitHub 레포 설정 → Archive |
| (선택) 프로젝트 삭제 | ☐ | `gcloud projects delete $GCP_PROJECT_ID` |

> **주의**: `gcloud projects delete`는 30일 유예 기간이 있으나, 이후 모든 데이터가 영구 삭제됩니다. 재사용 계획이 있으면 데이터셋만 삭제하세요.

---

## 9. 문제 해결(트러블슈팅)

### BigQuery 연결 오류

| 증상 | 원인 | 해결 방법 |
|------|------|-----------|
| `403 Access Denied` | 서비스 계정 권한 부족 | `bigquery.dataEditor` + `bigquery.jobUser` 역할 부여 확인 |
| `404 Not Found: Dataset` | 데이터셋 미생성 또는 프로젝트 ID 오류 | `bq ls ${GCP_PROJECT_ID}:raw` 실행하여 데이터셋 존재 확인 |
| `Could not deserialize key data` | JSON 키 형식 오류 | Secret 등록 시 키 전체를 그대로 복사했는지 확인 (줄바꿈 포함) |
| `Billing account not found` | 결제 미연결 | `gcloud billing projects link` 실행 |

### dbt 실행 오류

| 증상 | 원인 | 해결 방법 |
|------|------|-----------|
| `Profile 'fittrack_analysis' not found` | profiles.yml 누락 | `cp profiles.yml.example profiles.yml` 실행 후 프로젝트 ID 교체 |
| `env_var('BQ_PROJECT_ID') is undefined` | 환경 변수 미설정 | `export BQ_PROJECT_ID="<your-project-id>"` 실행 |
| `Relation does not exist` (staging 모델) | 소스 테이블 미생성 | 섹션 3의 합성 데이터 적재를 먼저 수행 |
| `dbt deps` 오류 | 패키지 의존성 미설치 | `uv run dbt deps` 실행 |

### GitHub Actions 오류

| 증상 | 원인 | 해결 방법 |
|------|------|-----------|
| `Error: Resource not accessible by integration` | 워크플로 권한 부족 | 섹션 5.3의 워크플로 권한 설정 확인 |
| `claude: command not found` | Claude Code CLI 미설치 (Actions 환경) | 워크플로에서 `npm install -g @anthropic-ai/claude-code` 스텝 추가 |
| `CLAUDE_CODE_TOKEN is not set` | Secret 미등록 | `gh secret list`로 Secret 등록 여부 확인 |
| 라벨 전환이 트리거되지 않음 | `issues: labeled` 이벤트 누락 | 워크플로 `on:` 트리거에 `issues: [labeled]` 포함 확인 |

### 합성 데이터 생성 오류

| 증상 | 원인 | 해결 방법 |
|------|------|-----------|
| `ModuleNotFoundError: numpy` | 의존성 미설치 | `uv pip install numpy pandas` 실행 |
| `BigQuery: Permission denied` (적재 시) | 서비스 계정 권한 부족 | `bigquery.dataEditor` 역할 확인 |
| 데이터 행 수가 기대보다 적음 | 파라미터 기본값이 아닌 경우 | `--num-users`, `--start-date`, `--end-date` 파라미터 확인 |

---

## 부록: 다중 학습자 환경 운영 팁

조직/팀 단위로 코스를 운영할 때 참고사항입니다.

### 학습자별 격리 방법

| 방법 | 장점 | 단점 |
|------|------|------|
| **학습자별 GCP 프로젝트** | 완전 격리, 비용 추적 용이 | 관리 오버헤드 높음 |
| **공유 프로젝트 + 학습자별 데이터셋** | 설정 간편 | 데이터셋 네이밍 규칙 필요 |
| **학습자별 포크** | GitHub 레벨 격리 | 각 포크에 Secrets 개별 등록 필요 |

### 권장 방식: 공유 프로젝트 + 학습자별 데이터셋

```bash
# 학습자별 데이터셋 생성 (예: raw_student01, analytics_student01)
for i in $(seq -w 1 20); do
  bq mk --dataset ${GCP_PROJECT_ID}:raw_student${i}
  bq mk --dataset ${GCP_PROJECT_ID}:analytics_student${i}
done
```

학습자는 `profiles.yml`에서 자신의 데이터셋을 지정합니다:

```yaml
fittrack_analysis:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: service-account
      project: "<SHARED_PROJECT_ID>"
      dataset: analytics_student01   # 학습자 번호에 맞게 변경
      location: US
```

> **참고**: 다중 학습자 환경에서는 학습자별 서비스 계정을 별도로 만들거나, 공유 서비스 계정에 모든 학습자 데이터셋 접근 권한을 부여합니다.

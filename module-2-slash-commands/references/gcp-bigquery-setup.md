# GCP/BigQuery 환경 설정 가이드

> **대상**: "하니스 엔지니어링 for 데이터 분석" 코스 수강생
> **목적**: BigQuery를 사용하기 위한 GCP 환경을 처음부터 설정하는 방법을 단계별로 안내합니다.
>
> 이미 GCP 프로젝트와 BigQuery 접근 권한이 있다면 [빠른 확인 체크리스트](#빠른-확인-체크리스트)로 바로 이동하세요.

---

## 목차

1. [사전 요구사항](#1-사전-요구사항)
2. [GCP 계정 생성](#2-gcp-계정-생성)
3. [gcloud CLI 설치 및 인증](#3-gcloud-cli-설치-및-인증)
4. [GCP 프로젝트 생성](#4-gcp-프로젝트-생성)
5. [BigQuery API 활성화](#5-bigquery-api-활성화)
6. [BigQuery 데이터셋 생성](#6-bigquery-데이터셋-생성)
7. [IAM 역할 및 서비스 계정](#7-iam-역할-및-서비스-계정)
8. [학습자 계정 프로비저닝 시나리오](#8-학습자-계정-프로비저닝-시나리오)
9. [GitHub Secret 등록](#9-github-secret-등록)
10. [최종 검증](#10-최종-검증)
11. [비용 관리](#11-비용-관리)
12. [문제 해결](#12-문제-해결)

---

## 빠른 확인 체크리스트

이미 GCP를 사용 중인 분은 아래 항목을 확인하세요:

```bash
# 1. gcloud 인증 확인
gcloud auth list

# 2. 현재 프로젝트 확인
gcloud config get-value project

# 3. BigQuery API 활성화 확인
gcloud services list --enabled --filter="name:bigquery.googleapis.com"

# 4. 서비스 계정 목록 확인
gcloud iam service-accounts list

# 5. BigQuery 접근 테스트
bq query --use_legacy_sql=false "SELECT 'BigQuery 연결 성공' AS status"
```

모두 정상이라면 [9. GitHub Secret 등록](#9-github-secret-등록)으로 바로 이동하세요.

---

## 1. 사전 요구사항

### 필요한 항목

| 항목 | 설명 | 확인 방법 |
|------|------|-----------|
| Google 계정 | Gmail 등 Google 계정 | 브라우저에서 로그인 |
| 신용카드/체크카드 | GCP 결제 계정 등록용 (무료 크레딧 $300 제공) | — |
| macOS 또는 Linux 터미널 | CLI 명령어 실행 환경 | 터미널 앱 실행 |
| GitHub 계정 | GitHub Actions 및 Secret 설정 | github.com |

### 예상 비용

이 코스에서 사용하는 BigQuery 비용은 매우 적습니다:

| 구분 | 예상 비용 | 설명 |
|------|-----------|------|
| 저장 비용 | ~$0.02/월 | 합성 데이터 약 500MB |
| 쿼리 비용 | ~$0.50~$2.00/월 | on-demand 요금, 1TB/월 무료 |
| 합계 | **$2.50 미만/월** | GCP 신규 계정 $300 무료 크레딧으로 충분 |

> **참고**: GCP 신규 계정에는 **$300 무료 크레딧(90일 유효)**이 제공됩니다.
> 이 코스 전체 실습 비용은 크레딧의 약 1% 미만입니다.

---

## 2. GCP 계정 생성

> 이미 GCP 계정이 있다면 이 단계를 건너뛰세요.

### 2.1 Google Cloud Console 접속

1. 브라우저에서 [https://console.cloud.google.com](https://console.cloud.google.com) 접속
2. Google 계정으로 로그인
3. **"무료로 시작"** 또는 **"시작하기"** 버튼 클릭

### 2.2 결제 계정 설정

GCP 서비스 이용을 위해 결제 계정이 필요합니다. (실제 청구는 무료 크레딧 소진 후 발생)

1. 국가 선택: **대한민국**
2. 이용약관 동의
3. 결제 정보 입력:
   - 계정 유형: 개인
   - 카드 정보 입력 (즉시 청구되지 않음, 크레딧 소진 후 청구)

> ⚠️ **자동 청구 방지**: 무료 체험 기간(90일) 종료 후 자동으로 유료로 전환되지 않습니다.
> 유료 전환을 원하지 않으면 결제 계정을 비활성화하세요.

### 2.3 GCP Console 기본 탐색

Console에 처음 접속하면 다음 구성이 보입니다:
- **상단 좌측**: 현재 프로젝트 선택 드롭다운
- **좌측 메뉴**: GCP 서비스 목록 (BigQuery, IAM 등)
- **검색창**: 서비스 빠른 검색

---

## 3. gcloud CLI 설치 및 인증

gcloud CLI는 터미널에서 GCP 리소스를 관리하는 도구입니다.

### 3.1 gcloud CLI 설치

```bash
# macOS — Homebrew 방식 (권장)
brew install --cask google-cloud-sdk

# macOS/Linux — 공식 설치 스크립트
curl https://sdk.cloud.google.com | bash
exec -l $SHELL  # 셸 재시작
```

```bash
# 설치 확인
gcloud --version
```

예상 출력:
```
Google Cloud SDK 460.0.0
bq 2.1.x
core 2024.01.xx
gsutil 5.x
```

> **Windows 사용자**: [gcloud CLI 공식 문서](https://cloud.google.com/sdk/docs/install-sdk#windows)를 참조하세요.
> 이 코스는 macOS/Linux 환경을 기준으로 작성되었습니다.

### 3.2 gcloud 인증

```bash
# 1단계: 브라우저를 통한 GCP 계정 로그인
gcloud auth login
# → 브라우저가 열리면 GCP 계정으로 로그인

# 2단계: Application Default Credentials 설정
# (Python 스크립트 및 SDK가 사용하는 인증 방식)
gcloud auth application-default login
# → 브라우저가 다시 열림, 동일한 계정으로 로그인

# 3단계: 인증 확인
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

`*`가 붙은 계정이 현재 활성 계정입니다.

---

## 4. GCP 프로젝트 생성

### 4.1 프로젝트 ID 결정

프로젝트 ID는 전 세계에서 고유해야 하며, 한 번 설정하면 변경할 수 없습니다.

**권장 형식**: `fittrack-analysis-[사용자구분]`

예시:
- `fittrack-analysis-mkim` (이름 이니셜)
- `fittrack-analysis-2026` (연도)
- `fittrack-analysis-prod` (환경)

> **규칙**: 소문자, 숫자, 하이픈만 사용. 6~30자. 문자로 시작.

### 4.2 프로젝트 생성 (CLI)

```bash
# 프로젝트 ID 설정 (본인만의 고유한 ID로 변경)
export GCP_PROJECT_ID="fittrack-analysis-yourname"

# 프로젝트 생성
gcloud projects create $GCP_PROJECT_ID \
  --name="FitTrack Analysis"

# 현재 세션에서 기본 프로젝트로 설정
gcloud config set project $GCP_PROJECT_ID

# 생성 확인
gcloud projects describe $GCP_PROJECT_ID
```

예상 출력:
```
createTime: '2026-03-22T00:00:00.000Z'
lifecycleState: ACTIVE
name: FitTrack Analysis
projectId: fittrack-analysis-yourname
projectNumber: '123456789012'
```

### 4.3 결제 계정 연결

BigQuery를 사용하려면 프로젝트에 결제 계정이 연결되어야 합니다.

```bash
# 결제 계정 ID 확인
gcloud billing accounts list
```

예상 출력:
```
ACCOUNT_ID            NAME                OPEN  MASTER_ACCOUNT_ID
01ABCD-234567-89EFGH  My Billing Account  True
```

```bash
# 프로젝트에 결제 계정 연결
gcloud billing projects link $GCP_PROJECT_ID \
  --billing-account=<ACCOUNT_ID>
  # 위 출력의 ACCOUNT_ID 값으로 교체
```

결제 계정이 없다면:
1. [GCP Console → 결제](https://console.cloud.google.com/billing) 이동
2. **"결제 계정 만들기"** 클릭
3. 카드 정보 입력 후 연결

### 4.4 프로젝트 생성 (Console UI 방식)

CLI 대신 웹 콘솔을 선호하는 경우:

1. [GCP Console](https://console.cloud.google.com) 상단의 프로젝트 선택 드롭다운 클릭
2. **"새 프로젝트"** 클릭
3. 프로젝트 이름: `FitTrack Analysis`
4. 프로젝트 ID 입력 (자동 생성되며 수정 가능)
5. **"만들기"** 클릭
6. 결제 → 이 프로젝트에 결제 계정 연결

---

## 5. BigQuery API 활성화

GCP 프로젝트에서 BigQuery를 사용하려면 BigQuery API를 활성화해야 합니다.

### 5.1 API 활성화 (CLI)

```bash
# BigQuery API 활성화
gcloud services enable bigquery.googleapis.com \
  --project=$GCP_PROJECT_ID

# 활성화 확인
gcloud services list --enabled \
  --filter="name:bigquery.googleapis.com" \
  --project=$GCP_PROJECT_ID
```

예상 출력:
```
NAME                        TITLE
bigquery.googleapis.com     BigQuery API
```

### 5.2 API 활성화 (Console UI 방식)

1. [GCP Console → API 및 서비스 → 라이브러리](https://console.cloud.google.com/apis/library) 이동
2. 검색창에 **"BigQuery API"** 입력
3. BigQuery API 선택
4. **"사용"** 버튼 클릭

> **참고**: API 활성화 후 적용까지 약 1~2분이 소요될 수 있습니다.

### 5.3 추가 권장 API

이 코스에서 사용하는 추가 API를 한 번에 활성화합니다:

```bash
# Cloud Resource Manager API (프로젝트 관리)
gcloud services enable cloudresourcemanager.googleapis.com \
  --project=$GCP_PROJECT_ID

# IAM API (서비스 계정 관리)
gcloud services enable iam.googleapis.com \
  --project=$GCP_PROJECT_ID

# Cloud Billing API (예산 알림 설정 시 필요)
gcloud services enable cloudbilling.googleapis.com \
  --project=$GCP_PROJECT_ID
```

---

## 6. BigQuery 데이터셋 생성

이 코스는 세 개의 BigQuery 데이터셋을 사용합니다.

### 6.1 데이터셋 구조

| 데이터셋 | 용도 | 접근 권한 |
|----------|------|-----------|
| `raw` | 합성 원시 이벤트 데이터 (강사 제공) | 읽기 전용 |
| `dbt_dev` | dbt 변환 결과 — 로컬 개발 환경 | 읽기/쓰기 |
| `dbt_ci` | dbt 변환 결과 — GitHub Actions CI | 읽기/쓰기 |

### 6.2 데이터셋 생성 (CLI)

```bash
# 1) raw 데이터셋 — 합성 원시 데이터 저장소
bq mk --dataset \
  --location=US \
  --description="FitTrack 앱 원시 이벤트 데이터 (합성)" \
  ${GCP_PROJECT_ID}:raw

# 2) dbt_dev 데이터셋 — 로컬 개발 환경 dbt 결과
bq mk --dataset \
  --location=US \
  --description="dbt 변환 모델 결과 — 로컬 개발(dev) 환경" \
  ${GCP_PROJECT_ID}:dbt_dev

# 3) dbt_ci 데이터셋 — GitHub Actions CI dbt 결과
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

### 6.3 리전 선택 가이드

| 리전 | 코드 | 권장 상황 |
|------|------|-----------|
| 미국 (멀티) | `US` | **이 코스 기본값** — 비용 최적화, 무료 쿼리 처리량 적용 |
| 서울 | `asia-northeast3` | 한국 시장 프로덕션 환경, 레이턴시 최소화 |
| 도쿄 | `asia-northeast1` | 일본/동아시아 멀티 리전 |

> **이 코스에서는 `US`를 사용합니다.** BigQuery 무료 처리량(매월 첫 1TB)은 모든 리전에 적용되지만,
> `US` 멀티 리전은 가용성과 비용 효율이 높습니다.

---

## 7. IAM 역할 및 서비스 계정

### 7.1 IAM 개요

**IAM(Identity and Access Management)**은 "누가 어떤 리소스에 무엇을 할 수 있는지"를 정의합니다.

이 코스에서는 두 가지 접근 방식을 사용합니다:
- **서비스 계정(Service Account)**: GitHub Actions 및 로컬 스크립트가 BigQuery에 접근할 때 사용
- **사용자 계정(User Account)**: 개발자가 직접 BigQuery Console을 사용할 때 적용

### 7.2 이 코스에서 필요한 IAM 역할

| 역할 | 설명 | 부여 이유 |
|------|------|-----------|
| `roles/bigquery.dataEditor` | 테이블 읽기/쓰기/삭제 | dbt 모델 빌드 결과를 BigQuery에 기록 |
| `roles/bigquery.jobUser` | 쿼리 작업 제출 및 실행 | `bq query`, dbt 실행 시 BigQuery Job 생성 |

> **부여하지 않는 역할 (보안상 이유)**:
> - `roles/bigquery.admin`: 데이터셋 생성/삭제 권한 포함 — 불필요
> - `roles/owner` / `roles/editor`: 과도한 권한 — 최소 권한 원칙 위반

### 7.3 서비스 계정 생성

서비스 계정은 사람이 아닌 **애플리케이션(GitHub Actions, 로컬 스크립트)**이 GCP에 인증할 때 사용합니다.

```bash
# 서비스 계정 이름 설정
export SA_NAME="fittrack-analyst"

# 서비스 계정 생성
gcloud iam service-accounts create $SA_NAME \
  --display-name="FitTrack Analysis Service Account" \
  --description="코스 실습용 BigQuery 접근 서비스 계정" \
  --project=$GCP_PROJECT_ID

# 서비스 계정 이메일 변수 설정
export SA_EMAIL="${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

# 생성 확인
gcloud iam service-accounts describe $SA_EMAIL \
  --project=$GCP_PROJECT_ID
```

예상 출력:
```
displayName: FitTrack Analysis Service Account
email: fittrack-analyst@fittrack-analysis-yourname.iam.gserviceaccount.com
name: projects/fittrack-analysis-yourname/serviceAccounts/fittrack-analyst@...
```

### 7.4 서비스 계정에 IAM 역할 부여

```bash
# 역할 1: BigQuery 데이터 편집자 (테이블 읽기/쓰기)
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/bigquery.dataEditor"

# 역할 2: BigQuery 작업 사용자 (쿼리 실행)
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/bigquery.jobUser"

# 부여된 역할 확인
gcloud projects get-iam-policy $GCP_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:$SA_EMAIL" \
  --format="table(bindings.role)"
```

예상 출력:
```
ROLE
roles/bigquery.dataEditor
roles/bigquery.jobUser
```

### 7.5 서비스 계정 JSON 키 생성

서비스 계정 키는 애플리케이션이 GCP에 인증하는 데 사용하는 자격증명 파일입니다.

```bash
# JSON 키 파일 생성
gcloud iam service-accounts keys create ./gcp-sa-key.json \
  --iam-account=$SA_EMAIL \
  --project=$GCP_PROJECT_ID

# 키 파일 내용 확인 (프로젝트 ID와 이메일만 출력)
python3 -c "
import json
with open('./gcp-sa-key.json') as f:
    d = json.load(f)
print(f'프로젝트: {d[\"project_id\"]}')
print(f'이메일: {d[\"client_email\"]}')
print(f'키 타입: {d[\"type\"]}')
"
```

예상 출력:
```
프로젝트: fittrack-analysis-yourname
이메일: fittrack-analyst@fittrack-analysis-yourname.iam.gserviceaccount.com
키 타입: service_account
```

> ⚠️ **보안 주의사항**:
> - `gcp-sa-key.json` 파일을 **절대 Git에 커밋하지 마세요**
> - 이 파일이 유출되면 악의적인 BigQuery 사용으로 요금이 발생할 수 있습니다
> - `.gitignore`에 `gcp-sa-key.json` 패턴이 포함되어 있는지 확인하세요

### 7.6 데이터셋별 세밀한 권한 제어 (선택 사항)

기본 설정은 프로젝트 전체에 `dataEditor` + `jobUser`를 부여합니다.
더 엄격한 보안이 필요하다면 데이터셋별로 권한을 설정할 수 있습니다:

```bash
# raw 데이터셋: 읽기 전용 ACL 파일 생성
cat > /tmp/raw_acl.json << EOF
{
  "access": [
    {"role": "OWNER", "specialGroup": "projectOwners"},
    {"role": "READER", "userByEmail": "${SA_EMAIL}"}
  ]
}
EOF

# ACL 적용 (raw 데이터셋은 읽기만 허용)
bq update --source /tmp/raw_acl.json ${GCP_PROJECT_ID}:raw

# dbt_dev 데이터셋: 읽기/쓰기 ACL 파일 생성
cat > /tmp/dbt_dev_acl.json << EOF
{
  "access": [
    {"role": "OWNER", "specialGroup": "projectOwners"},
    {"role": "WRITER", "userByEmail": "${SA_EMAIL}"}
  ]
}
EOF

bq update --source /tmp/dbt_dev_acl.json ${GCP_PROJECT_ID}:dbt_dev
```

> **참고**: 이 데이터셋별 권한 제어는 선택 사항입니다.
> 프로젝트 수준의 `dataEditor` + `jobUser` 조합으로 코스 실습에 충분합니다.

---

## 8. 학습자 계정 프로비저닝 시나리오

이 코스는 두 가지 환경에서 진행될 수 있습니다. 본인 상황에 맞는 시나리오를 선택하세요.

### 시나리오 A: 학습자 개인 GCP 프로젝트 (권장)

각 학습자가 본인의 GCP 프로젝트를 직접 만들고 관리합니다.

**장점**:
- 완전한 권한과 통제권
- 비용이 본인 계정에 귀속되어 명확
- 실무와 동일한 환경 경험

**설정 절차**: 이 가이드의 2~9장을 그대로 따릅니다.

**비용 예상**: 코스 전체 $2~5 (GCP 신규 계정 무료 크레딧 $300 내에서 해결)

---

### 시나리오 B: 강사 제공 공유 GCP 프로젝트

강사가 하나의 GCP 프로젝트를 생성하고, 학습자마다 별도의 서비스 계정을 발급합니다.

**장점**:
- 학습자가 GCP 결제 계정 없이도 참여 가능
- 강사가 비용을 중앙 관리

**학습자 수령 항목**:
강사로부터 다음 파일과 정보를 받습니다:

```
gcp-sa-key-[학습자명].json   ← 개인용 서비스 계정 JSON 키
GCP_PROJECT_ID              ← 공유 프로젝트 ID (예: fittrack-analysis-course)
```

**학습자 설정 절차**:

```bash
# 1단계: 받은 JSON 키 파일을 프로젝트 루트에 저장
cp ~/Downloads/gcp-sa-key-yourname.json ./gcp-sa-key.json

# 2단계: 키 파일 확인
python3 -c "
import json
with open('./gcp-sa-key.json') as f:
    d = json.load(f)
print(f'프로젝트: {d[\"project_id\"]}')
print(f'이메일: {d[\"client_email\"]}')
"

# 3단계: BigQuery 접근 테스트
export GOOGLE_APPLICATION_CREDENTIALS="./gcp-sa-key.json"
bq query --use_legacy_sql=false \
  "SELECT 'BigQuery 연결 성공' AS status, CURRENT_TIMESTAMP() AS ts"

# 4단계: 환경 변수 설정 (셸 프로파일에 추가 권장)
export GCP_PROJECT_ID="fittrack-analysis-course"  # 강사에게 받은 프로젝트 ID
```

> **공유 프로젝트 사용 시 주의사항**:
> - `dbt_dev` 데이터셋 내에 개인별 스키마를 사용합니다 (예: `dbt_dev_mkim`)
> - `profiles.yml`의 `schema` 값을 강사 지시에 따라 변경하세요
> - 다른 학습자의 데이터셋을 수정하지 마세요

---

### 시나리오 C: 기존 회사 GCP 프로젝트 사용

실무에서 이미 BigQuery를 사용하고 있다면 기존 프로젝트를 활용할 수 있습니다.

**필요 조건**:
- 본인 계정에 `bigquery.dataEditor` + `bigquery.jobUser` 권한 있음
- `raw`, `dbt_dev`, `dbt_ci` 데이터셋을 생성할 수 있음

**설정 절차**:

```bash
# 1단계: 기존 프로젝트로 전환
export GCP_PROJECT_ID="your-existing-project-id"
gcloud config set project $GCP_PROJECT_ID

# 2단계: BigQuery API 활성화 확인
gcloud services list --enabled --filter="name:bigquery.googleapis.com"

# 3단계: 코스용 데이터셋 생성 (이미 있다면 건너뜀)
bq mk --dataset --location=US ${GCP_PROJECT_ID}:raw
bq mk --dataset --location=US ${GCP_PROJECT_ID}:dbt_dev
bq mk --dataset --location=US ${GCP_PROJECT_ID}:dbt_ci

# 4단계: 서비스 계정 생성 (GitHub Actions용)
# 7.3~7.5 단계를 따릅니다
```

> **주의**: 회사 GCP 프로젝트를 사용할 때는 IT 보안 정책을 확인하세요.
> 코스용 데이터셋 이름(`raw`, `dbt_dev`, `dbt_ci`)이 기존 데이터셋과 충돌하지 않는지 확인하세요.

---

## 9. GitHub Secret 등록

서비스 계정 키와 프로젝트 ID를 GitHub Secret으로 등록합니다.
GitHub Actions에서 BigQuery에 접근할 때 이 Secret을 사용합니다.

### 9.1 필수 Secret 목록

| Secret 이름 | 값 | 설명 |
|-------------|-----|------|
| `GCP_SA_KEY` | JSON 키 파일 전체 내용 | BigQuery 인증용 서비스 계정 키 |
| `GCP_PROJECT_ID` | `fittrack-analysis-yourname` | GCP 프로젝트 ID |

### 9.2 GitHub Secret 등록 (CLI 방식 — 권장)

```bash
# GitHub CLI 로그인 (미로그인 시)
gh auth login

# GCP_SA_KEY 등록 (JSON 파일 내용을 그대로 전달)
gh secret set GCP_SA_KEY < ./gcp-sa-key.json

# GCP_PROJECT_ID 등록
gh secret set GCP_PROJECT_ID --body "$GCP_PROJECT_ID"

# 등록 확인 (값은 마스킹되어 이름만 표시됨)
gh secret list
```

예상 출력:
```
NAME            UPDATED
GCP_PROJECT_ID  2026-03-22
GCP_SA_KEY      2026-03-22
```

### 9.3 GitHub Secret 등록 (Console UI 방식)

1. GitHub 레포지토리 → **Settings** 탭
2. 좌측 메뉴 → **Secrets and variables** → **Actions**
3. **"New repository secret"** 클릭
4. `GCP_SA_KEY` 등록:
   - Name: `GCP_SA_KEY`
   - Secret: `gcp-sa-key.json` 파일 내용 전체를 복사해서 붙여넣기
5. `GCP_PROJECT_ID` 등록:
   - Name: `GCP_PROJECT_ID`
   - Secret: GCP 프로젝트 ID (예: `fittrack-analysis-yourname`)

> ⚠️ **JSON 키 복사 시 주의**: 파일 내용 전체를 복사하되, 앞뒤에 따옴표나 줄바꿈이 추가되지 않도록 합니다.
> CLI 방식(`gh secret set GCP_SA_KEY < ./gcp-sa-key.json`)이 더 안전합니다.

---

## 10. 최종 검증

모든 설정이 완료되면 아래 스크립트로 전체를 검증합니다.

```bash
# ─────────────────────────────────────────────
# BigQuery 환경 설정 검증 스크립트
# 실행: bash <(cat 이 스크립트 내용)
# ─────────────────────────────────────────────

echo "=== 1. gcloud 인증 확인 ==="
gcloud auth list 2>/dev/null | grep "^\*" || echo "❌ 인증 안 됨 — gcloud auth login 실행 필요"

echo ""
echo "=== 2. 프로젝트 설정 확인 ==="
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ -n "$CURRENT_PROJECT" ]; then
  echo "✅ 현재 프로젝트: $CURRENT_PROJECT"
else
  echo "❌ 프로젝트 미설정 — gcloud config set project <PROJECT_ID> 실행 필요"
fi

echo ""
echo "=== 3. BigQuery API 활성화 확인 ==="
BQ_API=$(gcloud services list --enabled --filter="name:bigquery.googleapis.com" --format="value(name)" 2>/dev/null)
if [ -n "$BQ_API" ]; then
  echo "✅ BigQuery API 활성화됨"
else
  echo "❌ BigQuery API 비활성화 — gcloud services enable bigquery.googleapis.com 실행 필요"
fi

echo ""
echo "=== 4. 데이터셋 목록 확인 ==="
bq ls --project_id=$CURRENT_PROJECT 2>/dev/null || echo "❌ 데이터셋 목록 조회 실패"

echo ""
echo "=== 5. 서비스 계정 JSON 키 확인 ==="
if [ -f "./gcp-sa-key.json" ]; then
  python3 -c "
import json
with open('./gcp-sa-key.json') as f:
    d = json.load(f)
print(f'✅ 프로젝트: {d[\"project_id\"]}')
print(f'✅ 서비스 계정: {d[\"client_email\"]}')
" 2>/dev/null || echo "❌ JSON 키 파일 형식 오류"
else
  echo "❌ gcp-sa-key.json 파일 없음"
fi

echo ""
echo "=== 6. 서비스 계정으로 BigQuery 쿼리 테스트 ==="
GOOGLE_APPLICATION_CREDENTIALS="./gcp-sa-key.json" \
bq query --use_legacy_sql=false --project_id=$CURRENT_PROJECT \
  "SELECT 'BigQuery 연결 성공' AS status, CURRENT_TIMESTAMP() AS verified_at" \
  2>/dev/null || echo "❌ 쿼리 실패 — IAM 권한 또는 키 파일 확인 필요"

echo ""
echo "=== 7. GitHub Secret 확인 ==="
gh secret list 2>/dev/null | grep -E "GCP_SA_KEY|GCP_PROJECT_ID" \
  || echo "❌ GitHub Secret 미등록 또는 gh CLI 로그인 필요"

echo ""
echo "=== 검증 완료 ==="
```

**모든 항목이 ✅이면 설정 완료입니다.** ❌가 있으면 해당 단계로 돌아가 수정하세요.

### 10.1 dbt 연결 테스트

```bash
# profiles.yml 기반 BigQuery 연결 테스트
dbt debug

# 예상 출력 (성공)
# Connection test: OK connection ok
```

`Connection test: OK`가 표시되면 dbt → BigQuery 연결이 완료된 것입니다.

---

## 11. 비용 관리

### 11.1 BigQuery on-demand 요금 구조

| 항목 | 요금 | 비고 |
|------|------|------|
| 쿼리 처리량 | $5.00 / TB | 매월 첫 1TB 무료 |
| 활성 스토리지 | $0.02 / GB·월 | 최근 90일 수정된 데이터 |
| 장기 스토리지 | $0.01 / GB·월 | 90일 이상 수정되지 않은 데이터 |

**이 코스의 예상 비용**: 합성 데이터 약 500MB, 쿼리 처리량 월 수십 GB → **무료 티어 이내**

### 11.2 예산 알림 설정

```bash
# 결제 계정 ID 확인
BILLING_ACCOUNT=$(gcloud billing accounts list \
  --format="value(name)" --filter="open=true" | head -1)

# $10 초과 시 알림 설정 (학습자 개인 계정용)
gcloud beta billing budgets create \
  --billing-account=$BILLING_ACCOUNT \
  --display-name="FitTrack Course Budget" \
  --budget-amount=10USD \
  --threshold-rule=percent=0.5 \
  --threshold-rule=percent=0.9 \
  --threshold-rule=percent=1.0
```

### 11.3 쿼리 비용 사전 확인 (dry-run)

쿼리 실행 전 처리할 데이터 양을 미리 확인할 수 있습니다:

```bash
# dry-run 모드로 비용 추정
bq query --use_legacy_sql=false --dry_run "
SELECT COUNT(*) FROM \`${GCP_PROJECT_ID}.raw.raw_events\`
"
# 출력 예: "Query will process 52428800 bytes."
# 50MB → $0.0003 미만 (1TB당 $5 기준)
```

> **모듈 2에서 자동화**: 코스의 `bq-cost-guard` 훅이 Claude Code가 실행하는
> 모든 쿼리에 대해 dry-run 비용 추정을 자동으로 수행합니다.

### 11.4 비용 절감 팁

```sql
-- 권장: 파티션 컬럼 필터로 스캔 범위 제한
SELECT *
FROM `project.raw.raw_events`
WHERE event_date BETWEEN '2026-01-01' AND '2026-03-31'  -- 파티션 프루닝 적용
LIMIT 1000;

-- 비권장: 전체 테이블 스캔
SELECT *
FROM `project.raw.raw_events`;  -- 500MB 전체 스캔 발생
```

```sql
-- 권장: 필요한 컬럼만 SELECT
SELECT user_id, event_type, event_date
FROM `project.raw.raw_events`
WHERE event_date = '2026-03-01';

-- 비권장: SELECT *는 모든 컬럼을 스캔
SELECT *
FROM `project.raw.raw_events`
WHERE event_date = '2026-03-01';
```

---

## 12. 문제 해결

### 12.1 자주 발생하는 오류

#### `gcloud: command not found`

```bash
# gcloud가 PATH에 없는 경우
# Homebrew 설치 시 셸 재시작 필요
exec -l $SHELL  # 또는 새 터미널 창 열기

# 직접 경로 추가 (zsh 기준)
echo 'source "$(brew --prefix)/share/google-cloud-sdk/path.zsh.inc"' >> ~/.zshrc
source ~/.zshrc
```

---

#### `ERROR: (gcloud.projects.create) Resource in projects ... already exists`

프로젝트 ID가 이미 존재합니다. 다른 고유한 ID를 사용하세요:

```bash
# 고유한 ID 생성 예시
export GCP_PROJECT_ID="fittrack-analysis-$(date +%s | tail -c 6)"
echo $GCP_PROJECT_ID
# 예: fittrack-analysis-423456
```

---

#### `BigQuery: Access Denied` (`dbt run` 실패 시)

서비스 계정에 필요한 IAM 역할이 없습니다:

```bash
# 현재 서비스 계정의 IAM 역할 확인
gcloud projects get-iam-policy $GCP_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:$SA_EMAIL" \
  --format="table(bindings.role)"

# 역할 재부여
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/bigquery.jobUser"
```

---

#### `dbt debug: Connection test: ERROR`

```bash
# 1. profiles.yml 경로 확인
cat ~/.dbt/profiles.yml

# 2. 서비스 계정 키 파일 경로 확인
# profiles.yml에서 keyfile 경로가 절대 경로인지 확인
# 예: /Users/username/projects/fittrack-analysis/gcp-sa-key.json

# 3. 환경변수로 인증
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/gcp-sa-key.json"
dbt debug
```

---

#### GitHub Actions에서 `google.auth.exceptions.DefaultCredentialsError`

```bash
# Secret 값 확인 (이름만 표시됨)
gh secret list

# GCP_SA_KEY가 올바른 JSON 형식인지 확인
# 잘못된 형식: Secret 값에 따옴표나 줄바꿈이 포함된 경우

# 재등록 (파일에서 직접 읽어서 등록 — 권장)
gh secret set GCP_SA_KEY < ./gcp-sa-key.json
```

---

#### `ERROR: (bq) Dataset already exists`

```bash
# 데이터셋이 이미 존재하는지 확인
bq ls --project_id=$GCP_PROJECT_ID

# 이미 있으면 생성 단계를 건너뛰어도 됩니다
```

---

### 12.2 GCP 프로젝트 정리 (코스 종료 후)

코스 완료 후 불필요한 과금을 방지하려면 리소스를 정리하세요:

```bash
# 데이터셋 삭제 (테이블 포함)
bq rm -r -f --dataset ${GCP_PROJECT_ID}:raw
bq rm -r -f --dataset ${GCP_PROJECT_ID}:dbt_dev
bq rm -r -f --dataset ${GCP_PROJECT_ID}:dbt_ci

# 서비스 계정 키 삭제
KEY_ID=$(cat gcp-sa-key.json | python3 -c "import sys,json; print(json.load(sys.stdin)['private_key_id'])")
gcloud iam service-accounts keys delete $KEY_ID \
  --iam-account=$SA_EMAIL \
  --project=$GCP_PROJECT_ID

# 서비스 계정 삭제
gcloud iam service-accounts delete $SA_EMAIL \
  --project=$GCP_PROJECT_ID

# 로컬 키 파일 삭제
rm -f ./gcp-sa-key.json

# (선택) 전체 프로젝트 삭제 (복구 불가)
# gcloud projects delete $GCP_PROJECT_ID
```

---

## 부록: 전체 설정 요약 스크립트

처음부터 모든 설정을 자동으로 진행하는 스크립트입니다.

```bash
#!/usr/bin/env bash
# setup-gcp.sh — GCP/BigQuery 환경 자동 설정
# 사용법: GCP_PROJECT_ID=fittrack-analysis-yourname bash setup-gcp.sh

set -euo pipefail

# ── 변수 설정 ───────────────────────────────
PROJECT_ID="${GCP_PROJECT_ID:-fittrack-analysis-$(whoami | tr -d '.' | head -c 8)}"
SA_NAME="fittrack-analyst"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
DATASET_LOCATION="US"

echo "=== GCP/BigQuery 환경 설정 시작 ==="
echo "프로젝트 ID: $PROJECT_ID"
echo "서비스 계정: $SA_EMAIL"
echo ""

# ── 1. gcloud 인증 확인 ─────────────────────
echo "[1/7] gcloud 인증 확인..."
if ! gcloud auth list 2>/dev/null | grep -q "^\*"; then
  echo "gcloud 로그인이 필요합니다."
  gcloud auth login
  gcloud auth application-default login
fi

# ── 2. 프로젝트 생성 ────────────────────────
echo "[2/7] GCP 프로젝트 생성..."
if ! gcloud projects describe $PROJECT_ID &>/dev/null; then
  gcloud projects create $PROJECT_ID --name="FitTrack Analysis"
  echo "✅ 프로젝트 생성됨: $PROJECT_ID"
else
  echo "ℹ️  프로젝트 이미 존재함: $PROJECT_ID"
fi
gcloud config set project $PROJECT_ID

# ── 3. BigQuery API 활성화 ──────────────────
echo "[3/7] BigQuery API 활성화..."
gcloud services enable bigquery.googleapis.com --project=$PROJECT_ID
echo "✅ BigQuery API 활성화"

# ── 4. 데이터셋 생성 ────────────────────────
echo "[4/7] BigQuery 데이터셋 생성..."
for DATASET in raw dbt_dev dbt_ci; do
  if ! bq ls --project_id=$PROJECT_ID | grep -q "$DATASET"; then
    bq mk --dataset --location=$DATASET_LOCATION ${PROJECT_ID}:${DATASET}
    echo "✅ 데이터셋 생성됨: $DATASET"
  else
    echo "ℹ️  데이터셋 이미 존재함: $DATASET"
  fi
done

# ── 5. 서비스 계정 생성 ─────────────────────
echo "[5/7] 서비스 계정 생성..."
if ! gcloud iam service-accounts describe $SA_EMAIL \
    --project=$PROJECT_ID &>/dev/null; then
  gcloud iam service-accounts create $SA_NAME \
    --display-name="FitTrack Analysis Service Account" \
    --project=$PROJECT_ID
  echo "✅ 서비스 계정 생성됨: $SA_EMAIL"
else
  echo "ℹ️  서비스 계정 이미 존재함: $SA_EMAIL"
fi

# ── 6. IAM 역할 부여 ────────────────────────
echo "[6/7] IAM 역할 부여..."
for ROLE in roles/bigquery.dataEditor roles/bigquery.jobUser; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="$ROLE" \
    --quiet
  echo "✅ 역할 부여됨: $ROLE"
done

# ── 7. 서비스 계정 키 생성 ──────────────────
echo "[7/7] 서비스 계정 JSON 키 생성..."
if [ ! -f "./gcp-sa-key.json" ]; then
  gcloud iam service-accounts keys create ./gcp-sa-key.json \
    --iam-account=$SA_EMAIL \
    --project=$PROJECT_ID
  echo "✅ 키 파일 생성됨: ./gcp-sa-key.json"
else
  echo "ℹ️  키 파일 이미 존재함: ./gcp-sa-key.json"
fi

echo ""
echo "=== GCP/BigQuery 환경 설정 완료 ==="
echo ""
echo "다음 단계: GitHub Secret 등록"
echo "  gh secret set GCP_SA_KEY < ./gcp-sa-key.json"
echo "  gh secret set GCP_PROJECT_ID --body \"$PROJECT_ID\""
echo ""
echo "⚠️  gcp-sa-key.json 파일을 Git에 커밋하지 마세요!"
```

사용법:

```bash
# 직접 실행
GCP_PROJECT_ID="fittrack-analysis-mkim" bash setup-gcp.sh

# 또는 scripts/ 디렉토리에 저장 후 실행
chmod +x scripts/setup-gcp.sh
GCP_PROJECT_ID="fittrack-analysis-mkim" ./scripts/setup-gcp.sh
```

---

*이 가이드는 "하니스 엔지니어링 for 데이터 분석" 코스의 일부입니다.*
*문제 발생 시 코스 강사 또는 GitHub Issue를 통해 문의하세요.*

# /validate — 모듈 0 완료 검증

모듈 0의 설정 상태를 검증합니다. **자동 검증 스크립트를 실행**하고 결과를 한국어로 보고하세요.

## 실행 방법

### 1단계: 자동 검증 스크립트 실행

```bash
bash scripts/validate.sh
```

스크립트가 다음 9개 항목을 **실제 기능 테스트**로 검증합니다 (파일 존재 확인이 아닌 실행 결과 검증):

| # | 항목 | 기능 검증 내용 |
|---|------|---------------|
| 0 | 환경 변수 | `.env` 파일의 `GCP_PROJECT_ID`와 `GOOGLE_APPLICATION_CREDENTIALS` 값 존재 + 인증 파일 경로 실제 접근 가능 여부 |
| 1 | Claude Code CLI | `claude --version` 실행하여 CLI 바이너리 동작 확인 |
| 2 | Claude Code 인증 | `claude whoami` 실행하여 인증 세션 활성 상태 확인 |
| 3 | uv 패키지 매니저 | `uv --version` 실행하여 패키지 매니저 동작 확인 |
| 4 | dbt 설치 상태 | `uv run dbt --version` 실행 — dbt-core 출력 + bigquery 어댑터 문자열 확인 |
| 5 | marimo 설치 상태 | `uv run marimo --version` 실행 — 버전 번호 출력 확인 (선택 사항) |
| 6 | GitHub Secrets | `gh secret list` 실행 — GCP_SA_KEY, GCP_PROJECT_ID, CLAUDE_TOKEN, GITHUB_PAT 4개 등록 확인 |
| 7 | BigQuery 데이터 | `bq query` 실행하여 raw_events ≥ 50만 건, raw_users ≥ 1만 건 실제 행 수 조회 |
| 8 | dbt 모델 빌드/테스트 | `dbt run` + `dbt test` 실행하여 전체 파이프라인 종료 코드 0 확인 |

### 2단계: 결과 해석 및 보고

스크립트 출력을 그대로 사용자에게 보여주세요. 추가로:

- ❌ 항목이 있으면: 각 실패 항목별 **구체적인 해결 방법**을 안내
  - 환경 변수: `.env.example`을 `.env`로 복사하고 값 입력 안내
  - CLI 도구: 설치 명령어 안내
  - GitHub Secrets: `gh secret set` 명령어 안내
  - BigQuery 데이터: 합성 데이터 생성 스크립트 작성 및 실행 안내
  - dbt: `profiles.yml` 생성 또는 모델 파일 작성 안내
- ⚠️ 항목만 있으면: 경고 내용과 선택적 해결 방법 안내
- 모든 항목 ✅이면: "🎉 모듈 0 완료! 모듈 1(훅 설정)로 진행할 준비가 되었습니다."

### 3단계: 스크립트 실행 불가 시 수동 검증

스크립트를 실행할 수 없는 경우, 아래 명령어를 **직접 실행**하여 각 항목의 기능을 검증하세요:

```bash
# 0. 환경 변수 — 파일 존재 + 값 설정 + 경로 유효
test -f .env && grep -q "GCP_PROJECT_ID=" .env && grep -q "GOOGLE_APPLICATION_CREDENTIALS=" .env

# 1. Claude Code CLI — 바이너리 동작
claude --version

# 2. Claude Code 인증 — 세션 활성
claude whoami

# 3. uv — 바이너리 동작
uv --version

# 4. dbt — dbt-core + bigquery 어댑터
uv run dbt --version

# 5. marimo (선택) — 버전 출력
uv run marimo --version

# 6. GitHub Secrets — 4개 시크릿 등록
gh secret list

# 7. BigQuery — 실제 행 수 조회
bq query --nouse_legacy_sql "SELECT COUNT(*) FROM \`$GCP_PROJECT_ID.$BQ_DATASET_RAW.raw_events\`"

# 8. dbt 파이프라인 — 빌드 + 테스트 성공
uv run dbt run && uv run dbt test
```

결과를 아래 형식으로 정리하세요:

```
## 모듈 0 검증 결과

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 0 | 환경 변수 | ✅/❌ | ... |
| ... | ... | ... | ... |

총 N/9 항목 통과
```

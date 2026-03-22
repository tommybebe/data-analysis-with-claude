# /setup-harness — 하니스 환경 초기화

새 데이터 분석 프로젝트에서 Claude Code 하니스를 처음 설정합니다.
필수 디렉토리, 권한, git 훅을 자동으로 구성합니다.

## 입력

- `$ARGUMENTS` (선택): 프로젝트 설정 옵션
  - `--skip-git-hooks`: git pre-commit 훅 설치 생략
  - `--bq-limit-gb=N`: BigQuery 비용 한도를 N GB로 설정 (기본값: 1)

## 실행 절차

### 1단계: 디렉토리 구조 생성
```bash
mkdir -p .claude/commands .claude/hooks .claude/logs
mkdir -p notebooks reports evidence
```

### 2단계: 훅 스크립트 실행 권한 부여
```bash
chmod +x .claude/hooks/*.sh
```

### 3단계: git pre-commit 훅 설치 (선택)
`--skip-git-hooks`가 없는 경우:
```bash
cp .claude/hooks/pre-commit-dbt-check.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### 4단계: .gitignore 설정 확인
다음 항목이 `.gitignore`에 포함되어 있는지 확인:
```
reports/          # HTML 리포트 (GitHub Actions 아티팩트로 업로드)
.env              # 환경 변수 (API 키 등)
target/           # dbt 빌드 결과물
.claude/logs/     # 쿼리 비용 로그
```

포함되지 않은 항목은 자동으로 추가.

### 5단계: 환경 변수 확인
필수 환경 변수가 설정되어 있는지 점검:

| 변수 | 설명 | 확인 방법 |
|------|------|----------|
| `BQ_PROJECT_ID` | BigQuery 프로젝트 ID | `echo $BQ_PROJECT_ID` |
| `GOOGLE_APPLICATION_CREDENTIALS` | GCP 서비스 계정 키 경로 | `test -f "$GOOGLE_APPLICATION_CREDENTIALS"` |

누락된 변수는 설정 방법을 안내.

### 6단계: dbt 연결 테스트
```bash
dbt debug --target dev
```

### 7단계: 설정 요약 출력

## 출력 형식

```
## 하니스 초기화 완료

### 생성된 디렉토리
- 📁 .claude/commands/ (슬래시 커맨드)
- 📁 .claude/hooks/ (훅 스크립트)
- 📁 .claude/logs/ (쿼리 비용 로그)
- 📁 notebooks/ (marimo 노트북)
- 📁 reports/ (HTML 리포트 - gitignore됨)
- 📁 evidence/ (완료 증거)

### 훅 상태
- ✅ bq-cost-guard.sh (실행 권한 설정됨)
- ✅ dbt-auto-test.sh (실행 권한 설정됨)
- ✅ marimo-check.sh (실행 권한 설정됨)
- ✅ query-logger.sh (실행 권한 설정됨)
- ✅ stop-summary.sh (실행 권한 설정됨)
- ✅ pre-commit-dbt-check.sh → .git/hooks/pre-commit

### 환경 변수
- ✅ BQ_PROJECT_ID: your-project-id
- ✅ GOOGLE_APPLICATION_CREDENTIALS: ~/.config/gcp/sa-key.json

### BigQuery 비용 한도
- 단일 쿼리 한도: 1 GB (변경: export BQ_COST_LIMIT_BYTES=N)

### 다음 단계
1. `uv sync` — Python 의존성 설치
2. `uv run dbt deps` — dbt 패키지 설치
3. `uv run dbt build --target dev` — 전체 빌드 확인
4. `/analyze #1` — 첫 번째 분석 시작
```

## 완료 증거

- [ ] `.claude/hooks/` 디렉토리의 모든 `.sh` 파일에 실행 권한 있음
- [ ] `.gitignore`에 `reports/`, `.env`, `target/` 포함됨
- [ ] `dbt debug` 가 성공 또는 누락된 설정이 문서화됨

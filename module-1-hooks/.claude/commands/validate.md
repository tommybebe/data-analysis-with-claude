# /validate — 모듈 1 완료 검증

모듈 1의 훅 설정 상태를 검증합니다. **자동 검증 스크립트를 실행**하고 결과를 한국어로 보고하세요.

## 실행 방법

### 1단계: 자동 검증 스크립트 실행

```bash
bash scripts/validate.sh
```

스크립트가 다음 7개 항목을 **실제 기능 테스트**로 검증합니다 (파일 존재 확인이 아닌 동작 검증):

| # | 항목 | 기능 검증 내용 |
|---|------|---------------|
| 0 | settings.json 구조 | `python -m json.tool`로 JSON 파싱 + Python으로 `hooks`와 `permissions` 키 존재 확인 |
| 1 | 훅 스크립트 실행 권한 | bq-cost-guard.sh, dbt-auto-test.sh, stop-summary.sh — 3개 파일 `-x` 퍼미션 비트 확인 |
| 2 | 비용 가드 차단 동작 | `BQ_COST_LIMIT_BYTES=1`로 설정 후 bq-cost-guard.sh에 테스트 JSON 입력 → **exit code ≠ 0** 확인 (실제 차단 동작) |
| 3 | dbt 오류 감지 훅 | 잘못된 SQL 파일(`SELEC * FORM broken`)을 생성 후 dbt-auto-test.sh 실행 → **오류 감지** 확인 (exit code 또는 에러 메시지) |
| 4 | permissions.deny 규칙 | JSON 파싱 후 `deny` 배열에 `git push --force`, `bq rm`, `dbt run --full-refresh`, `rm -rf` 4개 패턴 포함 확인 |
| 5 | 회고 기록 | evidence/module-1-retrospective.md 존재 및 50바이트 이상 내용 작성 확인 |
| 6 | 환경 변수 | `.env` 파일 존재 + `GCP_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS` 값 설정 + 인증 파일 경로 접근 가능 여부 |

### 2단계: 결과 해석 및 보고

스크립트 출력을 그대로 사용자에게 보여주세요. 추가로:

- ❌ 항목이 있으면: 각 실패 항목별 **구체적인 해결 방법**을 안내
  - settings.json: JSON 문법 오류 위치 안내 (trailing comma, 따옴표 확인)
  - 훅 실행 권한: `chmod +x .claude/hooks/*.sh` 안내
  - 비용 가드: `BQ_COST_LIMIT_BYTES` 환경 변수와 dry-run 비용 비교 로직 확인 안내
  - dbt 훅: profiles.yml 설정 상태 확인, dbt compile 경로 확인 안내
  - deny 규칙: 누락된 패턴을 settings.json의 permissions.deny에 추가 안내
  - 회고: 훅 vs permissions 비교 분석 작성 안내
  - 환경 변수: `.env.example`을 `.env`로 복사하고 `GCP_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS` 값 입력 안내
- ⚠️ 항목만 있으면: 경고 내용과 선택적 해결 방법 안내
- 모든 항목 ✅이면: "🎉 모듈 1 완료! 모듈 2(슬래시 커맨드)로 진행하세요."

### 3단계: 스크립트 실행 불가 시 수동 검증

스크립트를 실행할 수 없는 경우, 아래 명령어를 **직접 실행**하여 각 항목을 검증하세요:

```bash
# 0. settings.json — JSON 유효성 + 필수 키
python3 -m json.tool .claude/settings.json && \
python3 -c "import json; d=json.load(open('.claude/settings.json')); assert 'hooks' in d and 'permissions' in d"

# 1. 훅 스크립트 실행 권한
test -x .claude/hooks/bq-cost-guard.sh && \
test -x .claude/hooks/dbt-auto-test.sh && \
test -x .claude/hooks/stop-summary.sh

# 2. 비용 가드 — 실제 차단 동작 테스트
echo '{"tool_name":"Bash","tool_input":{"command":"bq query --use_legacy_sql=false \"SELECT 1\""}}' \
  | BQ_COST_LIMIT_BYTES=1 bash .claude/hooks/bq-cost-guard.sh
# exit code가 1(비정상)이어야 합격

# 3. dbt 오류 감지 — 잘못된 SQL 감지 테스트
echo "SELEC * FORM broken" > models/marts/_test_broken.sql
echo '{"tool_name":"Write","tool_input":{"file_path":"models/marts/_test_broken.sql"}}' \
  | bash .claude/hooks/dbt-auto-test.sh
rm -f models/marts/_test_broken.sql
# exit code가 1(비정상) 또는 에러 메시지 출력이어야 합격

# 4. permissions.deny — 필수 차단 패턴 존재
python3 -c "
import json; d=json.load(open('.claude/settings.json'))
deny=d.get('permissions',{}).get('deny',[])
for p in ['git push --force','bq rm','dbt run --full-refresh','rm -rf']:
    assert any(p in i for i in deny), f'Missing: {p}'
print('All deny patterns found')
"

# 5. 회고 기록
test -f evidence/module-1-retrospective.md && \
[ $(wc -c < evidence/module-1-retrospective.md) -gt 50 ]
```

결과를 아래 형식으로 정리하세요:

```
## 모듈 1 검증 결과

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 0 | settings.json 구조 | ✅/❌ | ... |
| ... | ... | ... | ... |

총 N/7 항목 통과
```

#### 6. 환경 변수 수동 확인

```bash
# .env 파일 존재 + 필수 변수 값 확인
test -f .env && grep -q "GCP_PROJECT_ID=" .env && grep -q "GOOGLE_APPLICATION_CREDENTIALS=" .env
```

# /validate — 모듈 3 완료 검증

모듈 3의 권한 오케스트레이션 설정 상태를 검증합니다. **자동 검증 스크립트를 실행**하고 결과를 한국어로 보고하세요.

## 실행 방법

### 1단계: 자동 검증 스크립트 실행

```bash
bash scripts/validate.sh
```

스크립트가 다음 6개 항목을 **실제 기능 테스트**로 검증합니다 (파일 존재 확인이 아닌 동작/내용 검증):

| # | 항목 | 기능 검증 내용 |
|---|------|---------------|
| 0 | 권한 규칙 수량 | `settings.json` JSON 파싱 → `permissions.allow` ≥ 3개, `permissions.deny` ≥ 3개 실제 카운트 |
| 1 | 필수 deny 규칙 | Python으로 deny 배열 파싱 → `git push --force`, `bq rm`, `rm -rf` 3개 패턴 포함 여부 확인 |
| 2 | GitHub Actions 워크플로 | `auto-analyze.yml` 존재 + `permissions:` 섹션 + `issues: write` + `contents: write` 키워드 확인 |
| 3 | 권한 설계 근거 문서 | `evidence/module-3-permissions-rationale.md` — 로컬/CI/GitHub Actions 키워드 2개 이상 포함 확인 |
| 4 | 회고 기록 | `evidence/module-3-permissions-retrospective.md` 존재 및 50바이트 이상 내용 작성 확인 |
| 5 | 환경 변수 | `.env` 파일 존재 + `GCP_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS`, `GITHUB_REPOSITORY` 값 설정 + 인증 파일 경로 접근 가능 여부 |

### 2단계: 결과 해석 및 보고

스크립트 출력을 그대로 사용자에게 보여주세요. 추가로:

- ❌ 항목이 있으면: 각 실패 항목별 **구체적인 해결 방법**을 안내
  - 권한 규칙 수량: `settings.json`의 `permissions.allow`/`permissions.deny` 배열에 규칙 추가 (각 최소 3개)
  - 필수 deny 규칙: 누락된 패턴을 deny 목록에 추가하는 예시 — `"git push --force"`, `"bq rm"`, `"rm -rf"`
  - 워크플로: `.github/workflows/auto-analyze.yml` 생성 및 `permissions:` 섹션에 `issues: write`, `contents: write` 추가
  - 설계 근거: 로컬 실행과 CI 실행의 권한 차이를 분석하는 문서 작성 (왜 다르게 설계해야 하는가?)
  - 회고: 권한 정책 설계 과정의 판단 기준과 로컬/CI 차이 분석 작성
  - 환경 변수: `.env.example`을 `.env`로 복사하고 `GCP_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS`, `GITHUB_REPOSITORY` 값 입력 안내
- ⚠️ 항목만 있으면: 경고 내용과 선택적 해결 방법 안내
- 모든 항목 ✅이면: "🎉 모듈 3 완료! 모듈 4(종단간 통합)로 진행하세요."

### 3단계: 스크립트 실행 불가 시 수동 검증

스크립트를 실행할 수 없는 경우, 아래 명령어를 **직접 실행**하여 각 항목을 검증하세요:

```bash
# 0. 권한 규칙 수량 — JSON 파싱 후 allow/deny 배열 길이 확인
python3 -c "
import json; d=json.load(open('.claude/settings.json'))
p = d.get('permissions', {})
allow_n = len(p.get('allow', []))
deny_n = len(p.get('deny', []))
assert allow_n >= 3 and deny_n >= 3, f'allow: {allow_n}, deny: {deny_n} (각 3 이상 필요)'
print(f'allow: {allow_n}개, deny: {deny_n}개 — 통과')
"

# 1. 필수 deny 규칙 — 3개 패턴 포함 확인
python3 -c "
import json; d=json.load(open('.claude/settings.json'))
deny = d.get('permissions', {}).get('deny', [])
for p in ['git push --force', 'bq rm', 'rm -rf']:
    assert any(p in item for item in deny), f'Missing: {p}'
print('All required deny patterns found')
"

# 2. GitHub Actions 워크플로 — 파일 존재 + permissions 섹션
test -f .github/workflows/auto-analyze.yml || echo "❌ auto-analyze.yml 없음"
grep -q 'permissions:' .github/workflows/auto-analyze.yml || echo "❌ permissions: 섹션 없음"
grep -q 'issues: write' .github/workflows/auto-analyze.yml || echo "❌ issues: write 없음"
grep -q 'contents: write' .github/workflows/auto-analyze.yml || echo "❌ contents: write 없음"

# 3. 권한 설계 근거 문서 — 로컬/CI 비교 키워드 확인
python3 -c "
t = open('evidence/module-3-permissions-rationale.md').read()
keywords = ['로컬', 'CI', 'GitHub Actions']
count = sum(1 for k in keywords if k in t)
assert count >= 2, f'키워드 {count}개 (최소 2개 필요: 로컬, CI, GitHub Actions)'
print(f'키워드 {count}개 포함 — 통과')
"

# 4. 회고 기록
test -f evidence/module-3-permissions-retrospective.md && \
[ $(wc -c < evidence/module-3-permissions-retrospective.md) -gt 50 ] && \
echo "✅ 회고 작성 완료" || echo "❌ 회고 없거나 내용 부족"
```

결과를 아래 형식으로 정리하세요:

```
## 모듈 3 검증 결과

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 0 | 권한 규칙 수량 | ✅/❌ | ... |
| ... | ... | ... | ... |

총 N/6 항목 통과
```

#### 5. 환경 변수 수동 확인

```bash
# .env 파일 존재 + 필수 변수 값 확인
test -f .env && grep -q "GCP_PROJECT_ID=" .env && \
  grep -q "GOOGLE_APPLICATION_CREDENTIALS=" .env && \
  grep -q "GITHUB_REPOSITORY=" .env
```

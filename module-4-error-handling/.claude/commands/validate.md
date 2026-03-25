# /validate — 모듈 4 완료 검증

모듈 4의 종단간 통합 상태를 검증합니다. **자동 검증 스크립트를 실행**하고 결과를 한국어로 보고하세요.

## 실행 방법

### 1단계: 자동 검증 스크립트 실행

```bash
bash scripts/validate.sh
```

스크립트가 다음 8개 항목을 자동으로 검증합니다:

| # | 항목 | 검증 내용 |
|---|------|-----------|
| 0 | 워크플로 YAML | auto-analyze.yml YAML 문법 유효성, issues labeled 트리거 + permissions 키 |
| 1 | 7단계 라벨 분기 | stage:1-parse ~ stage:7-report — 7개 단계 라벨 모두 YAML에 참조 |
| 2 | 오류 처리 로직 | stage:error 라벨 처리 + error-category 키워드 존재 |
| 3 | 프롬프트 파일 7개 | .claude/prompts/ 디렉터리에 stage-1-parse.md ~ stage-7-report.md 존재 |
| 4 | stage-5 프롬프트 내용 | 비용 제한(1GB), dbt 참조, BigQuery 참조 포함 여부 |
| 5 | 하니스 통합 점검 | 훅 3개 + 권한 정책(allow≥3, deny≥3) + 슬래시 커맨드 4개 + dbt 모델 존재 |
| 6 | 회고 기록 | evidence/module-4-retrospective.md — 하니스/파이프라인/비용 관련 내용 포함 |
| 7 | 환경 변수 | `.env` 파일 존재 + `GCP_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS`, `GITHUB_REPOSITORY` 값 설정 + 인증 파일 경로 접근 가능 여부 |

### 2단계: 결과 해석 및 보고

스크립트 출력을 그대로 사용자에게 보여주세요. 추가로:

- ❌ 항목이 있으면: 각 실패 항목별 **구체적인 해결 방법**을 안내
  - 워크플로 YAML: YAML 문법 오류 수정, issues labeled 트리거 및 permissions 추가 안내
  - 7단계 라벨: 누락된 단계 라벨을 워크플로 조건 분기에 추가 안내
  - 오류 처리: stage:error 라벨 처리 및 error-category 앵커 작성 안내
  - 프롬프트 파일: .claude/prompts/ 에 누락 파일 생성 안내
  - stage-5 내용: 1GB 비용 제한, dbt 테스트 통과 확인 제약 조건 추가 안내
  - 하니스 통합: 누락된 구성 요소(훅/권한/커맨드/모델) 복구 안내
  - 회고: 하니스 설계, 파이프라인 구조, 비용 관리 관점에서 분석 작성 안내
  - 환경 변수: `.env.example`을 `.env`로 복사하고 `GCP_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS`, `GITHUB_REPOSITORY` 값 입력 안내
- ⚠️ 항목만 있으면: 경고 내용과 선택적 해결 방법 안내
- 모든 항목 ✅이면: "🎉 모듈 4 완료! 코스 전체를 성공적으로 완료했습니다. 축하합니다!"

### 3단계: 스크립트 실행 불가 시 수동 검증

스크립트를 실행할 수 없는 경우, 아래 명령어를 **직접 실행**하여 각 항목을 검증하세요:

```bash
# 0. 워크플로 YAML — 존재 + YAML 유효성 + issues labeled 트리거 + permissions 키
python3 -c "
import yaml
t = open('.github/workflows/auto-analyze.yml').read()
yaml.safe_load(t)
assert 'labeled' in t, 'labeled 트리거 없음'
assert 'permissions:' in t, 'permissions 키 없음'
print('✅ YAML 유효, labeled 트리거 + permissions 확인')
"

# 1. 7단계 라벨 분기 — 7개 단계 라벨 모두 YAML에 참조
python3 -c "
t = open('.github/workflows/auto-analyze.yml').read()
stages = ['stage:1-parse','stage:2-define','stage:3-deliverables','stage:4-spec','stage:5-extract','stage:6-analyze','stage:7-report']
found = [s for s in stages if s in t]
missing = [s for s in stages if s not in t]
assert len(found) >= 7, f'{len(found)}/7 — 누락: {missing}'
print(f'✅ 7/7 단계 라벨 참조됨')
"

# 2. 오류 처리 로직 — stage:error + error-category 키워드
python3 -c "
t = open('.github/workflows/auto-analyze.yml').read()
assert 'stage:error' in t, 'stage:error 없음'
assert 'error-category' in t, 'error-category 없음'
print('✅ stage:error + error-category 포함')
"

# 3. 프롬프트 파일 7개 — .claude/prompts/ 디렉터리
python3 -c "
import os
prompts = [f'stage-{i}-{n}.md' for i,n in [(1,'parse'),(2,'define'),(3,'deliverables'),(4,'spec'),(5,'extract'),(6,'analyze'),(7,'report')]]
found = [p for p in prompts if os.path.isfile(f'.claude/prompts/{p}')]
missing = [p for p in prompts if p not in found]
assert len(found) >= 7, f'{len(found)}/7 — 누락: {missing}'
print(f'✅ 7/7 프롬프트 파일 존재')
"

# 4. stage-5 프롬프트 내용 — 비용 제한, dbt, BigQuery 참조
python3 -c "
t = open('.claude/prompts/stage-5-extract.md').read()
checks = [
    '1GB' in t or '1 GB' in t or 'cost' in t.lower(),
    'dbt' in t.lower(),
    'bigquery' in t.lower() or 'bq' in t.lower()
]
assert sum(checks) >= 3, f'필수 내용 {sum(checks)}/3개만 포함'
print('✅ 비용 제한, dbt, BigQuery 참조 모두 포함')
"

# 5. 하니스 통합 점검 — 훅 3개 + 권한 정책 + 커맨드 4개 + dbt 모델
python3 -c "
import json, os
checks = []
hooks = ['bq-cost-guard.sh', 'dbt-auto-test.sh', 'stop-summary.sh']
checks.append(('훅', all(os.path.isfile(f'.claude/hooks/{h}') for h in hooks)))
d = json.load(open('.claude/settings.json'))
p = d.get('permissions', {})
checks.append(('권한', len(p.get('allow',[])) >= 3 and len(p.get('deny',[])) >= 3))
cmds = ['analyze.md', 'check-cost.md', 'validate-models.md', 'generate-report.md']
checks.append(('커맨드', all(os.path.isfile(f'.claude/commands/{c}') for c in cmds)))
models = ['models/staging/stg_events.sql', 'models/staging/stg_users.sql', 'models/marts/fct_daily_active_users.sql']
checks.append(('dbt', all(os.path.isfile(m) for m in models)))
failed = [n for n, ok in checks if not ok]
assert not failed, f'실패: {failed}'
print('✅ 훅 + 권한 + 커맨드 + dbt 모델 모두 확인')
"

# 6. 회고 기록
python3 -c "
t = open('evidence/module-4-retrospective.md').read()
keywords = ['하니스', '파이프라인', '비용', 'pipeline', 'cost']
count = sum(1 for k in keywords if k in t)
assert count >= 2, f'키워드 {count}개 (최소 2개 필요: 하니스, 파이프라인, 비용)'
print(f'✅ 키워드 {count}개 포함')
"
```

결과를 아래 형식으로 정리하세요:

```
## 모듈 4 검증 결과

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 0 | 워크플로 YAML | ✅/❌ | ... |
| ... | ... | ... | ... |

총 N/8 항목 통과
```

#### 7. 환경 변수 수동 확인

```bash
# .env 파일 존재 + 필수 변수 값 확인
test -f .env && grep -q "GCP_PROJECT_ID=" .env && \
  grep -q "GOOGLE_APPLICATION_CREDENTIALS=" .env && \
  grep -q "GITHUB_REPOSITORY=" .env
```

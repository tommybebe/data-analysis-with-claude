# 단계 1: 이슈 파싱 (stage:1-parse)

GitHub Issue 본문을 파싱하여 후속 단계가 사용할 구조화된 요청 객체를 생성합니다.

## 컨텍스트

- 이전 단계 산출물: 없음 (파이프라인 진입점)
- 트리거: GitHub Issue에 `auto-analyze` 라벨 부착
- AGENTS.md 핵심 규약: 모든 산출물은 이슈 코멘트에 `<!-- stage:N-complete -->` 앵커와 함께 기록

## 작업 지시

1. 환경 변수에서 이슈 번호 획득: `$ISSUE_NUMBER` (GitHub Actions 컨텍스트에서 주입)
2. 이슈 본문 조회:
   ```bash
   gh issue view $ISSUE_NUMBER --json title,body,labels
   ```
3. 이슈 본문에서 다음 필드를 파싱하여 구조화된 JSON 객체 생성:
   - `metric`: 분석 대상 지표 (예: "DAU", "MAU", "retention")
   - `period`: 분석 기간 (예: "2026-01", "2026-Q1", "2026-01-01~2026-01-31")
   - `breakdown`: 세분화 기준 (예: "platform", "cohort", null)
   - `business_question`: 이슈 본문의 비즈니스 질문 원문 (그대로 보존)
   - `raw_title`: 이슈 제목 원문
4. 파싱 결과를 `evidence/stage-1-parse-result.json`에 저장
5. 성공 기준 검증:
   - `metric` 필드가 "DAU", "MAU", "retention" 중 하나인지 확인
   - `period` 필드가 YYYY-MM, YYYY-QN, 또는 날짜 범위 형식인지 확인
   - `business_question` 필드가 비어 있지 않은지 확인
6. 이슈에 파싱 결과 코멘트 게시:
   ```bash
   gh issue comment $ISSUE_NUMBER --body "..."
   ```
7. 라벨 전환: `stage:1-parse` 제거 → `stage:2-define` 부착

## 산출물

- `evidence/stage-1-parse-result.json` — 구조화된 파싱 결과
  ```json
  {
    "metric": "DAU",
    "period": "2026-01",
    "breakdown": "platform",
    "business_question": "원문 그대로",
    "raw_title": "이슈 제목 원문"
  }
  ```
- 이슈 코멘트 형식:
  ```
  ## 단계 1 완료: 이슈 파싱 결과

  | 필드 | 값 |
  |------|----|
  | 지표 | DAU |
  | 기간 | 2026-01 |
  | 세분화 | platform |

  **비즈니스 질문**: (원문)

  <!-- stage:1-complete -->
  ```

## 제약 조건

- `business_question` 원문을 수정하거나 요약하지 말 것 — 단계 2에서 의도 보존에 사용
- 파싱 불가 시: `<!-- error-category: AGENT -->` 앵커와 함께 오류 코멘트 게시 후 중단
- 환경 변수 하드코딩 금지: `GCP_PROJECT_ID`, `GITHUB_REPOSITORY` 등
- 라벨 전환은 파싱 성공 후에만 수행

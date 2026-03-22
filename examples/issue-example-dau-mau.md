# GitHub Issue 예시: DAU/MAU 분석 요청 (작성 완료 상태)

> 이 파일은 `issue-template-analysis-request.yml` 템플릿으로 생성된 이슈의 완성 예시입니다.
> 수강생이 템플릿을 채웠을 때 실제로 생성되는 이슈 본문을 보여줍니다.
> 7단계 자동 워크플로의 `stage:1-parse` 단계에서 에이전트가 파싱하는 대상입니다.

---

**이슈 제목**: `[분석] 2026년 1분기 DAU/MAU 트렌드 분석`

**라벨**: `분석 요청`, `auto-analyze`

---

### 분석 제목

2026년 1분기 DAU/MAU 트렌드 분석

### 문제 정의 (Problem Statement)

FitTrack 앱의 2026년 1분기 DAU와 MAU 추이를 파악하고, DAU/MAU 비율(stickiness)의 변화를 플랫폼(iOS/Android)별로 비교하라.

이 분석 결과는 Q2 사용자 리텐션 전략 수립에 활용될 예정이다. 특히 Android 사용자의 stickiness가 iOS 대비 낮다는 가설을 검증하고자 한다.

### 기대 산출물 (Expected Deliverables)

- 일별 DAU 추이 차트 (라인 차트, 플랫폼별 색상 구분)
- 월별 MAU 추이 차트 (바 차트)
- DAU/MAU 비율 트렌드 (플랫폼별 라인 차트)
- 주요 발견 요약 (3~5문장)

### 분석 시작일

2026-01-01

### 분석 종료일

2026-03-31

### 주요 세그먼트

platform (iOS / Android)

### 추가 세그먼트 (선택사항)

_선택 안 함_

### 분석 유형

트렌드 분석 (시계열 추이)

### 우선순위

🟡 보통 (3영업일 이내)

### 추가 컨텍스트 (선택사항)

- 테스트 계정(user_id가 `test_`로 시작)은 분석에서 제외
- 주말 효과가 예상되므로 요일별 패턴도 함께 확인 부탁

### 메트릭 정의 확인

- [x] DAU = 해당 일자에 1회 이상 이벤트를 발생시킨 고유 사용자 수
- [x] MAU = 해당 월에 1회 이상 이벤트를 발생시킨 고유 사용자 수
- [x] Stickiness = DAU / MAU (일별 활성 사용자가 월별 활성 사용자에서 차지하는 비율)

---

## 워크플로 실행 흐름

이 이슈에 `auto-analyze` 라벨을 부착하면 다음 7단계가 자동으로 진행됩니다:

| 단계 | 라벨 | 에이전트 작업 | 산출물 |
|------|------|---------------|--------|
| 1 | `stage:1-parse` | 이슈 본문 파싱 | 구조화된 요청 객체 (JSON) |
| 2 | `stage:2-define` | 문제 정의 구체화 | 분석 범위, 제약 조건 문서 |
| 3 | `stage:3-deliverables` | 산출물 명세 | 차트/테이블 스펙 목록 |
| 4 | `stage:4-spec` | 기술 스펙 작성 | dbt 모델 + marimo 노트북 설계 |
| 5 | `stage:5-extract` | 데이터 추출 | dbt 모델 실행, 결과 검증 |
| 6 | `stage:6-analyze` | 분석 수행 | marimo 노트북 생성 및 실행 |
| 7 | `stage:7-report` | 리포트 생성 | HTML/PDF 리포트 + PR 생성 |

### stage:1-parse 파싱 결과 예시

에이전트가 이슈 본문을 파싱하면 다음과 같은 구조화된 객체를 이슈 코멘트에 기록합니다:

```json
{
  "analysis_title": "2026년 1분기 DAU/MAU 트렌드 분석",
  "problem_statement": "FitTrack 앱의 2026년 1분기 DAU와 MAU 추이를 파악하고, DAU/MAU 비율(stickiness)의 변화를 플랫폼(iOS/Android)별로 비교하라.",
  "deliverables": [
    {"type": "chart", "description": "일별 DAU 추이 차트", "chart_type": "line", "segment": "platform"},
    {"type": "chart", "description": "월별 MAU 추이 차트", "chart_type": "bar", "segment": null},
    {"type": "chart", "description": "DAU/MAU 비율 트렌드", "chart_type": "line", "segment": "platform"},
    {"type": "summary", "description": "주요 발견 요약", "length": "3~5문장"}
  ],
  "date_range": {
    "start": "2026-01-01",
    "end": "2026-03-31"
  },
  "segments": {
    "primary": "platform",
    "values": ["ios", "android"],
    "additional": null
  },
  "analysis_type": "trend",
  "priority": "normal",
  "exclusions": ["user_id LIKE 'test_%'"],
  "metrics": {
    "dau": "해당 일자에 1회 이상 이벤트를 발생시킨 고유 사용자 수",
    "mau": "해당 월에 1회 이상 이벤트를 발생시킨 고유 사용자 수",
    "stickiness": "DAU / MAU"
  }
}
```

> **참고**: 이 파싱 결과는 이슈 코멘트에 `<!-- stage:1-parse-output -->` 태그로 감싸져 기록되며,
> 다음 단계(`stage:2-define`)의 에이전트가 이 코멘트를 읽어 입력으로 사용합니다.

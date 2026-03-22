# AGENTS.md

## 프로젝트 개요

**하니스 엔지니어링 for 데이터 분석** 코스 레포지토리입니다.

Claude Code와 GitHub Actions를 활용한 에이전트 기반 데이터 분석 자동화를 가르치는 코스로, 수강생이 스캐폴딩(scaffolding), 스킬/훅(skill/hook), 오케스트레이션(orchestration) 계층을 직접 구축하며 하니스 엔지니어링을 배웁니다.

샘플 프로젝트는 B2C 모바일 앱의 DAU/MAU 분석이며, BigQuery + dbt + marimo 노트북 기반 분석 워크플로를 사용합니다.

## 레포 구조

- `course-spec.md` — 코스 전체 명세 (모듈 요약 포함)
- `modules/` — 모듈별 상세 문서 (module-0.md ~ module-4.md)
- `examples/` — 실습 예제 파일 (Claude Code 설정, dbt 모델, marimo 노트북, GitHub Actions)
- `research/` — 하니스 엔지니어링 연구 노트
- `instructor-setup-guide.md` — 강사/자기학습자 환경 설정 가이드

## 문서 규약 (Documentation Conventions)

- **코스 문서**: 한국어로 작성
- **코드 변수/함수명**: 영어 사용
- **코드 주석 및 설명**: 한국어로 작성

## 편집 규칙 (Editing Rules)

- `course-spec.md`는 모듈 문서의 요약본입니다. 모듈 상세 내용(`modules/` 내 파일)을 변경할 경우 반드시 `course-spec.md`도 함께 동기화하세요.
- `examples/` 내 코드는 실제 실행 가능해야 합니다. 합성 데이터 기준으로 작성하세요.
- 모듈 1~4는 **관찰 → 수정 → 창작** 3단계 학습 사이클 구조를 따릅니다.
- 모듈 0은 환경 설정이므로 **개요 → 설치 → 개념 소개** 구조를 따릅니다.

## 금지 사항 (Prohibited)

- 프로덕션 데이터나 실제 API 키를 예제에 포함하지 마세요.
- 예제의 BigQuery 쿼리는 반드시 **on-demand 가격 모델** 기준으로 작성하세요. (flat-rate/edition 기반 쿼리 패턴 사용 금지)

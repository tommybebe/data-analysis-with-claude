# /generate-report — marimo 노트북 보고서 내보내기

Frozen snapshot from Module 2 output (prerequisite for Module 4).
marimo 노트북을 HTML 보고서로 내보내고 매니페스트를 기록합니다.

## Input
- `$ARGUMENTS`: 대상 노트북 경로 또는 패턴 (예: "analyses/analysis_dau_202601.py")

## Execution Steps
1. `$ARGUMENTS`로 대상 노트북 식별 (없으면 analyses/ 디렉터리 전체)
2. 각 노트북에 대해 marimo export 실행: `marimo export html [notebook.py] -o [output.html]`
3. 생성된 파일 목록 수집
4. evidence/report_manifest.json에 매니페스트 기록

## Output
- 생성된 HTML 보고서 파일
- `evidence/report_manifest.json` — 보고서 매니페스트

```json
{
  "timestamp": "2026-01-15T10:30:00+09:00",
  "outputs": [
    {
      "source": "analyses/analysis_dau_202601.py",
      "format": "html",
      "path": "analyses/analysis_dau_202601.html",
      "size_bytes": 45678
    }
  ],
  "total_reports": 1
}
```

## Constraints
- marimo export 사용 (marimo run이 아님)
- JSON에 outputs[].format, outputs[].path 필드 필수 포함
- 노트북이 존재하지 않으면 에러 메시지와 함께 중단

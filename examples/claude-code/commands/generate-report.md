# /generate-report — 리포트 생성 스킬

marimo 노트북을 HTML/PDF 정적 문서로 내보내고 결과를 검증합니다.

## 입력

- `$ARGUMENTS`: marimo 노트북 파일 경로 (예: `notebooks/analysis_42.py`)

## 실행 절차

1. **노트북 유효성 확인**: 파일 존재 여부, marimo 형식 확인
2. **HTML 내보내기**: `python -m marimo export html $ARGUMENTS -o reports/`
3. **PDF 내보내기** (선택): `python -m marimo export pdf $ARGUMENTS -o reports/`
4. **파일 크기 확인**: 생성된 파일이 비어있지 않은지 검증
5. **결과 요약**: 생성된 리포트 경로와 크기 보고

## 출력 경로 규약

```
reports/
├── analysis_<issue_number>.html    -- HTML 리포트
└── analysis_<issue_number>.pdf     -- PDF 리포트 (선택)
```

## 주의사항

- HTML/PDF 파일은 PR에 포함하지 않음 (`.gitignore`에 등록)
- PR에는 marimo 노트북 소스 파일(.py)만 포함
- 리포트 파일은 GitHub Actions 아티팩트로 업로드

## 출력 형식

```
## 리포트 생성 결과

- 📄 HTML: reports/analysis_42.html (2.3 MB)
- 📄 PDF: reports/analysis_42.pdf (1.1 MB)
- 📝 소스: notebooks/analysis_42.py

리포트가 정상적으로 생성되었습니다.
```

## 완료 증거

- [ ] HTML 파일이 `reports/` 디렉토리에 존재하며 크기가 0보다 큼
- [ ] 소스 노트북(.py)이 변경되지 않았음 (내보내기로 인한 수정 없음)

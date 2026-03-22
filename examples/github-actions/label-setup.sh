#!/usr/bin/env bash
# label-setup.sh — GitHub Issue 라벨 일괄 등록 스크립트
# 7단계 자동 분석 파이프라인에 필요한 라벨을 생성합니다.
#
# 사용법: bash .github/scripts/label-setup.sh <owner/repo>
# 예시:   bash .github/scripts/label-setup.sh myorg/data-analysis

set -euo pipefail

REPO="${1:?사용법: bash label-setup.sh <owner/repo>}"

echo "📋 GitHub Issue 라벨 등록 — $REPO"
echo ""

# 라벨 생성 함수
create_label() {
    local name="$1"
    local color="$2"
    local description="$3"

    if gh label create "$name" \
        --repo "$REPO" \
        --color "$color" \
        --description "$description" 2>/dev/null; then
        echo "  ✅ $name"
    else
        # 이미 존재하면 업데이트
        gh label edit "$name" \
            --repo "$REPO" \
            --color "$color" \
            --description "$description" 2>/dev/null
        echo "  🔄 $name (업데이트)"
    fi
}

echo "🏷️ 워크플로 트리거 라벨:"
create_label "auto-analyze" "0E8A16" "자동 분석 파이프라인 시작 트리거"

echo ""
echo "🏷️ 단계별 라벨 (stage:N):"
create_label "stage:1-problem"      "1D76DB" "Stage 1: 문제 정의"
create_label "stage:2-deliverables" "1D76DB" "Stage 2: 산출물 명세"
create_label "stage:3-spec"         "1D76DB" "Stage 3: 분석 스펙 작성"
create_label "stage:4-extract"      "1D76DB" "Stage 4: 데이터 추출"
create_label "stage:5-analyze"      "1D76DB" "Stage 5: 분석 수행"
create_label "stage:6-report"       "1D76DB" "Stage 6: 리포트 생성"
create_label "stage:7-pr"           "1D76DB" "Stage 7: PR 생성"

echo ""
echo "🏷️ 상태 라벨:"
create_label "done"          "0E8A16" "분석 완료"
create_label "status:error"  "D93F0B" "워크플로 실행 에러"
create_label "status:retry"  "FBCA04" "재시도 대기"

echo ""
echo "✅ 총 11개 라벨 등록 완료!"
echo ""
echo "확인: gh label list --repo $REPO"

#!/bin/bash
# 사용법: ./apply.sh [환경] [옵션]
# 예시:  ./apply.sh              (기본: lab)
#        ./apply.sh prod
#        ./apply.sh lab -auto-approve

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ── 환경 선택 ──
ENV="${1:-lab}"
shift 2>/dev/null || true

if [[ ! -f "environments/${ENV}/${ENV}.tfvars" ]]; then
    echo "❌ 환경 파일 없음: environments/${ENV}/${ENV}.tfvars"
    echo "사용 가능: $(ls environments/)"
    exit 1
fi

# ── Webex 설정 ──
WEBEX_TOKEN="${WEBEX_TOKEN:-MmE1NGQ1ZGItMWFiNy00NmI5LWJiZGUtZDkyMWI5ZTJlMmNlMmNjMWQ0MTUtZTU1_PF84_1eb65fdf-9643-417f-9974-ad72cae0e10f}"
WEBEX_ROOM_ID="${WEBEX_ROOM_ID:-Y2lzY29zcGFyazovL3VzL1JPT00vYTMzZDQ2YjAtYTk4Mi0xMWYwLWIzZjgtMzc4OWFlOTVmOTUz}"

VAR_FILE="environments/${ENV}/${ENV}.tfvars"
APPLY_LOG="/tmp/tf-apply-$$.log"
PLAN_LOG="/tmp/tf-plan-$$.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
WHOAMI=$(whoami)
EXTRA_ARGS="${*:-}"

# ── 색상 ──
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

send_webex() {
    local message="$1"
    curl -s -o /dev/null -X POST "https://webexapis.com/v1/messages" \
        -H "Authorization: Bearer $WEBEX_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"roomId\": \"$WEBEX_ROOM_ID\", \"markdown\": \"$message\"}"
}

cleanup() {
    rm -f "$APPLY_LOG" "$PLAN_LOG"
}
trap cleanup EXIT

# ── Step 1: Plan ──
echo -e "${YELLOW}━━━ Terraform Plan ━━━${NC}"
if terraform plan -var-file="$VAR_FILE" -no-color -out=tfplan 2>&1 | tee "$PLAN_LOG"; then
    PLAN_SUMMARY=$(grep -E "^Plan:|^No changes" "$PLAN_LOG" | head -1 || echo "Plan completed")
    echo -e "\n${GREEN}✅ Plan 성공: ${PLAN_SUMMARY}${NC}\n"
else
    PLAN_SUMMARY="Plan failed"
    echo -e "\n${RED}❌ Plan 실패${NC}\n"
    send_webex "❌ **SD-WAN Terraform Plan 실패**\n\n- **실행자**: ${WHOAMI}\n- **시간**: ${TIMESTAMP}\n- **환경**: ${VAR_FILE}"
    exit 1
fi

# No changes면 알림 보내고 종료
if echo "$PLAN_SUMMARY" | grep -q "No changes"; then
    echo -e "${GREEN}변경사항 없음. 종료.${NC}"
    exit 0
fi

# ── Step 2: 확인 ──
if [[ "$EXTRA_ARGS" != *"-auto-approve"* ]]; then
    echo -e "${YELLOW}위 Plan 결과를 확인하세요.${NC}"
    read -p "Apply 진행할까요? (yes/no): " CONFIRM
    if [[ "$CONFIRM" != "yes" ]]; then
        echo "취소됨."
        exit 0
    fi
fi

# ── Step 3: Apply ──
echo -e "\n${YELLOW}━━━ Terraform Apply ━━━${NC}"
if terraform apply -no-color tfplan 2>&1 | tee "$APPLY_LOG"; then
    APPLY_SUMMARY=$(grep -E "^Apply complete" "$APPLY_LOG" | head -1 || echo "Apply completed")
    STATUS="success"
    ICON="✅"
    echo -e "\n${GREEN}✅ Apply 성공: ${APPLY_SUMMARY}${NC}"
else
    APPLY_SUMMARY=$(grep -E "^Error" "$APPLY_LOG" | head -1 || echo "Apply failed")
    STATUS="failure"
    ICON="🚨"
    echo -e "\n${RED}❌ Apply 실패${NC}"
fi

# ── Step 4: Webex 알림 ──
GIT_COMMIT=$(git log -1 --format='%h %s' 2>/dev/null || echo "N/A")

send_webex "${ICON} **SD-WAN Terraform Apply (로컬)**\n\n- **실행자**: ${WHOAMI}\n- **결과**: ${STATUS}\n- **요약**: ${APPLY_SUMMARY}\n- **환경**: ${VAR_FILE}\n- **최근커밋**: ${GIT_COMMIT}\n- **시간**: ${TIMESTAMP}"

echo -e "\n${GREEN}📨 Webex 알림 전송 완료${NC}"

# 실패 시 exit 1
[[ "$STATUS" == "failure" ]] && exit 1

rm -f tfplan
exit 0

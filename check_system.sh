#!/usr/bin/env bash
set -uo pipefail
PORT=8765
LOG_FILE="/tmp/moonshot_health.log"
PID_FILE="/tmp/moonshot_health.pid"
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
cleanup() {
    [ -f "$PID_FILE" ] && kill "$(cat "$PID_FILE")" 2>/dev/null || true
    rm -f "$PID_FILE" /tmp/moonshot_resp.json
}
trap cleanup EXIT
echo "=== Moonshot 시스템 무결성 검사 시작 ==="
if lsof -ti:"$PORT" > /dev/null 2>&1; then
    echo -e "${YELLOW}포트 $PORT 선점 감지. 강제 종료 중...${NC}"
    lsof -ti:"$PORT" | xargs kill -9 2>/dev/null || true; sleep 1
fi
[ -f ".env" ] && { set -a; source .env; set +a; }
if [ -z "${DATABASE_URL:-}" ]; then
    echo -e "${RED}❌ DATABASE_URL이 설정되지 않았습니다.${NC}"; exit 1
fi
uvicorn moonshot_backend_fastapi:app --host 127.0.0.1 --port "$PORT" --log-level error > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
echo "FastAPI 기동 중 (PID: $(cat "$PID_FILE"))..."
READY=0
for i in $(seq 1 15); do
    curl -sf "http://127.0.0.1:$PORT/api/health" -o /dev/null 2>&1 && READY=1 && break
    sleep 1
done
[ "$READY" -eq 0 ] && { echo -e "${RED}❌ 서버 기동 실패${NC}"; cat "$LOG_FILE"; exit 1; }
HTTP_CODE=$(curl -s -o /tmp/moonshot_resp.json -w "%{http_code}" "http://127.0.0.1:$PORT/api/health")
BODY=$(cat /tmp/moonshot_resp.json 2>/dev/null || echo "")
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ 시스템 정상 (HTTP $HTTP_CODE) — DB 응답: $BODY${NC}"
    echo "=== 검사 완료: 배포 진행 가능 ==="; exit 0
else
    echo -e "${RED}❌ 헬스 체크 실패 (HTTP $HTTP_CODE) — $BODY${NC}"
    cat "$LOG_FILE"; echo "=== 검사 실패: 배포 중단 권고 ==="; exit 1
fi

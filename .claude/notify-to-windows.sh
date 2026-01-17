#!/bin/bash

# WSL에서 Windows 호스트로 알림 전송 스크립트
# 전제: 윈도우 호스트에서 dev-notify-bridge (port 6789) 를 실행 중이어야 합니다.
#      npx dev-notify-bridge --port 6789
# 사용법:
#   ./notify-to-windows.sh --title "제목" --message "메시지" --sound false
#   ./notify-to-windows.sh --title "Build Complete" --message "Your backend is ready" --sound true

# 기본값 설정
TITLE="Notification"
MESSAGE="Message"
SOUND="true"

# Named arguments 파싱
while [[ $# -gt 0 ]]; do
  case $1 in
    --title)
      TITLE="$2"
      shift 2
      ;;
    --message)
      MESSAGE="$2"
      shift 2
      ;;
    --sound)
      SOUND="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      shift
      ;;
  esac
done

# WSL에서 Windows 호스트 IP 가져오기 (기본 게이트웨이)
WINDOWS_HOST=$(ip route show | grep -i default | awk '{ print $3}')

if [ -z "$WINDOWS_HOST" ]; then
  # IP를 가져오지 못하면 조용히 종료 (hook 실패 방지)
  exit 0
fi

# dev-notify-bridge로 POST 요청 전송
# (실패해도 개발에 영향 없음)
curl -X POST "http://${WINDOWS_HOST}:6789/notify" \
  -H "Content-Type: application/json" \
  -d "{\"title\": \"$TITLE\", \"message\": \"$MESSAGE\", \"sound\": $SOUND}" \
  --silent --show-error --fail \
  --connect-timeout 1 \
  --max-time 2 \
  > /dev/null 2>&1

# 성공/실패 여부와 관계없이 항상 0 반환 (클로드 hook이 실패하지 않도록)
exit 0

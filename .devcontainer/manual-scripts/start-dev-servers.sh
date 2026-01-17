#!/bin/bash
# 개발 서버 시작 스크립트 (monoserver-private2)
# - Happy Server
# - Screen Party Server (Docker Image)
#
# 복사해서 바로 실행 (WSL에서)
# /home/simelvia/Develop-WSL/screen-party/.devcontainer/manual-scripts/start-dev-servers.sh

set -e

MONOSERVER_DIR="/home/simelvia/Develop-WSL/monoserver-private2"

echo "🚀 개발 서버 시작 중..."
echo "  위치: $MONOSERVER_DIR"
echo ""

cd "$MONOSERVER_DIR"
docker compose up -d

echo ""
echo "✅ 개발 서버 시작 완료"
echo "💡 팁: cd $MONOSERVER_DIR && docker compose logs -f 로 로그 확인"

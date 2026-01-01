#!/bin/bash

# Claude Code를 계속 반복 실행하는 스크립트
# 사용법: ./run-claude-loop.sh [claude 명령어 옵션...]

echo "🤖 Claude Code 반복 실행 모드"
echo "중단하려면 Ctrl+C를 누르세요"
echo "================================"
echo ""

# 실행 횟수 카운터
count=1

# 무한 루프
while true; do
    echo "📍 실행 #$count ($(date '+%Y-%m-%d %H:%M:%S'))"
    echo "--------------------------------"

    # Claude Code 실행 (모든 인자를 그대로 전달)
    claude "$@"

    # 종료 코드 확인
    exit_code=$?

    echo ""
    echo "✅ 실행 #$count 완료 (종료 코드: $exit_code)"
    echo "================================"
    echo ""

    # 다음 실행까지 2초 대기 (선택적)
    # sleep 2

    ((count++))
done

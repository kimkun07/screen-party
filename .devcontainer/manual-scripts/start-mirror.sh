#!/bin/bash
# WSL → Windows 실시간 동기화 스크립트
#
# 복사해서 바로 실행 (WSL에서)
# /home/simelvia/Develop-WSL/screen-party/.devcontainer/manual-scripts/start-mirror.sh /mnt/d/Data/Develop/screen-party-mirrored

set -e

# 프로젝트 루트 디렉토리 (이 스크립트 기준)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Windows 대상 경로 (인자로 받기)
WINDOWS_TARGET="$1"

if [ -z "$WINDOWS_TARGET" ]; then
  echo "❌ 오류: Windows 대상 경로가 지정되지 않았습니다."
  echo ""
  echo "사용법:"
  echo "  ./.devcontainer/manual-scripts/start-mirror.sh /mnt/d/Data/Develop/screen-party-mirrored"
  exit 1
fi

# 대상 디렉토리 존재 확인
if [ ! -d "$WINDOWS_TARGET" ]; then
  echo "⚠️  경고: 대상 디렉토리가 존재하지 않습니다: $WINDOWS_TARGET"
  read -p "디렉토리를 생성하시겠습니까? (y/n) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    mkdir -p "$WINDOWS_TARGET"
    echo "✅ 디렉토리 생성 완료: $WINDOWS_TARGET"
  else
    echo "❌ 취소되었습니다."
    exit 1
  fi
fi

echo "🔄 WSL → Windows 실시간 동기화 시작"
echo "  원본: $PROJECT_ROOT"
echo "  대상: $WINDOWS_TARGET"
echo ""
echo "💡 팁: Ctrl + C로 종료"
echo ""

cd "$PROJECT_ROOT" # watchexec try to use .gitignore

# watchexec + rsync로 실시간 동기화
watchexec \
  --print-events \
  -w "$PROJECT_ROOT" \
  --debounce 500 \
  --ignore '.agent' \
  --ignore '.venv*' \
  --ignore '__pycache__' \
  --ignore '.git' \
  --ignore '*.pyc' \
  --ignore '.pytest_cache' \
  --ignore '.ruff_cache' \
  --ignore '.mypy_cache' \
  --ignore 'node_modules' \
  -- \
  rsync -av --delete \
    --exclude='.claude' \
    --exclude='.venv' \
    --exclude='.venv-windows' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='.ruff_cache' \
    --exclude='.mypy_cache' \
    --exclude='node_modules' \
    --exclude='client/dist' \
    "$PROJECT_ROOT/" \
    "$WINDOWS_TARGET/"

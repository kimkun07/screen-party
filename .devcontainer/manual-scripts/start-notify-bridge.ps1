# Windows 알림 브릿지 시작 스크립트
#
# 복사해서 바로 실행 (PowerShell에서):
# & "D:\Data\Develop\screen-party-mirrored\.devcontainer\manual-scripts\start-notify-bridge.ps1"

Write-Host "🔔 Windows 알림 브릿지 시작 중..." -ForegroundColor Cyan
Write-Host "  포트: 6789" -ForegroundColor Gray
Write-Host ""

# dev-notify-bridge 실행
try {
    npx dev-notify-bridge --port 6789
} catch {
    Write-Host "❌ 오류: dev-notify-bridge 시작 실패" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

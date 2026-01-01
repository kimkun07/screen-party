# Task: Server Deployment (서버 Docker 배포)

## 개요

서버를 Docker 이미지로 빌드하여 배포

## 목표

- [ ] Dockerfile 작성
- [ ] docker-compose.yml 작성 (로컬 테스트용)
- [ ] 멀티 스테이지 빌드 (최적화)
- [ ] 환경 변수 설정
- [ ] Docker Hub/GitHub Container Registry에 푸시
- [ ] 배포 가이드 작성

## 상세 요구사항

### Dockerfile
- 베이스 이미지: `python:3.11-slim`
- Poetry로 의존성 설치
- 포트: 8765 노출
- 비 root 유저로 실행 (보안)

```dockerfile
# 멀티 스테이지 빌드
FROM python:3.11-slim as builder

WORKDIR /app

# Poetry 설치
RUN pip install poetry

# 의존성만 먼저 설치 (캐싱 최적화)
COPY server/pyproject.toml server/poetry.lock ./
RUN poetry config virtualenvs.in-project true && \
    poetry install --no-dev --no-root

# 소스 코드 복사
COPY server/src ./src

# 최종 이미지
FROM python:3.11-slim

WORKDIR /app

# 가상 환경 복사
COPY --from=builder /app/.venv ./.venv
COPY --from=builder /app/src ./src

# 비 root 유저 생성
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# 환경 변수
ENV PATH="/app/.venv/bin:$PATH"
ENV SCREEN_PARTY_PORT=8765

EXPOSE 8765

CMD ["python", "-m", "screen_party_server.server"]
```

### docker-compose.yml (로컬 테스트)
```yaml
version: "3.9"

services:
  server:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8765:8765"
    environment:
      - SCREEN_PARTY_PORT=8765
    restart: unless-stopped
```

### 환경 변수
- `SCREEN_PARTY_PORT`: 서버 포트 (기본: 8765)
- `LOG_LEVEL`: 로그 레벨 (기본: INFO)

### Docker Hub 배포
```bash
# 빌드
docker build -t yourusername/screen-party-server:latest .

# 푸시
docker push yourusername/screen-party-server:latest
```

### GitHub Actions 자동 배포
- main 브랜치에 push 시 자동 빌드
- GitHub Container Registry에 푸시
- 태그 버전 관리

```yaml
name: Docker Build and Push

on:
  push:
    branches: [main]
    tags: ["v*"]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      - name: Login to GitHub Container Registry
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}/server:latest
```

## 기술 결정

### 멀티 스테이지 빌드
- Poetry 설치 및 빌드는 builder 스테이지
- 최종 이미지는 가상 환경만 복사
- 이미지 크기 최소화

### 비 root 유저
- 보안 강화
- UID 1000으로 고정 (호환성)

## TODO

- [ ] Dockerfile 작성
- [ ] docker-compose.yml 작성
- [ ] 로컬 테스트 (docker-compose up)
- [ ] .dockerignore 작성
- [ ] GitHub Actions 워크플로우 작성
- [ ] 배포 가이드 (README.md 또는 별도 문서)

## 클로드 코드 일기

### 2026-01-01 - Docker 배포 준비

**상태**: 🟡 준비중 → 🟢 진행중

**진행 내용**:
- ✅ feature/server-deployment 브랜치 생성
- ✅ 기존 Dockerfile 검토 (uv 기반 multi-stage build 이미 작성됨)
- ✅ Dockerfile 보안 개선: 비 root 유저 추가 (appuser, UID 1000)
- ✅ devcontainer.json에 docker-in-docker feature 추가
- ✅ docker-compose.yml 확인 (기본 설정 완료)
- ✅ .dockerignore 파일 확인 (루트 및 server/ 모두 존재)

**현재 상태**:
- Dockerfile은 준비 완료 (보안 개선 포함)
- docker-compose.yml 준비 완료
- devcontainer rebuild 필요 (Docker 사용을 위해)

**테스트 명령어** (호스트 또는 rebuild된 devcontainer에서 실행):
```bash
# 1. Docker 이미지 빌드
docker build -f server/Dockerfile -t screen-party-server:latest .

# 2. docker-compose로 서버 실행
docker-compose up -d

# 3. 서버 로그 확인
docker-compose logs -f server

# 4. 클라이언트에서 연결 테스트
# devcontainer에서:
uv run python client/main.py
# 또는 호스트에서:
python client/main.py
# 서버 주소: localhost:8765

# 5. 정리
docker-compose down
```

**주요 개선사항**:
- **보안**: 비 root 유저로 실행 (appuser, UID 1000)
- **소유권 설정**: /app 디렉토리 appuser 소유

**다음 단계**:
1. devcontainer rebuild (Docker-in-Docker 활성화)
2. Docker 이미지 빌드 테스트
3. docker-compose로 서버 실행 테스트
4. 클라이언트 연결 테스트
5. GitHub Actions 워크플로우 작성 (선택)
6. 배포 가이드 README 업데이트

**블로커**:
- devcontainer rebuild 필요 (또는 호스트 환경에서 테스트)

---

> **다음 클로드 코드에게**:
> - devcontainer를 rebuild하거나 호스트 환경에서 Docker 테스트 실행
> - 위의 "테스트 명령어" 섹션을 참고하세요
> - 빌드가 성공하면 실제 연결 테스트까지 진행
> - 모든 테스트가 통과하면 devlog 완료 표시 및 커밋

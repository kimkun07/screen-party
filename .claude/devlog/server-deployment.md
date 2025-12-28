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

_이 섹션은 작업 진행 시 업데이트됩니다._

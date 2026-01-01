# Screen Party Server

WebSocket 기반 실시간 드로잉 서버

## 개요

Screen Party 서버는 WebSocket을 통해 호스트와 게스트 간 실시간 드로잉 데이터를 중계합니다.

## 주요 기능

- **세션 관리**: 6자리 코드로 세션 생성 및 참여
- **실시간 통신**: WebSocket을 통한 양방향 통신
- **브로드캐스팅**: 한 클라이언트의 드로잉을 모든 참여자에게 전송
- **자동 정리**: 비활성 세션 자동 만료 (기본 60분)

## API

### WebSocket 메시지

#### 세션 생성 (호스트)

```json
{
  "type": "create_session",
  "host_name": "Player1"
}
```

응답:
```json
{
  "type": "session_created",
  "session_id": "ABC123",
  "host_id": "uuid-1234"
}
```

#### 세션 참여 (게스트)

```json
{
  "type": "join_session",
  "session_id": "ABC123",
  "guest_name": "Player2"
}
```

응답:
```json
{
  "type": "guest_joined",
  "user_id": "uuid-5678",
  "guest_name": "Player2"
}
```

#### Ping/Pong

```json
{
  "type": "ping"
}
```

응답:
```json
{
  "type": "pong"
}
```

## 환경 변수

- `SERVER_HOST`: 바인드할 호스트 (기본값: `0.0.0.0`)
- `SERVER_PORT`: 서버 포트 (기본값: `8765`)

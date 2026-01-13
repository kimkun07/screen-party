# Task: Session Management (세션 관리 시스템)

## 개요

6자리 세션 ID 생성 및 세션 생명주기 관리

## 목표

- [ ] 6자리 세션 ID 생성 알고리즘 구현
- [ ] 세션 저장 및 조회 (in-memory)
- [ ] 세션 만료 처리
- [ ] 유닛 테스트 작성

## 상세 요구사항

### 세션 ID 생성
- 형식: 6자리 대문자 알파벳 + 숫자 (예: ABC123, XYZ789)
- 충돌 방지: 기존 활성 세션과 중복 체크
- 최대 재시도: 10회 (충돌 시)

### 세션 데이터 구조
```python
@dataclass
class Session:
    session_id: str
    participants: Dict[str, Participant]  # user_id -> Participant
    created_at: datetime
    last_activity: datetime
    is_active: bool
```

### 세션 생명주기
1. 생성: 첫 번째 참여자 연결 시
2. 활성: 다른 참여자 참여 가능
3. 만료: 마지막 활동 후 1시간 또는 마지막 참여자 disconnection
4. 삭제: 만료된 세션 자동 정리 (백그라운드 태스크)

### 주요 메서드
- `create_session(participant_name: str) -> (Session, Participant)`
- `get_session(session_id: str) -> Optional[Session]`
- `add_participant(session_id: str, participant_name: str) -> Optional[Participant]`
- `remove_participant(session_id: str, user_id: str) -> bool`
- `expire_session(session_id: str) -> None`
- `cleanup_expired_sessions() -> int`  # 삭제된 세션 수 반환

## 기술 결정

### 충돌 방지 전략
- 36^6 = 2,176,782,336 가능한 조합
- 동시 활성 세션이 1만 개라고 가정해도 충돌 확률 매우 낮음
- 충돌 시 재시도로 충분

### 만료 정책
- 기본: 마지막 활동 후 1시간
- 마지막 참여자 disconnection 시 즉시 만료
- 세션 생성자가 나가도 다른 참여자가 있으면 세션 유지
- 백그라운드 cleanup: 5분마다 실행

## TODO

- [x] Session, Participant 데이터 모델 정의 (models.py)
- [x] SessionManager 클래스 구현 (session.py)
- [x] 세션 ID 생성 함수 (유틸리티)
- [x] 만료 세션 cleanup 백그라운드 태스크
- [x] 유닛 테스트 작성 (test_session.py)
- [x] 호스트/게스트 개념 제거, 참여자 기반으로 변경 (2026-01-13)

## 클로드 코드 일기

### 2025-12-28 - Session Management 구현 완료

**상태**: 🟡 준비중 → ✅ 완료

**진행 내용**:
- ✅ `server/src/screen_party_server/models.py` 생성
  - `Guest` dataclass: user_id, name, joined_at
  - `Session` dataclass: session_id, host_id, host_name, guests, created_at, last_activity, is_active
- ✅ `server/src/screen_party_server/session.py` 생성
  - `SessionManager` 클래스 구현
  - `_generate_session_id()`: 6자리 대문자+숫자, 최대 10회 재시도
  - `create_session()`: 새 세션 생성
  - `get_session()`: 세션 조회
  - `add_guest()`, `remove_guest()`: 게스트 관리
  - `expire_session()`, `delete_session()`: 세션 종료/삭제
  - `cleanup_expired_sessions()`: 타임아웃 세션 정리 (기본 60분)
  - `start_cleanup_task()`: 백그라운드 asyncio 태스크 (5분마다)
- ✅ `server/tests/test_session.py` 생성
  - 14개 유닛 테스트 작성
  - 모든 테스트 통과 (14/14 in 1.06s)

**테스트 결과**:
```
test_session.py::test_generate_session_id PASSED
test_session.py::test_session_id_uniqueness PASSED
test_session.py::test_create_session PASSED
test_session.py::test_get_session PASSED
test_session.py::test_add_guest PASSED
test_session.py::test_remove_guest PASSED
test_session.py::test_expire_session PASSED
test_session.py::test_delete_session PASSED
test_session.py::test_cleanup_expired_sessions PASSED
test_session.py::test_cleanup_active_sessions_not_removed PASSED
test_session.py::test_activity_tracking PASSED
test_session.py::test_collision_retry PASSED
test_session.py::test_create_session_collision_limit PASSED
test_session.py::test_background_cleanup_task PASSED

14 passed in 1.06s
```

**주요 결정사항**:
- 세션 ID 형식: 6자리 대문자 알파벳 + 숫자 (36^6 = 2.1B 조합)
- 충돌 방지: 최대 10회 재시도로 충분 (충돌 확률 극히 낮음)
- 만료 정책: 마지막 활동 후 60분 (configurable)
- 백그라운드 cleanup: 5분마다 자동 실행 (asyncio task)

**다음 단계**:
P0 나머지 task 진행:
1. server-core: WebSocket 서버 구현 (세션 관리와 통합)
2. client-core: PyQt6 GUI 기본 구조

---

### 2026-01-13 - 호스트/게스트 개념 제거, 참여자 기반으로 변경

**상태**: ✅ 완료

**진행 내용**:
- ✅ `Guest` → `Participant` 이름 변경
- ✅ `Session` 모델에서 `host_id`, `host_name`, `host_color` 필드 제거
- ✅ `Session.guests` → `Session.participants` 변경
- ✅ `Session.has_participants()` 메서드 추가
- ✅ `create_session()` 반환 타입 변경: `Session` → `(Session, Participant)`
- ✅ `add_guest()` → `add_participant()` 이름 변경
- ✅ `remove_guest()` → `remove_participant()` 이름 변경
- ✅ `remove_participant()`에서 마지막 참여자 체크 후 세션 자동 만료
- ✅ 모든 유닛 테스트 업데이트 및 통과 (29/29)

**핵심 변경사항**:
1. **세션 생명주기**: 마지막 참여자가 나갈 때만 세션 만료 (첫 번째 참여자가 나가도 세션 유지)
2. **평등한 권한**: 모든 참여자가 동등한 권한, 특별한 호스트 권한 없음
3. **Backward compatibility**: 메시지 타입 `PARTICIPANT_JOINED`/`PARTICIPANT_LEFT` 추가, 기존 `GUEST_JOINED`/`GUEST_LEFT`도 지원

**테스트 결과**:
- Server 유닛 테스트: 15/15 통과
- Session 유닛 테스트: 14/14 통과
- 총 29개 테스트 모두 통과

**다음 단계**:
Integration 테스트 업데이트 및 실제 클라이언트 테스트

---

> **다음 Claude Code에게**:
> - SessionManager는 싱글톤 패턴으로 사용하세요 (서버에 하나만 존재)
> - WebSocket 서버에서 메시지 수신 시 `session.last_activity` 업데이트 필수
> - cleanup_task는 서버 시작 시 `asyncio.create_task()`로 백그라운드 실행
> - 테스트는 pytest-asyncio를 사용해 비동기 함수 테스트 가능
> - **중요**: 모든 참여자가 평등하며, 세션은 마지막 참여자가 나갈 때만 만료됨

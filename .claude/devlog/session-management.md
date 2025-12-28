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
    host_id: str
    host_name: str
    guests: Dict[str, Guest]  # user_id -> Guest
    created_at: datetime
    last_activity: datetime
    is_active: bool
```

### 세션 생명주기
1. 생성: 호스트 연결 시
2. 활성: 게스트 참여 가능
3. 만료: 마지막 활동 후 1시간 또는 호스트 disconnection
4. 삭제: 만료된 세션 자동 정리 (백그라운드 태스크)

### 주요 메서드
- `create_session(host_name: str) -> Session`
- `get_session(session_id: str) -> Optional[Session]`
- `add_guest(session_id: str, guest: Guest) -> bool`
- `remove_guest(session_id: str, user_id: str) -> bool`
- `expire_session(session_id: str) -> None`
- `cleanup_expired_sessions() -> int`  # 삭제된 세션 수 반환

## 기술 결정

### 충돌 방지 전략
- 36^6 = 2,176,782,336 가능한 조합
- 동시 활성 세션이 1만 개라고 가정해도 충돌 확률 매우 낮음
- 충돌 시 재시도로 충분

### 만료 정책
- 기본: 마지막 활동 후 1시간
- 호스트 disconnection 시 즉시 만료
- 백그라운드 cleanup: 5분마다 실행

## TODO

- [ ] Session, Guest 데이터 모델 정의 (models.py)
- [ ] SessionManager 클래스 구현 (session.py)
- [ ] 세션 ID 생성 함수 (유틸리티)
- [ ] 만료 세션 cleanup 백그라운드 태스크
- [ ] 유닛 테스트 작성 (test_session.py)

## 클로드 코드 일기

_이 섹션은 작업 진행 시 업데이트됩니다._

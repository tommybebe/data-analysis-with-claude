#!/usr/bin/env python3
"""
합성 데이터 생성 스크립트 — B2C 모바일 피트니스 앱 이벤트 데이터

BigQuery에 적재할 합성 데이터(raw_users, raw_sessions, raw_events)를 생성합니다.
DAU/MAU 분석 실습에 사용되는 현실적인 모바일 앱 행동 데이터를 시뮬레이션합니다.

사용법:
    # CSV 파일 생성 (기본 출력 디렉토리: ./output/)
    python generate_synthetic_data.py

    # Parquet 형식으로 출력
    python generate_synthetic_data.py --format parquet

    # CSV + Parquet 모두 출력
    python generate_synthetic_data.py --format both

    # 출력 디렉토리 지정
    python generate_synthetic_data.py --output-dir ./data/

    # BigQuery에 직접 적재
    python generate_synthetic_data.py --load-to-bigquery --project-id my-project --dataset raw

    # 사용자 수와 기간 조정
    python generate_synthetic_data.py --num-users 5000 --start-date 2025-06-01 --end-date 2026-03-31

    # 세션당 이벤트 수 조정 (기본값: 8)
    python generate_synthetic_data.py --events-per-session 12

필요 패키지:
    pip install numpy pandas  # 기본 CSV 생성
    pip install pyarrow  # Parquet 출력 시 추가
    pip install google-cloud-bigquery pandas-gbq  # BigQuery 적재 시 추가
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 상수 정의
# ---------------------------------------------------------------------------

# 기본 설정값
DEFAULT_NUM_USERS = 10_000
DEFAULT_START_DATE = "2025-01-01"
DEFAULT_END_DATE = "2026-03-31"
DEFAULT_EVENTS_PER_SESSION = 8  # 세션당 평균 이벤트 수 (app_open/app_close 포함)
RANDOM_SEED = 42

# 출력 형식 옵션
FORMAT_CSV = "csv"
FORMAT_PARQUET = "parquet"
FORMAT_BOTH = "both"
SUPPORTED_FORMATS = [FORMAT_CSV, FORMAT_PARQUET, FORMAT_BOTH]

# 플랫폼 비율 (한국 시장 반영: iOS 55%, Android 45%)
PLATFORM_WEIGHTS = {"ios": 0.55, "android": 0.45}

# 구독 등급 분포
SUBSCRIPTION_TIERS = {"free": 0.60, "premium": 0.30, "premium_plus": 0.10}

# 국가 분포
COUNTRY_DISTRIBUTION = {"KR": 0.40, "US": 0.25, "JP": 0.15, "TW": 0.08, "TH": 0.07, "VN": 0.05}

# 국가별 언어 매핑
COUNTRY_LANGUAGE_MAP = {
    "KR": "ko",
    "US": "en",
    "JP": "ja",
    "TW": "zh-TW",
    "TH": "th",
    "VN": "vi",
}

# 유입 채널 분포
REFERRAL_SOURCES = {"organic": 0.40, "paid_search": 0.25, "social": 0.20, "referral": 0.15}

# 연령대 분포
AGE_GROUPS = {"18-24": 0.20, "25-34": 0.35, "35-44": 0.25, "45-54": 0.12, "55+": 0.08}

# 이벤트 유형 목록 (워크아웃 시작/완료는 세션 내에서 쌍으로 처리)
EVENT_TYPES = [
    "app_open",
    "app_close",
    "screen_view",
    "workout_start",
    "workout_complete",
    "goal_set",
    "goal_achieved",
    "social_share",
    "purchase",
    "push_notification_open",
]

# 세션 내 이벤트 유형별 기본 발생 가중치 (workout_start/complete는 별도 처리)
EVENT_TYPE_BASE_WEIGHTS = {
    "app_open": 0.01,       # 세션 시작 시 한 번 발생 (별도 삽입)
    "screen_view": 0.40,
    "workout_start": 0.00,  # 별도 로직으로 처리
    "workout_complete": 0.00,
    "goal_set": 0.05,
    "goal_achieved": 0.03,
    "social_share": 0.04,
    "purchase": 0.02,
    "push_notification_open": 0.05,
    "app_close": 0.01,      # 세션 종료 시 한 번 발생 (별도 삽입)
}

# 앱 버전 분포 (최신 3개 버전에 90% 집중)
APP_VERSIONS = {
    "3.2.1": 0.45,
    "3.2.0": 0.30,
    "3.1.2": 0.15,
    "3.1.0": 0.06,
    "3.0.5": 0.04,
}

# 디바이스 유형 분포 (플랫폼별 스마트폰/태블릿 비율)
DEVICE_TYPE_WEIGHTS = {
    "ios": {"smartphone": 0.85, "tablet": 0.15},       # iPhone vs iPad
    "android": {"smartphone": 0.92, "tablet": 0.08},   # 안드로이드 폰 vs 태블릿
}

# 기기 모델 목록 (플랫폼별)
DEVICE_MODELS = {
    "ios": [
        "iPhone 16 Pro Max", "iPhone 16 Pro", "iPhone 16",
        "iPhone 15 Pro Max", "iPhone 15 Pro", "iPhone 15",
        "iPhone 14 Pro", "iPhone 14", "iPhone SE (3rd)",
    ],
    "android": [
        "Galaxy S25 Ultra", "Galaxy S25", "Galaxy S24 Ultra", "Galaxy S24",
        "Galaxy A55", "Galaxy A35", "Pixel 9 Pro", "Pixel 9",
        "Galaxy Z Flip 6", "Galaxy Z Fold 6",
    ],
}

# OS 버전 목록 (플랫폼별)
OS_VERSIONS = {
    "ios": ["iOS 19.0", "iOS 18.3", "iOS 18.2", "iOS 18.1", "iOS 17.7"],
    "android": ["Android 16", "Android 15", "Android 14", "Android 13"],
}

# 시간대 가중치 (0-23시, 한국 기준 UTC+9 → UTC 오프셋 적용)
# 오전 7-9시(KST) = UTC 22-00시(전날), 오후 6-10시(KST) = UTC 09-13시
HOUR_WEIGHTS = np.array([
    0.3, 0.2, 0.1, 0.05, 0.03, 0.02,   # 00-05 UTC (KST 09-14)
    0.04, 0.06, 0.10, 0.15, 0.18, 0.20, # 06-11 UTC (KST 15-20) ← 오후 피크
    0.22, 0.20, 0.15, 0.10, 0.08, 0.06, # 12-17 UTC (KST 21-02)
    0.05, 0.07, 0.10, 0.25, 0.35, 0.32, # 18-23 UTC (KST 03-08) ← 오전 피크
])
HOUR_WEIGHTS = HOUR_WEIGHTS / HOUR_WEIGHTS.sum()  # 정규화


# ---------------------------------------------------------------------------
# 유틸리티 함수
# ---------------------------------------------------------------------------

def generate_uuid(seed_str: str) -> str:
    """재현 가능한 UUID v4 생성 (시드 문자열 기반)"""
    h = hashlib.md5(seed_str.encode()).hexdigest()
    return str(uuid.UUID(h[:32], version=4))


def weighted_choice(rng: np.random.Generator, options: dict[str, float]) -> str:
    """가중치 기반 랜덤 선택"""
    keys = list(options.keys())
    weights = np.array(list(options.values()))
    weights = weights / weights.sum()
    return rng.choice(keys, p=weights)


def compute_churn_probability(days_since_signup: int) -> float:
    """
    가입 후 경과일에 따른 이탈(비활성) 확률 계산.
    시그모이드 함수로 시간이 지남에 따라 활동이 점진적으로 감소하는 패턴을 시뮬레이션합니다.
    """
    # 가입 후 90일을 중심으로 이탈 확률이 급격히 증가
    midpoint = 90
    steepness = 0.03
    base_active_prob = 1.0 / (1.0 + np.exp(steepness * (days_since_signup - midpoint)))
    return 1.0 - base_active_prob


def compute_daily_activity_probability(
    user_signup_date: date,
    current_date: date,
    is_weekend: bool,
    subscription_tier: str,
) -> float:
    """
    특정 날짜에 사용자가 활동할 확률을 계산합니다.
    가입 경과일, 주말 효과, 구독 등급을 반영합니다.
    """
    days_since_signup = (current_date - user_signup_date).days
    if days_since_signup < 0:
        return 0.0

    # 기본 활동 확률: 가입 직후 높고 점진적으로 감소
    base_prob = max(0.05, 0.6 * np.exp(-0.005 * days_since_signup))

    # 구독 등급에 따른 보정 (유료 사용자일수록 활동적)
    tier_multiplier = {"free": 0.8, "premium": 1.2, "premium_plus": 1.5}
    base_prob *= tier_multiplier.get(subscription_tier, 1.0)

    # 주말 효과: 15-20% 증가
    if is_weekend:
        base_prob *= 1.17

    return min(base_prob, 0.95)


# ---------------------------------------------------------------------------
# 데이터 생성 클래스
# ---------------------------------------------------------------------------

class SyntheticDataGenerator:
    """모바일 피트니스 앱의 합성 데이터를 생성하는 클래스"""

    def __init__(
        self,
        num_users: int = DEFAULT_NUM_USERS,
        start_date: str = DEFAULT_START_DATE,
        end_date: str = DEFAULT_END_DATE,
        seed: int = RANDOM_SEED,
        events_per_session: int = DEFAULT_EVENTS_PER_SESSION,
    ):
        self.num_users = num_users
        self.start_date = date.fromisoformat(start_date)
        self.end_date = date.fromisoformat(end_date)
        self.seed = seed
        self.events_per_session = events_per_session
        self.rng = np.random.default_rng(seed)

        # 생성된 데이터 저장
        self.users_df: pd.DataFrame | None = None
        self.sessions_df: pd.DataFrame | None = None
        self.events_df: pd.DataFrame | None = None

    def generate_all(self) -> None:
        """모든 테이블 데이터를 순차적으로 생성합니다."""
        print("🔄 사용자 데이터 생성 중...")
        self._generate_users()
        print(f"   ✅ {len(self.users_df):,}명 사용자 생성 완료")

        print("🔄 세션 데이터 생성 중...")
        self._generate_sessions()
        print(f"   ✅ {len(self.sessions_df):,}개 세션 생성 완료")

        print("🔄 이벤트 데이터 생성 중...")
        self._generate_events()
        print(f"   ✅ {len(self.events_df):,}개 이벤트 생성 완료")

        print("🔄 세션별 screen_count 역산 중...")
        self._derive_session_screen_count()
        print(f"   ✅ screen_count 컬럼 추가 완료")

        self._print_summary()

    def _generate_users(self) -> None:
        """raw_users 테이블 데이터를 생성합니다."""
        records = []
        date_range_days = (self.end_date - self.start_date).days

        for i in range(self.num_users):
            user_id = generate_uuid(f"user_{self.seed}_{i}")
            country = weighted_choice(self.rng, COUNTRY_DISTRIBUTION)
            platform = weighted_choice(self.rng, PLATFORM_WEIGHTS)

            # 가입일: 전체 기간에 걸쳐 분포 (초기에 약간 더 집중)
            signup_day_offset = int(self.rng.beta(2, 3) * date_range_days)
            signup_date_val = self.start_date + timedelta(days=signup_day_offset)
            signup_hour = int(self.rng.choice(24, p=HOUR_WEIGHTS))
            signup_minute = int(self.rng.integers(0, 60))
            signup_second = int(self.rng.integers(0, 60))
            signup_timestamp = datetime(
                signup_date_val.year, signup_date_val.month, signup_date_val.day,
                signup_hour, signup_minute, signup_second,
            )

            # 이탈 여부 결정
            days_since_signup = (self.end_date - signup_date_val).days
            churn_prob = compute_churn_probability(days_since_signup)
            is_active = bool(self.rng.random() > churn_prob * 0.43)  # 약 70% 활성 유지

            # 연령대: 일부 사용자는 미입력 (10%)
            age_group = None
            if self.rng.random() > 0.10:
                age_group = weighted_choice(self.rng, AGE_GROUPS)

            # 유입 채널: 일부 미입력 (5%)
            referral_source = None
            if self.rng.random() > 0.05:
                referral_source = weighted_choice(self.rng, REFERRAL_SOURCES)

            # 디바이스 유형: 플랫폼별 스마트폰/태블릿 비율 적용
            device_type = weighted_choice(self.rng, DEVICE_TYPE_WEIGHTS[platform])

            # 가입 시점의 앱 버전: 가입일이 이를수록 이전 버전일 확률 높음
            signup_progress = signup_day_offset / max(date_range_days, 1)
            if signup_progress < 0.3:
                # 초기 가입자: 이전 버전 비중 높음
                initial_version_weights = {
                    "3.0.5": 0.30, "3.1.0": 0.35, "3.1.2": 0.20,
                    "3.2.0": 0.10, "3.2.1": 0.05,
                }
            elif signup_progress < 0.7:
                # 중간 가입자: 중간 버전 비중 높음
                initial_version_weights = {
                    "3.0.5": 0.05, "3.1.0": 0.10, "3.1.2": 0.35,
                    "3.2.0": 0.35, "3.2.1": 0.15,
                }
            else:
                # 최근 가입자: 최신 버전 비중 높음
                initial_version_weights = {
                    "3.0.5": 0.02, "3.1.0": 0.03, "3.1.2": 0.10,
                    "3.2.0": 0.30, "3.2.1": 0.55,
                }
            initial_app_version = weighted_choice(self.rng, initial_version_weights)

            records.append({
                "user_id": user_id,
                "signup_timestamp": signup_timestamp.isoformat() + "Z",
                "signup_date": signup_date_val.isoformat(),
                "country": country,
                "language": COUNTRY_LANGUAGE_MAP.get(country, "en"),
                "platform": platform,
                "device_type": device_type,
                "initial_app_version": initial_app_version,
                "subscription_tier": weighted_choice(self.rng, SUBSCRIPTION_TIERS),
                "age_group": age_group,
                "referral_source": referral_source,
                "is_active": is_active,
                "last_active_date": None,  # 세션 생성 후 역산
            })

        self.users_df = pd.DataFrame(records)

    def _generate_sessions(self) -> None:
        """raw_sessions 테이블 데이터를 생성합니다."""
        sessions = []
        last_active_dates: dict[str, str] = {}

        # 일자별로 순회하며 세션 생성
        total_days = (self.end_date - self.start_date).days + 1
        date_list = [self.start_date + timedelta(days=d) for d in range(total_days)]

        for day_idx, current_date in enumerate(date_list):
            if day_idx % 30 == 0:
                print(f"   📅 {current_date} 처리 중... ({day_idx}/{total_days}일)")

            is_weekend = current_date.weekday() >= 5
            current_date_str = current_date.isoformat()

            for _, user in self.users_df.iterrows():
                signup_date_val = date.fromisoformat(user["signup_date"])
                if current_date < signup_date_val:
                    continue  # 가입 전에는 활동 없음

                if not user["is_active"]:
                    # 비활성 사용자: 마지막 활동일 이후 활동 중단
                    days_active = int((self.end_date - signup_date_val).days * 0.4)
                    cutoff = signup_date_val + timedelta(days=days_active)
                    if current_date > cutoff:
                        continue

                # 일일 활동 확률 계산
                activity_prob = compute_daily_activity_probability(
                    signup_date_val, current_date, is_weekend, user["subscription_tier"],
                )

                if self.rng.random() > activity_prob:
                    continue  # 오늘은 비활동

                # 세션 수 결정 (평균 1.7회, 포아송 분포)
                num_sessions = max(1, int(self.rng.poisson(1.7)))
                num_sessions = min(num_sessions, 5)  # 최대 5회

                for s_idx in range(num_sessions):
                    session_id = generate_uuid(
                        f"session_{self.seed}_{user['user_id']}_{current_date_str}_{s_idx}"
                    )

                    # 세션 시작 시간: 시간대 가중치 적용
                    start_hour = int(self.rng.choice(24, p=HOUR_WEIGHTS))
                    start_minute = int(self.rng.integers(0, 60))
                    start_second = int(self.rng.integers(0, 60))
                    session_start = datetime(
                        current_date.year, current_date.month, current_date.day,
                        start_hour, start_minute, start_second,
                    )

                    # 세션 지속 시간: 로그 정규 분포 (평균 ~8분=480초)
                    duration_seconds = int(self.rng.lognormal(mean=np.log(480), sigma=0.8))
                    duration_seconds = min(duration_seconds, 7200)  # 최대 2시간
                    duration_seconds = max(duration_seconds, 10)    # 최소 10초

                    # 비정상 종료 확률: ~3%
                    is_abnormal_end = bool(self.rng.random() < 0.03)

                    session_end = None
                    session_duration = None
                    if not is_abnormal_end:
                        session_end = session_start + timedelta(seconds=duration_seconds)
                        session_duration = duration_seconds

                    # 이벤트 수: events_per_session 기준으로 포아송 분포 적용 (최소 2: app_open + app_close)
                    # 세션 길이가 짧으면 이벤트 수를 줄여 현실성 유지
                    duration_factor = min(1.0, duration_seconds / 300)  # 5분 이하 세션은 축소
                    adjusted_mean = max(2, int(self.events_per_session * duration_factor))
                    event_count = max(2, int(self.rng.poisson(adjusted_mean)))
                    event_count = min(event_count, 50)

                    platform = user["platform"]
                    app_version = weighted_choice(self.rng, APP_VERSIONS)
                    device_model = self.rng.choice(DEVICE_MODELS[platform])
                    os_version = self.rng.choice(OS_VERSIONS[platform])

                    sessions.append({
                        "session_id": session_id,
                        "user_id": user["user_id"],
                        "session_start": session_start.isoformat() + "Z",
                        "session_end": (session_end.isoformat() + "Z") if session_end else None,
                        "session_date": current_date_str,
                        "session_duration_seconds": session_duration,
                        "platform": platform,
                        "app_version": app_version,
                        "device_model": device_model,
                        "os_version": os_version,
                        "ip_country": user["country"],
                        "event_count": event_count,
                    })

                    # 마지막 활동일 갱신
                    last_active_dates[user["user_id"]] = current_date_str

        self.sessions_df = pd.DataFrame(sessions)

        # users 테이블의 last_active_date 역산
        self.users_df["last_active_date"] = self.users_df["user_id"].map(last_active_dates)

    def _generate_events(self) -> None:
        """raw_events 테이블 데이터를 생성합니다."""
        events = []

        for idx, session in self.sessions_df.iterrows():
            if idx % 50_000 == 0 and idx > 0:
                print(f"   🔨 {idx:,}/{len(self.sessions_df):,} 세션 이벤트 생성 중...")

            session_start = datetime.fromisoformat(session["session_start"].rstrip("Z"))
            session_end_str = session["session_end"]
            duration = session["session_duration_seconds"]
            if duration is None or pd.isna(duration):
                duration = 300  # 비정상 종료 시 추정값 5분 사용
            event_count = session["event_count"]

            session_events = []

            # 1. app_open 이벤트 (세션 시작 시점)
            session_events.append(self._create_event_record(
                session, "app_open", session_start, event_idx=0,
            ))

            # 2. 중간 이벤트 생성 (event_count - 2개, app_open/app_close 제외)
            mid_event_count = max(0, event_count - 2)

            # 워크아웃 시작/완료 쌍 결정 (세션의 약 30%에서 운동 이벤트 발생)
            has_workout = bool(self.rng.random() < 0.30)
            workout_completed = False

            for e_idx in range(mid_event_count):
                # 이벤트 시간: 세션 기간 내 균등 분포
                time_offset = timedelta(
                    seconds=int((e_idx + 1) * duration / (mid_event_count + 1))
                )
                event_time = session_start + time_offset

                if has_workout and e_idx == mid_event_count // 3:
                    # 세션 중반부에 workout_start 삽입
                    session_events.append(self._create_event_record(
                        session, "workout_start", event_time, event_idx=e_idx + 1,
                    ))
                    # 완료율 85%
                    workout_completed = bool(self.rng.random() < 0.85)
                    continue
                elif has_workout and workout_completed and e_idx == (mid_event_count * 2) // 3:
                    # 세션 후반부에 workout_complete 삽입
                    session_events.append(self._create_event_record(
                        session, "workout_complete", event_time, event_idx=e_idx + 1,
                    ))
                    continue

                # 일반 이벤트 유형 선택 (워크아웃 제외)
                general_types = {
                    k: v for k, v in EVENT_TYPE_BASE_WEIGHTS.items()
                    if k not in ("app_open", "app_close", "workout_start", "workout_complete")
                    and v > 0
                }
                event_type = weighted_choice(self.rng, general_types)
                session_events.append(self._create_event_record(
                    session, event_type, event_time, event_idx=e_idx + 1,
                ))

            # 3. app_close 이벤트 (세션 종료 시점, 비정상 종료 시 생략)
            if session_end_str is not None:
                session_end = datetime.fromisoformat(session_end_str.rstrip("Z"))
                session_events.append(self._create_event_record(
                    session, "app_close", session_end, event_idx=event_count - 1,
                ))

            events.extend(session_events)

        self.events_df = pd.DataFrame(events)

    def _derive_session_screen_count(self) -> None:
        """
        생성된 이벤트 데이터로부터 세션별 screen_view 횟수를 역산합니다.

        세션 생성 시점에는 이벤트가 아직 없으므로, 이벤트 생성 완료 후
        screen_view 이벤트를 집계하여 sessions_df에 screen_count 컬럼을 추가합니다.
        이 값은 세션 내 사용자가 조회한 화면 수로, 세션 깊이(depth) 분석에 활용됩니다.
        """
        # 세션별 screen_view 이벤트 수 집계
        screen_views = (
            self.events_df[self.events_df["event_type"] == "screen_view"]
            .groupby("session_id")
            .size()
            .reset_index(name="screen_count")
        )

        # sessions_df에 screen_count 병합 (screen_view가 없는 세션은 0)
        self.sessions_df = self.sessions_df.merge(
            screen_views, on="session_id", how="left"
        )
        self.sessions_df["screen_count"] = (
            self.sessions_df["screen_count"].fillna(0).astype(int)
        )

    def _create_event_record(
        self,
        session: pd.Series,
        event_type: str,
        event_time: datetime,
        event_idx: int,
    ) -> dict:
        """개별 이벤트 레코드를 생성합니다."""
        event_id = generate_uuid(
            f"event_{self.seed}_{session['session_id']}_{event_idx}"
        )

        # 이벤트별 추가 속성 (JSON)
        event_properties = self._generate_event_properties(event_type)

        return {
            "event_id": event_id,
            "user_id": session["user_id"],
            "session_id": session["session_id"],
            "event_type": event_type,
            "event_timestamp": event_time.isoformat() + "Z",
            "event_date": event_time.date().isoformat(),
            "platform": session["platform"],
            "app_version": session["app_version"],
            "device_model": session["device_model"],
            "event_properties": json.dumps(event_properties, ensure_ascii=False) if event_properties else None,
        }

    def _generate_event_properties(self, event_type: str) -> dict | None:
        """이벤트 유형별 추가 속성을 생성합니다."""
        if event_type == "screen_view":
            screens = [
                "home", "workout_list", "workout_detail", "profile",
                "settings", "social_feed", "leaderboard", "goals",
            ]
            return {"screen_name": self.rng.choice(screens)}

        if event_type == "workout_start":
            workout_types = ["running", "yoga", "strength", "cycling", "stretching", "hiit"]
            return {
                "workout_type": self.rng.choice(workout_types),
                "planned_duration_minutes": int(self.rng.choice([15, 20, 30, 45, 60])),
            }

        if event_type == "workout_complete":
            return {
                "actual_duration_minutes": int(self.rng.integers(10, 75)),
                "calories_burned": int(self.rng.integers(50, 600)),
            }

        if event_type == "purchase":
            items = [
                {"item": "premium_monthly", "price": 9900},
                {"item": "premium_annual", "price": 79900},
                {"item": "workout_pack", "price": 4900},
                {"item": "theme_bundle", "price": 2900},
            ]
            selected = self.rng.choice(items)
            return {"item_name": selected["item"], "price_krw": int(selected["price"])}

        if event_type == "goal_set":
            goal_types = ["daily_steps", "weekly_workouts", "weight_target", "streak_days"]
            return {"goal_type": self.rng.choice(goal_types)}

        if event_type == "goal_achieved":
            goal_types = ["daily_steps", "weekly_workouts", "weight_target", "streak_days"]
            return {"goal_type": self.rng.choice(goal_types), "streak_count": int(self.rng.integers(1, 30))}

        if event_type == "social_share":
            share_targets = ["kakao", "instagram", "twitter", "facebook"]
            return {"share_target": self.rng.choice(share_targets)}

        if event_type == "push_notification_open":
            notification_types = ["workout_reminder", "goal_progress", "social_update", "promotion"]
            return {"notification_type": self.rng.choice(notification_types)}

        return None

    def _print_summary(self) -> None:
        """생성된 데이터의 요약 통계를 출력합니다."""
        print("\n" + "=" * 60)
        print("📊 합성 데이터 생성 완료 — 요약 통계")
        print("=" * 60)

        print(f"\n📋 raw_users: {len(self.users_df):,}행")
        active_count = self.users_df["is_active"].sum()
        print(f"   - 활성 사용자: {active_count:,} ({active_count/len(self.users_df)*100:.1f}%)")
        country_dist = {str(k): int(v) for k, v in self.users_df["country"].value_counts().head(5).items()}
        sub_dist = {str(k): int(v) for k, v in self.users_df["subscription_tier"].value_counts().items()}
        plat_dist = {str(k): int(v) for k, v in self.users_df["platform"].value_counts().items()}
        device_dist = {str(k): int(v) for k, v in self.users_df["device_type"].value_counts().items()}
        version_dist = {str(k): int(v) for k, v in self.users_df["initial_app_version"].value_counts().items()}
        print(f"   - 국가 분포: {country_dist}")
        print(f"   - 구독 분포: {sub_dist}")
        print(f"   - 플랫폼 분포: {plat_dist}")
        print(f"   - 디바이스 유형 분포: {device_dist}")
        print(f"   - 가입 시 앱 버전 분포: {version_dist}")

        print(f"\n📋 raw_sessions: {len(self.sessions_df):,}행")
        valid_durations = self.sessions_df["session_duration_seconds"].dropna()
        print(f"   - 평균 세션 길이: {valid_durations.mean():.0f}초 ({valid_durations.mean()/60:.1f}분)")
        null_end_count = self.sessions_df["session_end"].isna().sum()
        print(f"   - 비정상 종료: {null_end_count:,}건 ({null_end_count/len(self.sessions_df)*100:.1f}%)")
        sessions_per_user = self.sessions_df.groupby(["user_id", "session_date"]).size()
        print(f"   - 사용자-일 평균 세션 수: {sessions_per_user.mean():.2f}회")
        if "screen_count" in self.sessions_df.columns:
            avg_screens = self.sessions_df["screen_count"].mean()
            zero_screen_pct = (self.sessions_df["screen_count"] == 0).mean() * 100
            print(f"   - 평균 screen_count: {avg_screens:.1f}회")
            print(f"   - screen_count=0 비율: {zero_screen_pct:.1f}%")

        print(f"\n📋 raw_events: {len(self.events_df):,}행")
        print(f"   - 이벤트 유형 분포:")
        for evt_type, count in self.events_df["event_type"].value_counts().items():
            print(f"     {evt_type}: {count:,} ({count/len(self.events_df)*100:.1f}%)")

        # DAU/MAU 미리보기
        daily_active = self.events_df.groupby("event_date")["user_id"].nunique()
        print(f"\n📈 DAU 미리보기:")
        print(f"   - 평균 DAU: {daily_active.mean():.0f}")
        print(f"   - 최대 DAU: {daily_active.max():.0f}")
        print(f"   - 최소 DAU: {daily_active.min():.0f}")

        monthly_events = self.events_df.copy()
        monthly_events["month"] = pd.to_datetime(monthly_events["event_date"]).dt.to_period("M")
        monthly_active = monthly_events.groupby("month")["user_id"].nunique()
        print(f"\n📈 MAU 미리보기:")
        for month, mau in monthly_active.tail(6).items():
            print(f"   - {month}: {mau:,}")

    def _add_loaded_at(self) -> None:
        """dbt 소스 신선도 검사에 사용되는 _loaded_at 컬럼을 추가합니다."""
        loaded_at = datetime.utcnow().isoformat() + "Z"
        for df in [self.users_df, self.sessions_df, self.events_df]:
            df["_loaded_at"] = loaded_at

    def save_to_csv(self, output_dir: str = "./output") -> None:
        """생성된 데이터를 CSV 파일로 저장합니다."""
        self._add_loaded_at()

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        users_path = output_path / "raw_users.csv"
        sessions_path = output_path / "raw_sessions.csv"
        events_path = output_path / "raw_events.csv"

        self.users_df.to_csv(users_path, index=False)
        print(f"💾 {users_path} 저장 완료 ({len(self.users_df):,}행)")

        self.sessions_df.to_csv(sessions_path, index=False)
        print(f"💾 {sessions_path} 저장 완료 ({len(self.sessions_df):,}행)")

        self.events_df.to_csv(events_path, index=False)
        print(f"💾 {events_path} 저장 완료 ({len(self.events_df):,}행)")

        print(f"\n✅ 모든 CSV 파일이 {output_path.resolve()}에 저장되었습니다.")

    def save_to_parquet(self, output_dir: str = "./output") -> None:
        """생성된 데이터를 Parquet 파일로 저장합니다."""
        try:
            import pyarrow  # noqa: F401
        except ImportError:
            print("❌ pyarrow 패키지가 필요합니다.")
            print("   pip install pyarrow")
            return

        self._add_loaded_at()

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        tables = [
            ("raw_users.parquet", self.users_df),
            ("raw_sessions.parquet", self.sessions_df),
            ("raw_events.parquet", self.events_df),
        ]

        for filename, df in tables:
            file_path = output_path / filename
            df.to_parquet(file_path, index=False, engine="pyarrow")
            # 파일 크기를 사람이 읽기 쉬운 형태로 표시
            file_size = file_path.stat().st_size
            if file_size > 1_000_000:
                size_str = f"{file_size / 1_000_000:.1f}MB"
            else:
                size_str = f"{file_size / 1_000:.1f}KB"
            print(f"💾 {file_path} 저장 완료 ({len(df):,}행, {size_str})")

        print(f"\n✅ 모든 Parquet 파일이 {output_path.resolve()}에 저장되었습니다.")

    def save(self, output_dir: str = "./output", output_format: str = FORMAT_CSV) -> None:
        """
        지정된 형식으로 데이터를 저장합니다.

        Args:
            output_dir: 출력 디렉토리 경로
            output_format: 출력 형식 ('csv', 'parquet', 'both')
        """
        if output_format in (FORMAT_CSV, FORMAT_BOTH):
            self.save_to_csv(output_dir=output_dir)

        if output_format in (FORMAT_PARQUET, FORMAT_BOTH):
            self.save_to_parquet(output_dir=output_dir)

    def load_to_bigquery(
        self,
        project_id: str,
        dataset: str = "raw",
    ) -> None:
        """생성된 데이터를 BigQuery에 직접 적재합니다."""
        try:
            from google.cloud import bigquery
        except ImportError:
            print("❌ google-cloud-bigquery 패키지가 필요합니다.")
            print("   pip install google-cloud-bigquery pandas-gbq")
            return

        self._add_loaded_at()
        client = bigquery.Client(project=project_id)
        dataset_ref = f"{project_id}.{dataset}"

        # 데이터셋 생성 (없으면)
        try:
            client.get_dataset(dataset_ref)
        except Exception:
            ds = bigquery.Dataset(dataset_ref)
            ds.location = "US"
            client.create_dataset(ds, exists_ok=True)
            print(f"📦 데이터셋 {dataset_ref} 생성 완료")

        # 테이블 스키마 정의
        users_schema = [
            bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("signup_timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("signup_date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("country", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("language", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("platform", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("device_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("initial_app_version", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("subscription_tier", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("age_group", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("referral_source", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("is_active", "BOOLEAN", mode="REQUIRED"),
            bigquery.SchemaField("last_active_date", "DATE", mode="NULLABLE"),
            bigquery.SchemaField("_loaded_at", "TIMESTAMP", mode="REQUIRED"),
        ]

        sessions_schema = [
            bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("session_start", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("session_end", "TIMESTAMP", mode="NULLABLE"),
            bigquery.SchemaField("session_date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("session_duration_seconds", "INT64", mode="NULLABLE"),
            bigquery.SchemaField("platform", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("app_version", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("device_model", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("os_version", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("ip_country", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("event_count", "INT64", mode="REQUIRED"),
            bigquery.SchemaField("screen_count", "INT64", mode="REQUIRED"),
            bigquery.SchemaField("_loaded_at", "TIMESTAMP", mode="REQUIRED"),
        ]

        events_schema = [
            bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("event_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("event_timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("event_date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("platform", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("app_version", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("device_model", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("event_properties", "JSON", mode="NULLABLE"),
            bigquery.SchemaField("_loaded_at", "TIMESTAMP", mode="REQUIRED"),
        ]

        tables = [
            ("raw_users", self.users_df, users_schema),
            ("raw_sessions", self.sessions_df, sessions_schema),
            ("raw_events", self.events_df, events_schema),
        ]

        for table_name, df, schema in tables:
            table_ref = f"{dataset_ref}.{table_name}"
            job_config = bigquery.LoadJobConfig(
                schema=schema,
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            )
            print(f"⬆️  {table_ref} 적재 중... ({len(df):,}행)")
            job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
            job.result()  # 완료 대기
            print(f"   ✅ {table_ref} 적재 완료")

        print(f"\n✅ 모든 테이블이 {dataset_ref}에 적재되었습니다.")


# ---------------------------------------------------------------------------
# CLI 인터페이스
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="모바일 피트니스 앱 합성 데이터 생성기 (DAU/MAU 분석용)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 기본 CSV 생성 (10,000 사용자, 2025-01-01 ~ 2026-03-31)
  python generate_synthetic_data.py

  # Parquet 형식으로 출력
  python generate_synthetic_data.py --format parquet

  # CSV + Parquet 모두 출력
  python generate_synthetic_data.py --format both

  # 소규모 테스트 데이터 (1,000 사용자, 3개월)
  python generate_synthetic_data.py --num-users 1000 --start-date 2026-01-01 --end-date 2026-03-31

  # 세션당 이벤트 수 조정
  python generate_synthetic_data.py --events-per-session 12

  # BigQuery 직접 적재
  python generate_synthetic_data.py --load-to-bigquery --project-id my-gcp-project --dataset raw
        """,
    )

    parser.add_argument(
        "--num-users", type=int, default=DEFAULT_NUM_USERS,
        help=f"생성할 사용자 수 (기본값: {DEFAULT_NUM_USERS:,})",
    )
    parser.add_argument(
        "--start-date", type=str, default=DEFAULT_START_DATE,
        help=f"데이터 시작 일자 (YYYY-MM-DD, 기본값: {DEFAULT_START_DATE})",
    )
    parser.add_argument(
        "--end-date", type=str, default=DEFAULT_END_DATE,
        help=f"데이터 종료 일자 (YYYY-MM-DD, 기본값: {DEFAULT_END_DATE})",
    )
    parser.add_argument(
        "--output-dir", type=str, default="./output",
        help="출력 디렉토리 (기본값: ./output)",
    )
    parser.add_argument(
        "--format", type=str, default=FORMAT_CSV,
        choices=SUPPORTED_FORMATS,
        dest="output_format",
        help=f"출력 형식: csv, parquet, both (기본값: {FORMAT_CSV})",
    )
    parser.add_argument(
        "--events-per-session", type=int, default=DEFAULT_EVENTS_PER_SESSION,
        help=f"세션당 평균 이벤트 수 (기본값: {DEFAULT_EVENTS_PER_SESSION}, 최소 2)",
    )
    parser.add_argument(
        "--seed", type=int, default=RANDOM_SEED,
        help=f"난수 시드 (기본값: {RANDOM_SEED}, 재현 가능한 결과 보장)",
    )
    parser.add_argument(
        "--load-to-bigquery", action="store_true",
        help="BigQuery에 직접 적재 (google-cloud-bigquery 패키지 필요)",
    )
    parser.add_argument(
        "--project-id", type=str, default=None,
        help="GCP 프로젝트 ID (--load-to-bigquery 사용 시 필수)",
    )
    parser.add_argument(
        "--dataset", type=str, default="raw",
        help="BigQuery 데이터셋 이름 (기본값: raw)",
    )

    args = parser.parse_args()

    # BigQuery 적재 시 프로젝트 ID 필수 확인
    if args.load_to_bigquery and not args.project_id:
        parser.error("--load-to-bigquery 사용 시 --project-id는 필수입니다.")

    # events_per_session 최소값 검증
    if args.events_per_session < 2:
        parser.error("--events-per-session은 최소 2 이상이어야 합니다 (app_open + app_close).")

    # 설정 요약 출력
    print("=" * 60)
    print("⚙️  합성 데이터 생성 설정")
    print("=" * 60)
    print(f"   사용자 수: {args.num_users:,}")
    print(f"   기간: {args.start_date} ~ {args.end_date}")
    print(f"   세션당 평균 이벤트 수: {args.events_per_session}")
    print(f"   출력 형식: {args.output_format}")
    print(f"   출력 디렉토리: {args.output_dir}")
    print(f"   난수 시드: {args.seed}")
    if args.load_to_bigquery:
        print(f"   BigQuery 적재: {args.project_id}.{args.dataset}")
    print("=" * 60 + "\n")

    # 데이터 생성
    generator = SyntheticDataGenerator(
        num_users=args.num_users,
        start_date=args.start_date,
        end_date=args.end_date,
        seed=args.seed,
        events_per_session=args.events_per_session,
    )
    generator.generate_all()

    # 파일 저장 (CSV/Parquet/both)
    generator.save(output_dir=args.output_dir, output_format=args.output_format)

    # BigQuery 적재 (옵션)
    if args.load_to_bigquery:
        generator.load_to_bigquery(
            project_id=args.project_id,
            dataset=args.dataset,
        )


if __name__ == "__main__":
    main()

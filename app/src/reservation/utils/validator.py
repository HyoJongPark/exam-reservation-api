from datetime import datetime, timedelta


def validate_reservation_datetime(start_time: datetime, end_time: datetime):
    min_date = datetime.now() + timedelta(days=3)
    max_date = datetime.now() + timedelta(days=180)

    # 1. 현재 시점 이후만 예약 가능
    if start_time < min_date:
        raise ValueError("예약은 3일 이후의 일정만 가능합니다.")

    # 2. 180일 이내만 예약 가능
    if start_time > max_date:
        raise ValueError("예약은 현재 시점으로부터 180일 이내까지만 가능합니다.")

    # 3. end가 있다면 start < end 검증
    if end_time <= start_time:
        raise ValueError("종료 시간은 시작 시간보다 커야 합니다.")

    # 4. 10분 단위 검증
    if start_time.minute % 10 != 0 or end_time.minute % 10 != 0:
        raise ValueError("예약 시간은 10분 단위로 입력해야 합니다.")

    # 5. 최소 30분 간격 검증
    if (end_time - start_time).total_seconds() / 60 < 30:
        raise ValueError("예약 시간은 최소 30분 이상이어야 합니다.")

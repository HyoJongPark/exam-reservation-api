from datetime import datetime, timedelta


def validate_reservation_datetime(start: datetime, end: datetime):
    min_date = datetime.now() + timedelta(days=3)
    max_date = datetime.now() + timedelta(days=180)

    # 1. 현재 시점 이후만 예약 가능
    if start < min_date:
        raise ValueError("예약은 3일 이후의 일정만 가능합니다.")

    # 2. 180일 이내만 예약 가능
    if start > max_date:
        raise ValueError("예약은 현재 시점으로부터 180일 이내까지만 가능합니다.")

    # 3. end가 있다면 start < end 검증
    if end <= start:
        raise ValueError("종료 시간은 시작 시간보다 커야 합니다.")

    # 4. 10분 단위 검증
    if start.minute % 10 != 0 or end.minute % 10 != 0:
        raise ValueError("예약 시간은 10분 단위로 입력해야 합니다.")

    # 5. 최소 30분 간격 검증
    if (end - start).total_seconds() / 60 < 30:
        raise ValueError("예약 시간은 최소 30분 이상이어야 합니다.")


def validate_reservation_date_format(date: str, format: str):
    try:
        datetime.strptime(date, format)
    except ValueError as e:
        raise ValueError(f"해당 요청 형식은 '{format}' 포맷이어야 합니다.") from e

from fastapi import HTTPException
import pytest
import datetime

from threading import Thread
from app.src.reservation import service as reservation_service
from app.src.reservation.utils.constants import MAX_CAPACITY
from app.src.user.model import User, Role
from app.src.reservation.model import Reservation, ReservationStatus


@pytest.mark.integration
class TestReservationConcurrency:
    @pytest.fixture(scope="function")
    def dummy_user(self):
        return User(id=1, user_name="test", email="test@example.com", role=Role.ADMIN)

    def test_concurrent_confirmations(self, db_session, dummy_user):
        """동시에 여러 예약을 CONFIRMED 처리해도 5만명 제한 초과 안되도록 정합성 유지"""
        # given
        db_session.add(dummy_user)
        db_session.commit()

        reservations = []
        success_ids = []
        failed_ids = []

        number_of_people = 5000
        count = 100
        for i in range(count):
            res = Reservation(
                user_id=dummy_user.id,
                reservation_name=f"test-{i}",
                start_time=datetime.datetime(2025, 5, 1, 10, 0),
                end_time=datetime.datetime(2025, 5, 1, 11, 0),
                number_of_people=number_of_people,
                status=ReservationStatus.PENDING,
            )
            db_session.add(res)
            reservations.append(res)
        db_session.commit()

        threads = []
        for res in reservations:
            t = Thread(
                target=confirm_with_new_session,
                args=(db_session, dummy_user, res.id, success_ids, failed_ids),
            )
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # then
        # print(success_ids)
        assert len(success_ids) == MAX_CAPACITY / number_of_people  # 성공한 예약 10개
        assert len(failed_ids) == count - len(success_ids)  # 실패한 예약 90개


def confirm_with_new_session(
    db_session, user: User, reservation_id: int, success_ids: list, failed_ids: list
):
    try:
        reservation_service.confirm_reservation(db_session, user, reservation_id)
        success_ids.append(reservation_id)
    except HTTPException as e:
        failed_ids.append(reservation_id)

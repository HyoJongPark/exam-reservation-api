from fastapi import HTTPException
import pytest
import datetime

from app.src.reservation import service as reservation_service
from app.src.reservation.dto.request.update_reservation_request import (
    UpdateReservationRequest,
)
from app.src.reservation.utils.constants import MAX_CAPACITY
from app.src.user.model import User, Role
from app.src.reservation.model import Reservation, ReservationStatus
from threading import Thread


@pytest.fixture()
def dummy_user():
    return User(id=1, user_name="test", email="test@example.com", role=Role.ADMIN)


@pytest.mark.integration
class TestReservationUpdate:

    @pytest.fixture()
    def dummy_reservations(self):
        reservations = []
        for i in range(10):
            reservations.append(
                Reservation(
                    id=i,
                    user_id=1,
                    reservation_name=f"test-{i}",
                    start_time=datetime.datetime(2025, 5, 1, 10, 0),
                    end_time=datetime.datetime(2025, 5, 1, 11, 0),
                    status=ReservationStatus.CONFIRMED,
                    number_of_people=5000,
                )
            )
        return reservations

    def test_update_reservation_when_number_of_people_under_limit(
        self, db_session, dummy_user, dummy_reservations
    ):
        """
        예약 인원이 5만명 이하인 경우 예약 수정 가능해야 한다
        변경하려는 예약의 이전 정보는 제한사항 검사에 포함되지 않아야 한다.
        즉, 5만명이 예약되어 있던 예약 정보를 4만명으로 변경하는 것이 가능해야한다.
        """
        # given
        before_update_number_of_people = MAX_CAPACITY
        after_update_number_of_people = 40000

        dummy_reservations[0].number_of_people = before_update_number_of_people
        db_session.add(dummy_user)
        db_session.add(dummy_reservations[0])
        db_session.commit()

        # when
        result = reservation_service.update_reservation(
            db_session,
            dummy_user,
            dummy_reservations[0].id,
            UpdateReservationRequest(number_of_people=after_update_number_of_people),
        )

        # then
        assert result.number_of_people == after_update_number_of_people

    def test_not_update_reservation_when_number_of_people_over_limit(
        self, db_session, dummy_user, dummy_reservations
    ):
        """예약하려는 스케줄에 5만명 제한을 초과하면, 예외 발생"""
        # given
        db_session.add(dummy_user)
        for reservation in dummy_reservations:
            db_session.add(reservation)
        db_session.commit()

        after_update_number_of_people = MAX_CAPACITY

        # when
        with pytest.raises(HTTPException) as e:
            reservation_service.update_reservation(
                db_session,
                dummy_user,
                dummy_reservations[0].id,
                UpdateReservationRequest(
                    number_of_people=after_update_number_of_people
                ),
            )

        # then
        assert e.value.status_code == 400


@pytest.mark.integration
class TestReservationConcurrency:
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
                target=self.confirm_with_new_session,
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
        self,
        db_session,
        user: User,
        reservation_id: int,
        success_ids: list,
        failed_ids: list,
    ):
        try:
            reservation_service.confirm_reservation(db_session, user, reservation_id)
            success_ids.append(reservation_id)
        except HTTPException as e:
            print(e)
            failed_ids.append(reservation_id)

import datetime
from fastapi import HTTPException
import pytest
from unittest.mock import MagicMock

from app.src.reservation.dto.request.create_reservation_request import (
    CreateReservationRequest,
)
from app.src.reservation.dto.request.get_available_schedule_request import (
    GetAvailableScheduleRequest,
)
from app.src.reservation.dto.request.get_reservations_request import (
    GetReservationsRequest,
)
from app.src.reservation.dto.request.update_reservation_request import (
    UpdateReservationRequest,
)
from app.src.reservation.model import Reservation, ReservationStatus
from app.src.reservation import service as reservation_service
from app.src.reservation.utils.constants import DATETIME_FORMAT, MAX_CAPACITY
from app.src.user.model import Role, User


@pytest.fixture
def mock_db():
    return MagicMock()


class TestFindAllByDate:
    """find_all_by_date 함수 테스트"""

    @pytest.fixture(scope="class")
    def dummy_user(self):
        return User(
            id=1,
            user_name="test",
            email="test@test.com",
        )

    @pytest.fixture(scope="class")
    def dummy_request(self):
        now = datetime.datetime.now() + datetime.timedelta(days=3)

        return GetReservationsRequest(
            start=f"{now.year}-{now.month:02d}-{now.day:02d}",
            end=f"{now.year}-{now.month:02d}-{now.day:02d}",
            page=1,
            limit=10,
        )

    def test_call_user_function_and_return_empty_list_when_user_role_is_user_and_no_reservation(
        self, mocker, dummy_request, dummy_user
    ):
        """조회 사용자 권한이 일반 사용자라면, find_all_by_user_and_date_and_page 함수 호출"""
        # given
        dummy_user.role = Role.USER

        mock_admin_function = mocker.patch(
            "app.src.reservation.repository.find_all_by_date_and_page",
            return_value=[],
        )
        mock_user_function = mocker.patch(
            "app.src.reservation.repository.find_all_by_user_and_date_and_page",
            return_value=[],
        )

        # when
        result = reservation_service.find_all_by_date(
            mock_db, dummy_user, dummy_request
        )

        # then
        assert len(result) == 0
        assert mock_admin_function.call_count == 0
        assert mock_user_function.call_count == 1

    def test_call_admin_function_and_return_empty_list_when_user_role_is_admin_and_no_reservation(
        self, mocker, dummy_request, dummy_user
    ):
        """조회 사용자 권한이 관리자라면, find_all_by_date_and_page 함수 호출"""
        # given
        dummy_user.role = Role.ADMIN

        mock_admin_function = mocker.patch(
            "app.src.reservation.repository.find_all_by_date_and_page",
            return_value=[],
        )
        mock_user_function = mocker.patch(
            "app.src.reservation.repository.find_all_by_user_and_date_and_page",
            return_value=[],
        )

        # when
        result = reservation_service.find_all_by_date(
            mock_db, dummy_user, dummy_request
        )

        # then
        assert len(result) == 0
        assert mock_admin_function.call_count == 1
        assert mock_user_function.call_count == 0

    def test_return_all_reservations_when_reservation_exists(
        self, mocker, dummy_request, dummy_user
    ):
        """조회 시 예약 상태에 관계없이 모든 예약 반환"""
        # given
        dummy_user.role = Role.USER
        reservations = [
            Reservation(
                id=1,
                reservation_name="test",
                start_time=dummy_request.start,
                end_time=dummy_request.end,
                number_of_people=10000,
                status=ReservationStatus.PENDING,
                created_at=datetime.datetime.now(),
            ),
            Reservation(
                id=2,
                reservation_name="test2",
                start_time=dummy_request.start,
                end_time=dummy_request.end,
                number_of_people=10000,
                status=ReservationStatus.CONFIRMED,
                created_at=datetime.datetime.now(),
            ),
            Reservation(
                id=3,
                reservation_name="test3",
                start_time=dummy_request.start,
                end_time=dummy_request.end,
                number_of_people=10000,
                status=ReservationStatus.CANCELLED,
                created_at=datetime.datetime.now(),
            ),
        ]

        mocker.patch(
            "app.src.reservation.repository.find_all_by_user_and_date_and_page",
            return_value=reservations,
        )

        # when
        result = reservation_service.find_all_by_date(
            mock_db, dummy_user, dummy_request
        )

        # then
        assert len(result) == len(reservations)
        assert {res.id for res in result} == {res.id for res in reservations}


class TestFindByID:
    """find_by_id 함수 테스트"""

    @pytest.fixture(scope="class")
    def dummy_user(self):
        return User(
            id=1,
            user_name="test",
            email="test@test.com",
        )

    def test_raise_403_exception_when_user_role_is_user_and_not_reservation_owner(
        self, mocker, dummy_user
    ):
        """조회 권한이 사용자이고, 해당 예약자가 아닐 때 403 예외 발생"""
        # given
        dummy_user.role = Role.USER
        now = datetime.datetime.now()
        reservation_id = 1

        mocker.patch(
            "app.src.reservation.repository.find_by_id",
            return_value=Reservation(
                id=reservation_id,
                reservation_name="test",
                start_time=now,
                end_time=now + datetime.timedelta(hours=1),
                number_of_people=10000,
                status=ReservationStatus.PENDING,
                created_at=datetime.datetime.now(),
                user_id=dummy_user.id + 1,
            ),
        )

        # when - then
        with pytest.raises(HTTPException) as e:
            reservation_service.find_by_id(mock_db, dummy_user, reservation_id)

        # then
        assert e.value.status_code == 403
        assert e.value.detail == "조회할 수 없는 예약 정보입니다."

    def test_return_reservation_when_user_role_is_user_and_reservation_owner(
        self, mocker, dummy_user
    ):
        """조회 권한이 사용자이고, 해당 예약자일 때 예약 반환"""
        # given
        dummy_user.role = Role.USER
        now = datetime.datetime.now()
        reservation_id = 1

        mocker.patch(
            "app.src.reservation.repository.find_by_id",
            return_value=Reservation(
                id=reservation_id,
                reservation_name="test",
                start_time=now,
                end_time=now + datetime.timedelta(hours=1),
                number_of_people=10000,
                status=ReservationStatus.PENDING,
                created_at=datetime.datetime.now(),
                user_id=dummy_user.id,
            ),
        )

        # when
        result = reservation_service.find_by_id(mock_db, dummy_user, reservation_id)

        # then
        assert result.id == reservation_id

    def test_return_reservation_when_user_role_admin_and_not_reservation_owner(
        self, mocker, dummy_user
    ):
        """조회 권한이 관리자 일때, 예약자가 아니더라도 조회 가능"""
        # given
        dummy_user.role = Role.ADMIN
        now = datetime.datetime.now()
        reservation_id = 1
        reservation_owner = dummy_user.id + 1

        mocker.patch(
            "app.src.reservation.repository.find_by_id",
            return_value=Reservation(
                id=reservation_id,
                reservation_name="test",
                start_time=now,
                end_time=now + datetime.timedelta(hours=1),
                number_of_people=10000,
                status=ReservationStatus.PENDING,
                created_at=datetime.datetime.now(),
                user_id=reservation_owner,
            ),
        )

        # when
        result = reservation_service.find_by_id(mock_db, dummy_user, reservation_id)

        # then
        assert result.id == reservation_id

    def test_return_reservation_when_user_role_admin_and_reservation_owner(
        self, mocker, dummy_user
    ):
        """조회 권한이 관리자 일때, 자신의 예약 조회 가능"""
        # given
        dummy_user.role = Role.ADMIN
        now = datetime.datetime.now()
        reservation_id = 1

        mocker.patch(
            "app.src.reservation.repository.find_by_id",
            return_value=Reservation(
                id=reservation_id,
                reservation_name="test",
                start_time=now,
                end_time=now + datetime.timedelta(hours=1),
                number_of_people=10000,
                status=ReservationStatus.PENDING,
                created_at=datetime.datetime.now(),
                user_id=dummy_user.id,
            ),
        )

        # when
        result = reservation_service.find_by_id(mock_db, dummy_user, reservation_id)

        # then
        assert result.id == reservation_id


class TestFindAvailableSchedules:
    """find_available_schedules 함수 테스트"""

    @pytest.fixture(scope="class", autouse=True)
    def dummy_request(self):
        now = datetime.datetime.now() + datetime.timedelta(days=3)
        return GetAvailableScheduleRequest(
            start=f"{now.year}-{now.month:02d}-{now.day:02d}",
            end=f"{now.year}-{now.month:02d}-{now.day:02d}",
        )

    def test_full_capacity_when_no_reservations(self, mocker, dummy_request):
        """조회 구간에 확정된 예약이 없으면, 조회 구간 전체가 50_000명 예약 가능 반환"""
        # given
        mocker.patch(
            "app.src.reservation.repository.find_all_by_range_and_status",
            return_value=[],
        )

        # when
        result = reservation_service.find_available_schedules(mock_db, dummy_request)

        # then
        assert len(result) == 1
        assert result[0].start == dummy_request.start
        assert result[0].end == dummy_request.end
        assert result[0].available_capacity == MAX_CAPACITY

    def test_decrease_capacity_when_reservations_exist(self, mocker, dummy_request):
        """CONFIRMED 예약 존재 -> 해당 구간 예약 가능 인원이 줄어야 한다"""
        # given
        number_of_people = 10000
        mocker.patch(
            "app.src.reservation.repository.find_all_by_range_and_status",
            return_value=[
                Reservation(
                    id=1,
                    start_time=dummy_request.start,
                    end_time=dummy_request.end,
                    number_of_people=number_of_people,
                    status=ReservationStatus.CONFIRMED,
                )
            ],
        )

        # when
        result = reservation_service.find_available_schedules(mock_db, dummy_request)

        # then
        assert len(result) == 1
        assert result[0].available_capacity == MAX_CAPACITY - number_of_people
        assert result[0].start == dummy_request.start
        assert result[0].end == dummy_request.end

    def test_ignore_not_confirmed_reservations(self, mocker, dummy_request):
        """PENDING 예약 존재 -> 예약 가능 인원이 줄지 않아야 한다"""
        # given
        number_of_people = 10000
        mocker.patch(
            "app.src.reservation.repository.find_all_by_range_and_status",
            return_value=[
                Reservation(
                    id=1,
                    start_time=dummy_request.start,
                    end_time=dummy_request.end,
                    number_of_people=number_of_people,
                    status=ReservationStatus.PENDING,
                ),
                Reservation(
                    id=2,
                    start_time=dummy_request.start,
                    end_time=dummy_request.end,
                    number_of_people=number_of_people,
                    status=ReservationStatus.CANCELLED,
                ),
                Reservation(
                    id=3,
                    start_time=dummy_request.start,
                    end_time=dummy_request.end,
                    number_of_people=number_of_people,
                    status=ReservationStatus.REJECTED,
                ),
            ],
        )

        # when
        result = reservation_service.find_available_schedules(mock_db, dummy_request)

        # then
        assert len(result) == 1
        assert result[0].available_capacity == MAX_CAPACITY
        assert result[0].start == dummy_request.start
        assert result[0].end == dummy_request.end

    def test_return_multiple_schedules_when_multiple_reservations_exist_each_slot(
        self, mocker, dummy_request
    ):
        """서로 다른 예약이 서로 다른 구간에 존재하면, 각 구간별로 예약 가능 인원을 반환해야한다."""
        # given
        number_of_people = 10000
        mocker.patch(
            "app.src.reservation.repository.find_all_by_range_and_status",
            return_value=[
                Reservation(
                    id=1,
                    start_time=dummy_request.start,
                    end_time=dummy_request.end,
                    number_of_people=number_of_people,
                    status=ReservationStatus.CONFIRMED,
                ),
                Reservation(
                    id=2,
                    start_time=dummy_request.start + datetime.timedelta(minutes=10),
                    end_time=dummy_request.end,
                    number_of_people=number_of_people,
                    status=ReservationStatus.CONFIRMED,
                ),
            ],
        )

        # when
        result = reservation_service.find_available_schedules(mock_db, dummy_request)

        # then
        assert len(result) == 2
        assert result[0].available_capacity == MAX_CAPACITY - number_of_people
        assert result[1].available_capacity == MAX_CAPACITY - 2 * number_of_people
        assert result[0].start == dummy_request.start
        assert result[1].start == dummy_request.start + datetime.timedelta(minutes=10)
        assert result[0].end == result[1].start
        assert result[1].end == dummy_request.end

    def test_return_multiple_schedules_when_multiple_reservations_exist_equal_slot(
        self, mocker, dummy_request
    ):
        """서로 다른 예약이 동일한 구간에 존재하면, 해당 인원수를 통합해 반환해야한다."""
        # given
        number_of_people = 10000
        mocker.patch(
            "app.src.reservation.repository.find_all_by_range_and_status",
            return_value=[
                Reservation(
                    id=1,
                    start_time=dummy_request.start,
                    end_time=dummy_request.end,
                    number_of_people=number_of_people,
                    status=ReservationStatus.CONFIRMED,
                ),
                Reservation(
                    id=2,
                    start_time=dummy_request.start,
                    end_time=dummy_request.end,
                    number_of_people=number_of_people,
                    status=ReservationStatus.CONFIRMED,
                ),
            ],
        )

        # when
        result = reservation_service.find_available_schedules(mock_db, dummy_request)

        # then
        assert len(result) == 1
        assert result[0].available_capacity == MAX_CAPACITY - 2 * number_of_people
        assert result[0].start == dummy_request.start
        assert result[0].end == dummy_request.end


class TestCreateReservation:
    """create_reservation 함수 테스트"""

    @pytest.fixture(scope="class")
    def dummy_user(self):
        return User(
            id=1,
            user_name="test",
            email="test@test.com",
            role=Role.USER,
        )

    @pytest.fixture(scope="class")
    def dummy_request(self):
        min_date = datetime.datetime.now() + datetime.timedelta(days=3)

        return CreateReservationRequest(
            start=f"{min_date.year}-{min_date.month:02d}-{min_date.day:02d} {min_date.hour+1:02d}:00",
            end=f"{min_date.year}-{min_date.month:02d}-{min_date.day:02d} {min_date.hour+2:02d}:00",
            number_of_people=10000,
            reservation_name="test",
        )

    def test_raise_error_when_number_of_people_over_limit(
        self, mocker, dummy_user, dummy_request
    ):
        """해당 구간에 이미 5만명의 제한으로 인해 예약 불가능한 경우, 예약 불가능 예외 발생"""
        # given
        reservation_id = 1

        validation_function = mocker.patch(
            "app.src.reservation.repository.find_all_by_range_and_status",
            return_value=[
                Reservation(
                    id=1,
                    start_time=dummy_request.start,
                    end_time=dummy_request.end,
                    number_of_people=MAX_CAPACITY,
                    status=ReservationStatus.CONFIRMED,
                )
            ],
        )
        create_function = mocker.patch(
            "app.src.reservation.repository.create",
            return_value=Reservation(id=reservation_id),
        )

        # when - then
        with pytest.raises(HTTPException) as e:
            reservation_service.create_reservation(mock_db, dummy_user, dummy_request)

        assert e.value.status_code == 400
        assert validation_function.call_count == 1
        assert create_function.call_count == 0

    def test_create_reservation_when_number_of_people_under_limit(
        self, mocker, dummy_user, dummy_request
    ):
        """해당 구간에 이미 5만명의 제한을 통과하면 예약 가능"""
        # given
        reservation_id = 1

        validation_function = mocker.patch(
            "app.src.reservation.repository.find_all_by_range_and_status",
            return_value=[
                Reservation(
                    id=1,
                    start_time=dummy_request.start,
                    end_time=dummy_request.end,
                    number_of_people=MAX_CAPACITY - dummy_request.number_of_people,
                    status=ReservationStatus.CONFIRMED,
                )
            ],
        )
        create_function = mocker.patch(
            "app.src.reservation.repository.create",
            return_value=Reservation(
                id=reservation_id,
                start_time=dummy_request.start,
                end_time=dummy_request.end,
                number_of_people=dummy_request.number_of_people,
                status=ReservationStatus.PENDING,
                created_at=datetime.datetime.now(),
            ),
        )

        # when
        result = reservation_service.create_reservation(
            mock_db, dummy_user, dummy_request
        )

        # then
        assert result.id == reservation_id
        assert validation_function.call_count == 1
        assert create_function.call_count == 1


class TestConfirmReservation:
    """confirm_reservation 함수 테스트"""

    @pytest.fixture(scope="class")
    def dummy_user(self):
        return User(
            id=1,
            user_name="test",
            email="test@test.com",
            role=Role.ADMIN,
        )

    def test_raise_error_when_reservation_not_found(self, mocker, dummy_user):
        """존재하지 않는 예약을 승인하려고 하면 예외 발생"""
        # given
        reservation_id = 1

        find_function = mocker.patch(
            "app.src.reservation.repository.find_by_id",
            return_value=None,
        )
        validation_function = mocker.patch(
            "app.src.reservation.repository.find_all_by_range_and_status",
            return_value=[Reservation(id=1)],
        )

        # when - then
        with pytest.raises(HTTPException) as e:
            reservation_service.confirm_reservation(mock_db, dummy_user, reservation_id)

        # then
        assert e.value.status_code == 404
        assert find_function.call_count == 1
        assert validation_function.call_count == 0

    def test_raise_error_when_reservation_is_already_confirmed(
        self, mocker, dummy_user
    ):
        """예약이 이미 확정된 경우 예외 발생"""
        # given
        reservation_id = 1

        find_function = mocker.patch(
            "app.src.reservation.repository.find_by_id",
            return_value=Reservation(
                id=reservation_id,
                status=ReservationStatus.CONFIRMED,
            ),
        )
        validation_function = mocker.patch(
            "app.src.reservation.repository.find_all_by_range_and_status",
            return_value=[Reservation(id=1)],
        )

        # when - then
        with pytest.raises(HTTPException) as e:
            reservation_service.confirm_reservation(mock_db, dummy_user, reservation_id)

        # then
        assert e.value.status_code == 400
        assert find_function.call_count == 1
        assert validation_function.call_count == 0

    def test_raise_error_when_reservation_is_cancelled(self, mocker, dummy_user):
        """예약이 취소된 경우 예외 발생"""
        # given
        reservation_id = 1

        find_function = mocker.patch(
            "app.src.reservation.repository.find_by_id",
            return_value=Reservation(
                id=reservation_id,
                status=ReservationStatus.CANCELLED,
            ),
        )
        validation_function = mocker.patch(
            "app.src.reservation.repository.find_all_by_range_and_status",
            return_value=[Reservation(id=1)],
        )

        # when - then
        with pytest.raises(HTTPException) as e:
            reservation_service.confirm_reservation(mock_db, dummy_user, reservation_id)

        # then
        assert e.value.status_code == 400
        assert find_function.call_count == 1
        assert validation_function.call_count == 0

    def test_raise_error_when_number_of_people_over_limit(self, mocker, dummy_user):
        """예약 인원이 5만명을 초과하면 예외 발생"""
        # given
        reservation_id = 1
        min_date = datetime.datetime.now() + datetime.timedelta(days=3)

        find_function = mocker.patch(
            "app.src.reservation.repository.find_by_id",
            return_value=Reservation(
                id=reservation_id,
                start_time=min_date,
                end_time=min_date + datetime.timedelta(hours=1),
                number_of_people=MAX_CAPACITY,
                status=ReservationStatus.PENDING,
            ),
        )
        validation_function = mocker.patch(
            "app.src.reservation.repository.find_all_by_range_and_status",
            return_value=[
                Reservation(
                    id=1,
                    start_time=min_date,
                    end_time=min_date + datetime.timedelta(hours=1),
                    number_of_people=MAX_CAPACITY,
                    status=ReservationStatus.CONFIRMED,
                )
            ],
        )
        # when - then
        with pytest.raises(HTTPException) as e:
            reservation_service.confirm_reservation(mock_db, dummy_user, reservation_id)

        # then
        assert e.value.status_code == 400
        assert find_function.call_count == 1
        assert validation_function.call_count == 1

    def test_raise_error_when_number_of_people_under_limit(self, mocker, dummy_user):
        """예약 인원이 5만명 미만이면 예약 확정"""
        # given
        reservation_id = 1
        number_of_people = 10000
        min_date = datetime.datetime.now() + datetime.timedelta(days=3)

        mocker.patch(
            "app.src.reservation.repository.find_by_id",
            return_value=Reservation(
                id=reservation_id,
                start_time=min_date,
                end_time=min_date + datetime.timedelta(hours=1),
                number_of_people=number_of_people,
                status=ReservationStatus.PENDING,
                created_at=datetime.datetime.now(),
            ),
        )
        mocker.patch(
            "app.src.reservation.repository.find_all_by_range_and_status",
            return_value=[
                Reservation(
                    id=reservation_id + 1,
                    start_time=min_date,
                    end_time=min_date + datetime.timedelta(hours=1),
                    number_of_people=MAX_CAPACITY - number_of_people,
                    status=ReservationStatus.CONFIRMED,
                )
            ],
        )

        # when
        result = reservation_service.confirm_reservation(
            mock_db, dummy_user, reservation_id
        )

        # then
        assert result.id == reservation_id
        assert result.status == ReservationStatus.CONFIRMED


class TestUpdateReservation:
    """update_reservation 함수 테스트"""

    @pytest.fixture(scope="class")
    def dummy_user(self):
        reserved_start = datetime.datetime.now() + datetime.timedelta(days=3)
        reserved_end = reserved_start + datetime.timedelta(hours=1)
        return User(
            id=1,
            user_name="test",
            email="test@test.com",
        )

    def test_raise_error_when_reservation_not_found(self, mocker, dummy_user):
        """예약이 존재하지 않으면, 예외발생"""
        # given
        reservation_id = 1
        request = UpdateReservationRequest(number_of_people=10000)

        find_function = mocker.patch(
            "app.src.reservation.repository.find_by_id", return_value=[]
        )
        validation_function = mocker.patch(
            "app.src.reservation.repository.find_all_by_range_and_status",
            return_value=[Reservation(id=1)],
        )

        # when - then
        with pytest.raises(HTTPException) as e:
            reservation_service.update_reservation(
                mock_db, dummy_user, reservation_id, request
            )

        # then
        assert e.value.status_code == 404
        assert find_function.call_count == 1
        assert validation_function.call_count == 0

    def test_raise_error_when_user_is_not_reservation_owner(self, mocker, dummy_user):
        """요청자가 일반 사용자면서, 해당 예약의 예약자가 아니면 예외 발생"""
        # given
        reservation_id = 1
        dummy_user.role = Role.USER
        request = UpdateReservationRequest(number_of_people=10000)

        find_function = mocker.patch(
            "app.src.reservation.repository.find_by_id",
            return_value=Reservation(
                id=reservation_id,
                user_id=dummy_user.id + 1,
                status=ReservationStatus.PENDING,
            ),
        )
        validation_function = mocker.patch(
            "app.src.reservation.repository.find_all_by_range_and_status",
            return_value=[Reservation(id=1)],
        )

        # when - then
        with pytest.raises(HTTPException) as e:
            reservation_service.update_reservation(
                mock_db, dummy_user, reservation_id, request
            )

        # then
        assert e.value.status_code == 403
        assert find_function.call_count == 1
        assert validation_function.call_count == 0

    def test_raise_error_when_reservation_is_cancelled(self, mocker, dummy_user):
        """요청자는 유효하지만, 예약이 CANCELLED 상태라면 예외 발생"""
        # given
        reservation_id = 1
        request = UpdateReservationRequest(number_of_people=10000)

        find_function = mocker.patch(
            "app.src.reservation.repository.find_by_id",
            return_value=Reservation(
                id=reservation_id,
                user_id=dummy_user.id,
                status=ReservationStatus.CANCELLED,
            ),
        )
        validation_function = mocker.patch(
            "app.src.reservation.repository.find_all_by_range_and_status",
            return_value=[Reservation(id=1)],
        )

        # when - then
        with pytest.raises(HTTPException) as e:
            reservation_service.update_reservation(
                mock_db, dummy_user, reservation_id, request
            )

        # then
        assert e.value.status_code == 400
        assert find_function.call_count == 1
        assert validation_function.call_count == 0

    def test_raise_error_when_reservation_is_confirmed(self, mocker, dummy_user):
        """요청자는 유효하지만, 예약이 CONFIRMED 상태라면 예외 발생"""
        # given
        reservation_id = 1
        request = UpdateReservationRequest(number_of_people=10000)

        find_function = mocker.patch(
            "app.src.reservation.repository.find_by_id",
            return_value=Reservation(
                id=reservation_id,
                user_id=dummy_user.id,
                status=ReservationStatus.CONFIRMED,
            ),
        )
        validation_function = mocker.patch(
            "app.src.reservation.repository.find_all_by_range_and_status",
            return_value=[Reservation(id=1)],
        )

        # when - then
        with pytest.raises(HTTPException) as e:
            reservation_service.update_reservation(
                mock_db, dummy_user, reservation_id, request
            )

        # then
        assert e.value.status_code == 400
        assert find_function.call_count == 1
        assert validation_function.call_count == 0

    def test_raise_error_when_date_change_and_number_of_people_over_limit(
        self, mocker, dummy_user
    ):
        """요청자는 유효하지만, 예약이 시작/종료 시간 변경 시 5만명 제한을 초과하면 예외 발생"""
        # given
        reservation_id = 1
        number_of_people = 10000
        min_date = datetime.datetime.now() + datetime.timedelta(days=3)
        start = f"{min_date.year}-{min_date.month:02d}-{min_date.day:02d} {min_date.hour+1:02d}:00"
        end = f"{min_date.year}-{min_date.month:02d}-{min_date.day:02d} {min_date.hour+2:02d}:00"

        request = UpdateReservationRequest(start=start, end=end)

        find_function = mocker.patch(
            "app.src.reservation.repository.find_by_id",
            return_value=Reservation(
                id=reservation_id,
                user_id=dummy_user.id,
                number_of_people=number_of_people,
                status=ReservationStatus.PENDING,
            ),
        )
        validation_function = mocker.patch(
            "app.src.reservation.repository.find_all_by_range_and_status",
            return_value=[
                Reservation(
                    id=reservation_id + 1,
                    start_time=request.start,
                    end_time=request.end,
                    number_of_people=MAX_CAPACITY,
                    status=ReservationStatus.CONFIRMED,
                )
            ],
        )

        # when - then
        with pytest.raises(HTTPException) as e:
            reservation_service.update_reservation(
                mock_db, dummy_user, reservation_id, request
            )

        # then
        assert e.value.status_code == 400
        assert find_function.call_count == 1
        assert validation_function.call_count == 1

    def test_raise_error_when_number_of_people_change_and_number_of_people_over_limit(
        self, mocker, dummy_user
    ):
        """요청자는 유효하지만, 예약인원 변경 시 5만명 제한을 초과하면 예외 발생"""
        # given
        reservation_id = 1
        before_number_of_people = 1
        after_number_of_people = 10000
        min_date = datetime.datetime.now() + datetime.timedelta(days=3)
        start = datetime.datetime.strptime(
            f"{min_date.year}-{min_date.month:02d}-{min_date.day:02d} {min_date.hour+1:02d}:00",
            DATETIME_FORMAT,
        )
        end = datetime.datetime.strptime(
            f"{min_date.year}-{min_date.month:02d}-{min_date.day:02d} {min_date.hour+2:02d}:00",
            DATETIME_FORMAT,
        )
        request = UpdateReservationRequest(number_of_people=after_number_of_people)

        find_function = mocker.patch(
            "app.src.reservation.repository.find_by_id",
            return_value=Reservation(
                id=reservation_id,
                user_id=dummy_user.id,
                start_time=start,
                end_time=end,
                number_of_people=before_number_of_people,
                status=ReservationStatus.PENDING,
            ),
        )
        validation_function = mocker.patch(
            "app.src.reservation.repository.find_all_by_range_and_status",
            return_value=[
                Reservation(
                    id=reservation_id + 1,
                    start_time=start,
                    end_time=end,
                    number_of_people=MAX_CAPACITY - before_number_of_people,
                    status=ReservationStatus.CONFIRMED,
                )
            ],
        )

        # when - then
        with pytest.raises(HTTPException) as e:
            reservation_service.update_reservation(
                mock_db, dummy_user, reservation_id, request
            )

        # then
        assert e.value.status_code == 400
        assert find_function.call_count == 1
        assert validation_function.call_count == 1

    def test_update_reservation_when_number_of_people_under_limit(
        self, mocker, dummy_user
    ):
        """요청자가 유효하면서, 예약 변경 시 5만명 제한을 초과하지 않으면 예약 수정"""
        # given
        reservation_id = 1
        before_number_of_people = 1
        min_date = datetime.datetime.now() + datetime.timedelta(days=3)
        start = datetime.datetime.strptime(
            f"{min_date.year}-{min_date.month:02d}-{min_date.day:02d} {min_date.hour+1:02d}:00",
            DATETIME_FORMAT,
        )
        end = datetime.datetime.strptime(
            f"{min_date.year}-{min_date.month:02d}-{min_date.day:02d} {min_date.hour+2:02d}:00",
            DATETIME_FORMAT,
        )
        request = UpdateReservationRequest(number_of_people=MAX_CAPACITY)

        mocker.patch(
            "app.src.reservation.repository.find_by_id",
            return_value=Reservation(
                id=reservation_id,
                user_id=dummy_user.id,
                start_time=start,
                end_time=end,
                number_of_people=before_number_of_people,
                status=ReservationStatus.PENDING,
                created_at=datetime.datetime.now(),
            ),
        )
        mocker.patch(
            "app.src.reservation.repository.find_all_by_range_and_status",
            return_value=[],
        )

        # when
        result = reservation_service.update_reservation(
            mock_db, dummy_user, reservation_id, request
        )

        # then
        assert result.id == reservation_id
        assert result.number_of_people == MAX_CAPACITY

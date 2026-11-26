import pytest

from app.models import DeviceCreate
from app.repositories.device_repository import InMemoryDeviceRepository
from app.services.device_service import (
    DeviceAlreadyExistsError,
    DeviceNotFoundError,
    DeviceService,
)


def make_service() -> tuple[InMemoryDeviceRepository, DeviceService]:
    repository = InMemoryDeviceRepository()
    return repository, DeviceService(repository)


def make_device(status: str = "online") -> DeviceCreate:
    return DeviceCreate(
        device_id="RTR-101",
        name="Branch Router",
        device_type="router",
        ip_address="192.168.10.1",
        status=status,
    )


def test_register_device() -> None:
    _, service = make_service()

    registered = service.register(make_device())

    assert registered.device_id == "RTR-101"
    assert registered.status == "online"


def test_duplicate_registration_raises_error() -> None:
    _, service = make_service()
    service.register(make_device())

    with pytest.raises(DeviceAlreadyExistsError):
        service.register(make_device())


def test_missing_device_raises_error() -> None:
    _, service = make_service()

    with pytest.raises(DeviceNotFoundError):
        service.get("MISSING")


def test_initial_offline_registration_does_not_create_alert() -> None:
    repository, service = make_service()

    service.register(make_device(status="offline"))

    assert repository.list_alerts() == []


def test_online_to_offline_creates_one_alert() -> None:
    repository, service = make_service()
    service.register(make_device())

    service.update_status("RTR-101", "offline")

    alerts = repository.list_alerts()
    assert len(alerts) == 1
    assert alerts[0].device_id == "RTR-101"
    assert "online to offline" in alerts[0].message
    assert alerts[0].timestamp.utcoffset().total_seconds() == 0


def test_repeated_offline_update_does_not_create_another_alert() -> None:
    repository, service = make_service()
    service.register(make_device())

    service.update_status("RTR-101", "offline")
    service.update_status("RTR-101", "offline")

    assert len(repository.list_alerts()) == 1
import pytest

from fakes import device
from fakes import receiver


@pytest.fixture
def fake_receiver():
    yield receiver.FakeReceiver()


@pytest.fixture
def fake_device():
    yield device.FakeDevice()

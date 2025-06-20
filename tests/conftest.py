import pytest

from fakes import device
from fakes import receiver
from logitech_receiver import hidpp20_constants


@pytest.fixture
def fake_receiver():
    yield receiver.FakeReceiver()


@pytest.fixture
def fake_device():
    yield device.FakeDevice()


@pytest.fixture
def fake_device_init():
    yield device.FakeDevice


@pytest.fixture
def fake_device_with_gesture_support():
    yield device.FakeDevice(
        "GESTURES", responses=device.responses_gestures, feature=hidpp20_constants.SupportedFeature.GESTURE_2
    )

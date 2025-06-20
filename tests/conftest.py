import pytest

from fakes import receiver


@pytest.fixture
def fake_receiver():
    yield receiver.MockReceiver()
    yield receiver.FakeReceiver()

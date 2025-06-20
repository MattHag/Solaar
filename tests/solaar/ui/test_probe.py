from unittest import mock

from logitech_receiver.hidpp10_constants import ErrorCode
from solaar.cli.probe import run


def test_run_register_errors(fake_receiver):
    mock_args = mock.Mock()
    mock_args.receiver = False

    # Define expected addresses to be called in order
    expected_addresses = []

    for reg in range(0, 0xFF):
        expected_addresses.append((0x8100 | reg, 0))  # First short call, returns invalid_value (continue)
        expected_addresses.append((0x8100 | reg, 1))  # Second short call, returns invalid_address (stop here)

        expected_addresses.append((0x8100 | (0x200 + reg), 0))  # First long call, returns invalid_value (continue)
        expected_addresses.append((0x8100 | (0x200 + reg), 1))  # Second long call, returns invalid_address (stop here)

    # To record the actual addresses called
    called_addresses = []

    def mock_base_request(handle, devnumber, reg, sub, return_error=False):
        called_addresses.append((reg, sub))
        if sub == 0:
            return ErrorCode.INVALID_VALUE
        elif sub == 1:
            return ErrorCode.INVALID_ADDRESS
        return b"\x01\x02"

    with mock.patch("logitech_receiver.base.request", side_effect=mock_base_request), mock.patch(
        "solaar.cli.probe._print_receiver", return_value=None
    ):
        # Call the run function with mocked receivers and args (passing real find_receiver function)
        run([fake_receiver], mock_args, None, None)

        # Evaluate that the addresses called match the expected addresses
        assert (
            called_addresses == expected_addresses
        ), f"Called addresses {called_addresses} do not match expected {expected_addresses}"

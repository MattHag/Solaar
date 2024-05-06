import textwrap

from unittest import mock
from unittest.mock import mock_open

import pytest

from logitech_receiver import diversion
from logitech_receiver.diversion import rule_storage


def test_load_builtin_rules(rule_config):
    expected_rules = [
        [diversion.Key, diversion.KeyPress],
        [diversion.Key, diversion.KeyPress],
    ]

    with mock.patch("os.path.isfile", return_value=False):
        loaded_rules = rule_storage.load_config()

    assert len(loaded_rules.components) == 1  # predefined and user configured rules
    assert_expected_rules(loaded_rules, expected_rules)


@pytest.fixture
def rule_config():
    rule_content = """
    %YAML 1.3
    ---
    - MouseGesture: Mouse Left
    - KeyPress:
      - [Control_L, Alt_L, Left]
      - click
    ...
    ---
    - MouseGesture: Mouse Up
    - KeyPress:
      - [Super_L, Up]
      - click
    ...
    ---
    - Test: [thumb_wheel_up, 10]
    - KeyPress:
      - [Control_L, Page_Down]
      - click
    ...
    ---
    """
    return textwrap.dedent(rule_content)


def test_load_rule_from_yaml_file(rule_config):
    expected_rules = [
        [diversion.MouseGesture, diversion.KeyPress],
        [diversion.MouseGesture, diversion.KeyPress],
        [diversion.Test, diversion.KeyPress],
    ]

    with mock.patch("os.path.isfile", return_value=True):
        with mock.patch("builtins.open", new=mock_open(read_data=rule_config)):
            loaded_rules = rule_storage.load_config()

    assert len(loaded_rules.components) == 2  # predefined and user configured rules
    assert_expected_rules(loaded_rules, expected_rules)


def assert_expected_rules(loaded_rules, expected_rules):
    user_configured_rules = loaded_rules.components[0]
    assert isinstance(user_configured_rules, diversion.Rule)

    for components, expected_components in zip(user_configured_rules.components, expected_rules):
        for component, expected_component in zip(components.components, expected_components):
            assert isinstance(component, expected_component)


def test_diversion_rule():
    args = [
        {
            "Rule": [  # Implement problematic keys for Craft and MX Master
                {"Rule": [{"Key": ["Brightness Down", "pressed"]}, {"KeyPress": "XF86_MonBrightnessDown"}]},
                {"Rule": [{"Key": ["Brightness Up", "pressed"]}, {"KeyPress": "XF86_MonBrightnessUp"}]},
            ]
        },
    ]

    rule = diversion.Rule(args)

    assert len(rule.components) == 1
    root_rule = rule.components[0]
    assert isinstance(root_rule, diversion.Rule)

    assert len(root_rule.components) == 2
    for component in root_rule.components:
        assert isinstance(component, diversion.Rule)
        assert len(component.components) == 2

        key = component.components[0]
        assert isinstance(key, diversion.Key)
        key = component.components[1]
        assert isinstance(key, diversion.KeyPress)

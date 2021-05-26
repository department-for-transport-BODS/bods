from transit_odp.common.utils.choice_enum import ChoiceEnum


def test_choice_enum_renders_choices():
    # Setup
    class MyChoices(ChoiceEnum):
        DEPLOYING = "deploying"
        SYSTEM_ERROR = "system_error"
        FEED_UP = "feed_up"
        FEED_DOWN = "feed_down"

    # Test
    choices = MyChoices.choices()

    # Assert
    assert choices == [
        ("deploying", "DEPLOYING"),
        ("feed_down", "FEED_DOWN"),
        ("feed_up", "FEED_UP"),
        ("system_error", "SYSTEM_ERROR"),
    ]

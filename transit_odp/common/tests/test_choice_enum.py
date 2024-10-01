from transit_odp.common.utils.choice_enum import ChoiceEnum


def test_choice_enum_renders_choices():
    # Setup
    class MyChoices(ChoiceEnum):
        FIRST = "first"
        SECOND = "second"

    # Test
    choices = MyChoices.choices()

    # Assert
    assert choices == [
        ("first", "FIRST"),
        ("second", "SECOND"),
    ]

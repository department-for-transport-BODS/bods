from transit_odp.data_quality.constants import IncorrectNocObservation


def test_observation_type():
    assert IncorrectNocObservation.type == IncorrectNocObservation.category.value

import pytest

from transit_odp.otc.common import format_service_number

test_data_sets = [
    ("8", "39|8A|9"),
    ("Excel (A,B,C)", ""),
    ("418 (418W)(418R)", ""),
    ("88,08,81,891", ""),
    ("Louth Nipper", "40, 40a, 40B"),
    ("33 63", "33|33B"),
    ("L1:L2", "L1|L2"),
    ("192 Rural Rider", "193 Rural Rider"),
    ("WYN", "Wyn"),
    ("Ring & Ride (Coventry)", ""),
    ("298-1", "")
]

expected_results = [
    "8|39|8A|9",
    "Excel A|Excel B|Excel C",
    "418 (418W)|418 (418R)",
    "88|08|81|891",
    "Louth Nipper|40|40a|40B",
    "33|63|33B",
    "L1|L2",
    "192 Rural Rider|193 Rural Rider",
    "WYN",
    "Ring & Ride (Coventry)",
    "298-1"
]


@pytest.mark.parametrize(
    "test_data, expected_result", zip(test_data_sets, expected_results)
)
def test_format_service_number(test_data, expected_result):
    service_number = format_service_number(test_data[0], test_data[1])

    assert service_number == expected_result

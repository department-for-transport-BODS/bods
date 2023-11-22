from transit_odp.browse.templatetags.custom_filters import top_three_reasons
from transit_odp.disruptions.models import DisruptionReasonsEnum


class TestCustomFilters:
    def test_returned_reasons(self):
        data = {
            "constructionWork": 4,
            "ice": 10,
            "operatorCeasedTrading": 14,
            "accident": 15,
            "repairWork": 3,
            "insufficientDemand": 8,
            "signalFailure": 1,
            "roadClosed": 2,
            "industrialAction": 8,
            "maintenanceWork": 3,
            "routeDiversion": 1,
            "overcrowded": 5,
            "emergencyEngineeringWork": 4,
        }

        expected = [
            DisruptionReasonsEnum.accident.label,
            DisruptionReasonsEnum.operatorCeasedTrading.label,
            DisruptionReasonsEnum.ice.label,
        ]
        reasons = top_three_reasons(data)

        assert reasons == expected

    def test_returned_reasons_with_unknown_enums(self):
        data = {
            "operatorCeasedTrading": 14,
            "accident": 15,
            "unknowKey": 20,
            "industrialAction": 8,
        }

        expected = [
            DisruptionReasonsEnum.accident.label,
            DisruptionReasonsEnum.operatorCeasedTrading.label,
            DisruptionReasonsEnum.industrialAction.label,
        ]
        reasons = top_three_reasons(data)
        assert reasons == expected

    def test_returned_reasons_with_less_than_three_inputs(self):
        data = {"operatorCeasedTrading": 14, "accident": 15}

        expected = [
            DisruptionReasonsEnum.accident.label,
            DisruptionReasonsEnum.operatorCeasedTrading.label,
        ]
        reasons = top_three_reasons(data)
        assert reasons == expected

    def test_returned_reasons_without_input(self):
        data = {}

        expected = []
        reasons = top_three_reasons(data)
        assert not reasons

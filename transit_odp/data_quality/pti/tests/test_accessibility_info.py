import pytest

from transit_odp.data_quality.pti.factories import (
    ObservationFactory,
    RuleFactory,
    SchemaFactory,
)
from transit_odp.data_quality.pti.tests.conftest import JSONFile, TXCFile
from transit_odp.data_quality.pti.validators import PTIValidator


@pytest.mark.parametrize(
    "infos,expected",
    [
        (("nextStopIndicator", "stopAnnouncements"), True),
        (("nextStopIndicator", "other"), False),
        ((), True),
    ],
)
def test_passenger_info(infos, expected):
    xml = """
    <VehicleType>
        <VehicleTypeCode>BendyBus</VehicleTypeCode>
        <Description>Big, red and exploding</Description>
        <VehicleEquipment>
            <PassengerInfoEquipment>
                {0}
                <AccessibilityInfo>visualDisplays</AccessibilityInfo>
                <AccessibilityInfo>audioInformation</AccessibilityInfo>
            </PassengerInfoEquipment>
            <AccessVehicleEquipment>
                <LowFloor>true</LowFloor>
                <NumberOfSteps>1</NumberOfSteps>
                <BoardingHeight>0.50</BoardingHeight>
                <AutomaticDoors>true</AutomaticDoors>
            </AccessVehicleEquipment>
            <WheelchairVehicleEquipment>
                <NumberOfWheelChairAreas>3</NumberOfWheelChairAreas>
                <WidthOfAccessArea>1.0</WidthOfAccessArea>
                <HeightOfAccessArea>2.0</HeightOfAccessArea>
                <WheelchairTurningCircle>2.0</WheelchairTurningCircle>
            </WheelchairVehicleEquipment>
        </VehicleEquipment>
    </VehicleType>
    """
    info_temp = "<PassengerInfo>{0}</PassengerInfo>"
    passenge_infos = [info_temp.format(info) for info in infos]
    xml = xml.format("\n".join(passenge_infos))
    xml = TXCFile(xml)

    details = (
        "Accessibility information is optional. But if you are including "
        "it then it is required to be in the correct structure. Here, you have "
        "an incorrect structure in PassengerInfo field. The only values "
        "you can input in the field are 'nextStopIndicator' and 'stopAnnouncements'."
    )
    rule = RuleFactory(test="in(., 'nextStopIndicator', 'stopAnnouncements')")
    observation = ObservationFactory(
        details=details,
        context="//x:PassengerInfo",
        category="Accessibility Information",
        reference="2.4.3",
        rules=[rule],
    )
    schema = SchemaFactory(observations=[observation])
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)
    is_valid = pti.is_valid(xml)
    assert is_valid == expected


@pytest.mark.parametrize(
    "infos,expected",
    [
        (
            (
                "displaysForVisuallyImpaired",
                "audioInformation",
                "audioForHearingImpaired",
                "visualDisplays",
            ),
            True,
        ),
        (
            (
                "displaysForVisuallyImpaired",
                "audioInformation",
            ),
            True,
        ),
        (
            ("audioInformation", "visualDisplays", "other"),
            False,
        ),
        (("tactileGuidingStrips"), False),
        ((), True),
    ],
)
def test_accessibility_info(infos, expected):
    xml = """
    <VehicleType>
        <VehicleTypeCode>BendyBus</VehicleTypeCode>
        <Description>Big, red and exploding</Description>
        <VehicleEquipment>
            <PassengerInfoEquipment>
                <PassengerInfo>nextStopIndicator </PassengerInfo>
                <PassengerInfo>stopAnnouncements</PassengerInfo>
                {0}
            </PassengerInfoEquipment>
            <AccessVehicleEquipment>
                <LowFloor>true</LowFloor>
                <NumberOfSteps>1</NumberOfSteps>
                <BoardingHeight>0.50</BoardingHeight>
                <AutomaticDoors>true</AutomaticDoors>
            </AccessVehicleEquipment>
            <WheelchairVehicleEquipment>
                <NumberOfWheelChairAreas>3</NumberOfWheelChairAreas>
                <WidthOfAccessArea>1.0</WidthOfAccessArea>
                <HeightOfAccessArea>2.0</HeightOfAccessArea>
                <WheelchairTurningCircle>2.0</WheelchairTurningCircle>
            </WheelchairVehicleEquipment>
        </VehicleEquipment>
    </VehicleType>
    """
    info_temp = "<AccessibilityInfo>{0}</AccessibilityInfo>"
    accessibility_infos = [info_temp.format(info) for info in infos]
    xml = xml.format("\n".join(accessibility_infos))
    xml = TXCFile(xml)

    details = (
        "Accessibility information is optional. But if you are including "
        "it then it is required to be in the correct structure. Here, you have "
        "an incorrect structure in Accessibility field. The only values "
        "you can input in the field are  'audioInformation', 'audioForHearingImpaired',"
        " 'visualDisplays', 'displaysForVisuallyImpaired."
    )
    rule = RuleFactory(
        test=(
            "in(., 'displaysForVisuallyImpaired', 'audioInformation', "
            "'audioForHearingImpaired', 'visualDisplays')"
        )
    )
    observation = ObservationFactory(
        details=details,
        context="//x:AccessibilityInfo",
        category="Accessibility Information",
        reference="2.4.3",
        rules=[rule],
    )
    schema = SchemaFactory(observations=[observation])
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)
    is_valid = pti.is_valid(xml)
    assert is_valid == expected

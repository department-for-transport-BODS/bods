from transit_odp.timetables.transxchange import (
    TransXChangeDocument,
    GRID_LOCATION,
    WSG84_LOCATION,
)
from transit_odp.data_quality.pti.tests.conftest import TXCFile


def test_get_location_system():
    grid_stop_point = """
    <StopPoints>
        <StopPoint CreationDateTime="1970-01-01T01:00:00">
        <AtcoCode>999014AA766B</AtcoCode>
        <Descriptor>
            <CommonName>Dover (DFDS Ferry)</CommonName>
        </Descriptor>
        <Place>
            <NptgLocalityRef>E0047158</NptgLocalityRef>
            <LocalityName>Dover</LocalityName>
            <Location>
            <Translation>
                <Easting>633910</Easting>
                <Northing>141970</Northing>
                <Longitude>1.34172</Longitude>
                <Latitude>51.12922</Latitude>
            </Translation>
            </Location>
        </Place>
        <StopClassification>
            <StopType>busCoachTrolleyOnStreetPoint</StopType>
            <OnStreet>
            <Bus>
                <BusStopType>MKD</BusStopType>
                <TimingStatus>principalTimingPoint</TimingStatus>
                <MarkedPoint>
                <Bearing>
                    <CompassPoint>N</CompassPoint>
                </Bearing>
                </MarkedPoint>
            </Bus>
            </OnStreet>
        </StopClassification>
        <AdministrativeAreaRef>999</AdministrativeAreaRef>
        <Public>true</Public>
        </StopPoint>
    </StopPoints>
    """
    xml = TXCFile(grid_stop_point)
    doc = TransXChangeDocument(xml)
    stop_points = doc.get_stop_points()
    system = doc.get_location_system(stop_points[0])
    assert system == GRID_LOCATION

    wsg84_stop_point = """
    <StopPoints>
        <StopPoint CreationDateTime="1970-01-01T01:00:00">
        <AtcoCode>999014AA766B</AtcoCode>
        <Descriptor>
            <CommonName>Dover (DFDS Ferry)</CommonName>
        </Descriptor>
        <Place>
            <NptgLocalityRef>E0047158</NptgLocalityRef>
            <LocalityName>Dover</LocalityName>
            <Location>
                <Latitude>48.835318</Latitude>
                <Longitude>2.380519</Longitude>
            </Location>
        </Place>
        <StopClassification>
            <StopType>busCoachTrolleyOnStreetPoint</StopType>
            <OnStreet>
            <Bus>
                <BusStopType>MKD</BusStopType>
                <TimingStatus>principalTimingPoint</TimingStatus>
                <MarkedPoint>
                <Bearing>
                    <CompassPoint>N</CompassPoint>
                </Bearing>
                </MarkedPoint>
            </Bus>
            </OnStreet>
        </StopClassification>
        <AdministrativeAreaRef>999</AdministrativeAreaRef>
        <Public>true</Public>
        </StopPoint>
    </StopPoints>
    """
    xml = TXCFile(wsg84_stop_point)
    doc = TransXChangeDocument(xml)
    stop_points = doc.get_stop_points()
    system = doc.get_location_system(stop_points[0])
    assert system == WSG84_LOCATION


def test_has_latitude():
    xml_1 = """<StopPoints>
        <StopPoint CreationDateTime="1970-01-01T01:00:00">
        <AtcoCode>999014AA766B</AtcoCode>
        <Descriptor>
            <CommonName>Dover (DFDS Ferry)</CommonName>
        </Descriptor>
        <Place>
            <NptgLocalityRef>E0047158</NptgLocalityRef>
            <LocalityName>Dover</LocalityName>
            <Location>
            <Translation>
                <Easting>633910</Easting>
                <Northing>141970</Northing>
                <Longitude>1.34172</Longitude>
                <Latitude>51.12922</Latitude>
            </Translation>
            </Location>
        </Place>
        <StopClassification>
            <StopType>busCoachTrolleyOnStreetPoint</StopType>
            <OnStreet>
            <Bus>
                <BusStopType>MKD</BusStopType>
                <TimingStatus>principalTimingPoint</TimingStatus>
                <MarkedPoint>
                <Bearing>
                    <CompassPoint>N</CompassPoint>
                </Bearing>
                </MarkedPoint>
            </Bus>
            </OnStreet>
        </StopClassification>
        <AdministrativeAreaRef>999</AdministrativeAreaRef>
        <Public>true</Public>
        </StopPoint>
    </StopPoints>
    """
    xml = TXCFile(xml_1)
    doc = TransXChangeDocument(xml)
    stop_points = doc.get_stop_points()
    has_latitude = doc.has_latitude(stop_points[0])
    assert has_latitude == False

    xml_2 = """<StopPoints>
        <StopPoint CreationDateTime="1970-01-01T01:00:00">
        <AtcoCode>999014AA766B</AtcoCode>
        <Descriptor>
            <CommonName>Dover (DFDS Ferry)</CommonName>
        </Descriptor>
        <Place>
            <NptgLocalityRef>E0047158</NptgLocalityRef>
            <LocalityName>Dover</LocalityName>
            <Location>
                <Latitude>48.835318</Latitude>
                <Longitude>2.380519</Longitude>
            </Location>
        </Place>
        <StopClassification>
            <StopType>busCoachTrolleyOnStreetPoint</StopType>
            <OnStreet>
            <Bus>
                <BusStopType>MKD</BusStopType>
                <TimingStatus>principalTimingPoint</TimingStatus>
                <MarkedPoint>
                <Bearing>
                    <CompassPoint>N</CompassPoint>
                </Bearing>
                </MarkedPoint>
            </Bus>
            </OnStreet>
        </StopClassification>
        <AdministrativeAreaRef>999</AdministrativeAreaRef>
        <Public>true</Public>
        </StopPoint>
    </StopPoints>
    """
    xml = TXCFile(xml_2)
    doc = TransXChangeDocument(xml)
    stop_points = doc.get_stop_points()
    has_latitude = doc.has_latitude(stop_points[0])
    assert has_latitude == True

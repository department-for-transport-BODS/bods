from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField
from transit_odp.common.fields import CallableStorageFileField
from transit_odp.disruptions.storage import get_sirisx_storage


class DisruptionsDataArchive(models.Model):
    created = CreationDateTimeField(_("created"))
    last_updated = ModificationDateTimeField(_("last_updated"))
    data = CallableStorageFileField(
        storage=get_sirisx_storage,
        help_text=_("A zip file containing an up to date SIRI-SX XML."),
    )

    class Meta:
        get_latest_by = "-created"
        ordering = ("-created",)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(created={self.created!r}, "
            f"last_updated={self.last_updated!r}, data={self.data.name!r}, "
            f"data_format={self.data_format!r})"
        )


class DisruptionReasonsEnum(models.TextChoices):
    accident = "accident", "Accident"
    securityAlert = "securityAlert", "Security Alert"
    congestion = "congestion", "Congestion"
    roadClosed = "roadClosed", "Road Closed"
    incident = "incident", "Incident"
    routeDiversion = "routeDiversion", "Route Diversion"
    unknown = "unknown", "Unknown"
    vandalism = "vandalism", "Vandalism"
    overcrowded = "overcrowded", "Overcrowded"
    operatorCeasedTrading = "operatorCeasedTrading", "Operator Ceased Trading"
    vegetation = "vegetation", "Vegetation"
    roadworks = "roadworks", "Roadworks"
    specialEvent = "specialEvent", "Special Event"
    insufficientDemand = "insufficientDemand", "Insufficient Demand"
    staffSickness = "staffSickness", "Staff Sickness"
    staffInjury = "staffInjury", "Staff Injury"
    contractorStaffInjury = "contractorStaffInjury", "Contractor Staff Injury"
    staffAbsence = "staffAbsence", "Staff Absence"
    staffInWrongPlace = "staffInWrongPlace", "Staff in Wrong Place"
    staffShortage = "staffShortage", "Staff Shortage"
    industrialAction = "industrialAction", "Industrial Action"
    unofficialIndustrialAction = (
        "unofficialIndustrialAction",
        "Unofficial Industrial Action",
    )
    workToRule = "workToRule", "Work to Rule"
    undefinedPersonnelProblem = (
        "undefinedPersonnelProblem",
        "Undefined Personnel Problem",
    )
    pointsFailure = "pointsFailure", "Points Failure"
    signalProblem = "signalProblem", "Signal Problem"
    trainWarningSystemProblem = (
        "trainWarningSystemProblem",
        "Train Warning System Problem",
    )
    trackCircuitProblem = "trackCircuitProblem", "Track Circuit Problem"
    signalFailure = "signalFailure", "Signal Failure"
    derailment = "derailment", "Derailment"
    engineFailure = "engineFailure", "Engine Failure"
    tractionFailure = "tractionFailure", "Traction Failure"
    breakDown = "breakDown", "Break Down"
    technicalProblem = "technicalProblem", "Technical Problem"
    brokenRail = "brokenRail", "Broken Rail"
    poorRailConditions = "poorRailConditions", "Poor Rail Conditions"
    wheelImpactLoad = "wheelImpactLoad", "Wheel Impact Load"
    lackOfOperationalStock = "lackOfOperationalStock", "Lack of Operational Stock"
    defectiveFireAlarmEquipment = (
        "defectiveFireAlarmEquipment",
        "Defective Fire Alarm Equipment",
    )
    defectivePlatformEdgeDoors = (
        "defectivePlatformEdgeDoors",
        "Defective Platform Edge Doors",
    )
    defectiveCctv = "defectiveCctv", "Defective Cctv"
    defectivePublicAnnouncementSystem = (
        "defectivePublicAnnouncementSystem",
        "Defective Public Announcement System",
    )
    ticketingSystemNotAvailable = (
        "ticketingSystemNotAvailable",
        "Ticketing System Not Available",
    )
    repairWork = "repairWork", "Repair Work"
    constructionWork = "constructionWork", "Construction Work"
    maintenanceWork = "maintenanceWork", "Maintenance Work"
    emergencyEngineeringWork = "emergencyEngineeringWork", "Emergency Engineering Work"
    lateFinishToEngineeringWork = (
        "lateFinishToEngineeringWork",
        "Late Finish to Engineering Work",
    )
    powerProblem = "powerProblem", "Power Problem"
    fuelProblem = "fuelProblem", "Fuel Problem"
    swingBridgeFailure = "swingBridgeFailure", "Swing Bridge Failure"
    escalatorFailure = "escalatorFailure", "Escalator Failure"
    liftFailure = "liftFailure", "Lift Failure"
    gangwayProblem = "gangwayProblem", "Gangway Problem"
    closedForMaintenance = "closedForMaintenance", "Closed for Maintenance"
    fuelShortage = "fuelShortage", "Fuel Shortage"
    deicingWork = "deicingWork", "Deicing Work"
    wheelProblem = "wheelProblem", "Wheel Problem"
    luggageCarouselProblem = "luggageCarouselProblem", "Luggage Carousel Problem"
    undefinedEquipmentProblem = (
        "undefinedEquipmentProblem",
        "Undefined Equipment Problem",
    )
    fog = "fog", "Fog"
    roughSea = "roughSea", "Rough Sea"
    heavySnowFall = "heavySnowFall", "Heavy Snow Fall"
    driftingSnow = "driftingSnow", "Drifting Snow"
    blizzardConditions = "blizzardConditions", "Blizzard Conditions"
    heavyRain = "heavyRain", "Heavy Rain"
    strongWinds = "strongWinds", "Strong Winds"
    stormConditions = "stormConditions", "Storm Conditions"
    stormDamage = "stormDamage", "Storm Damage"
    tidalRestrictions = "tidalRestrictions", "Tidal Restrictions"
    highTide = "highTide", "High Tide"
    lowTide = "lowTide", "Low Tide"
    ice = "ice", "Ice"
    frozen = "frozen", "Frozen"
    hail = "hail", "Hail"
    sleet = "sleet", "Sleet"
    highTemperatures = "highTemperatures", "High Temperatures"
    flooding = "flooding", "Flooding"
    waterlogged = "waterlogged", "Water Logged"
    lowWaterLevel = "lowWaterLevel", "Low Water Level"
    highWaterLevel = "highWaterLevel", "High Water Level"
    fallenLeaves = "fallenLeaves", "Fallen Leaves"
    fallenTree = "fallenTree", "Fallen Tree"
    landslide = "landslide", "Landslide"
    undefinedEnvironmentalProblem = (
        "undefinedEnvironmentalProblem",
        "Undefined Environmental Problem",
    )
    lightningStrike = "lightningStrike", "Lightning Strike"
    sewerOverflow = "sewerOverflow", "Sewer Overflow"
    grassFire = "grassFire", "Grass Fire"

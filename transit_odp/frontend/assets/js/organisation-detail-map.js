import cross from "../images/disruptions-map/cross.png";
import diversion from "../images/disruptions-map/diversion.png";
import engineering from "../images/disruptions-map/engineering.png";
import event from "../images/disruptions-map/event.png";
import industrialAction from "../images/disruptions-map/industrial-action.png";
import questionMark from "../images/disruptions-map/question-mark.png";
import roadworks from "../images/disruptions-map/roadworks.png";
import traffic from "../images/disruptions-map/traffic.png";
import weather from "../images/disruptions-map/weather.png";
import Spiderfy from "@nazka/map-gl-js-spiderfy";
import circle from "../images/disruptions-map/circle-sdf.png";

const mapboxgl = require("mapbox-gl");

const createStopsPopUp = (e, map, popup, isInSpider = false) => {
  const disruptionInfo = isInSpider ? e.properties : e.features[0].properties;
  const coordinates = isInSpider ? e.geometry.coordinates : e.lngLat;
  const disruptionReason =
    disruptionReasonText[disruptionInfo.disruptionReason];
  const name = disruptionInfo.commonName;
  const disruptionDates = `${disruptionInfo.disruptionStartDateTime} - ${disruptionInfo.disruptionEndDateTime}`;
  const atcoCode = `Atco code: ${disruptionInfo.atcoCode}`;
  const bearing = `Bearing: ${disruptionInfo.bearing}`;
  const disruptionLink = `disruption-detail/${disruptionInfo.disruptionId}`;
  const popup_content = `<h2>${disruptionReason}</h2><h3>${name}</h3><div><p>${disruptionDates}</p><p>${atcoCode}</p><p>${bearing}</p><a href=${disruptionLink}>See more</a></div>`;

  popup.setLngLat(coordinates).setHTML(popup_content).addTo(map);
};

const createServicesPopUp = (e, map, popup, isInSpider = false) => {
  const disruptionInfo = isInSpider ? e.properties : e.features[0].properties;
  const coordinates = isInSpider ? e.geometry.coordinates : e.lngLat;
  const disruptionReason =
    disruptionReasonText[disruptionInfo.disruptionReason];
  const name = disruptionInfo.lineDisplayName;
  const disruptionDates = `${disruptionInfo.disruptionStartDateTime} - ${disruptionInfo.disruptionEndDateTime}`;
  const operatorName = `Operator: ${disruptionInfo.operatorName}`;
  const disruptionLink = `disruption-detail/${disruptionInfo.disruptionId}`;
  const popup_content = `<h2>${disruptionReason}</h2><h3>${name}</h3><div><p>${disruptionDates}</p><p>${operatorName}</p><a href=${disruptionLink}>See more</a></div>`;

  popup.setLngLat(coordinates).setHTML(popup_content).addTo(map);
};

const iconDisruptions = ["individual-points"];

const images = [
  { url: cross, id: "cross" },
  { url: diversion, id: "diversion" },
  { url: engineering, id: "engineering" },
  { url: event, id: "event" },
  { url: industrialAction, id: "industrialaction" },
  { url: questionMark, id: "questionmark" },
  { url: roadworks, id: "roadworks" },
  { url: traffic, id: "traffic" },
  { url: weather, id: "weather" },
];

const disruptionReasonByIcon = {
  cross: ["operatorceasedtrading"],
  diversion: ["routediversion"],
  engineering: [
    "emergencyengineeringwork",
    "escalatorfailure",
    "liftfailure",
    "repairwork",
    "securityalert",
    "signalfailure",
    "signalproblem",
    "vandalism",
  ],
  event: ["specialevent"],
  industrialaction: ["industrialaction"],
  questionmark: ["unknown"],
  roadworks: ["constructionwork", "maintenancework", "roadclosed", "roadworks"],
  traffic: ["accident", "breakdown", "congestion", "incident", "overcrowded"],
  weather: [
    "flooding",
    "fog",
    "heavyrain",
    "heavysnowfall",
    "hightemperatures",
    "ice",
  ],
};

function getIconForDisruption(disruptionReason) {
  for (const [icon, reasons] of Object.entries(disruptionReasonByIcon)) {
    if (reasons.includes(disruptionReason.toLowerCase())) {
      return icon;
    }
  }
  return "questionmark";
}
const disruptionReasonText = {
  accident: "Accident",
  securityAlert: "Security alert",
  congestion: "Congestion",
  roadClosed: "Road closed",
  incident: "Incident",
  routeDiversion: "Route diversion",
  unknown: "Unknown",
  vandalism: "Vandalism",
  overcrowded: "Overcrowded",
  operatorCeasedTrading: "Operator ceased trading",
  roadworks: "Roadworks",
  specialEvent: "Special event",
  industrialAction: "Industrial action",
  signalProblem: "Signal problem",
  signalFailure: "Signal failure",
  repairWork: "Repair work",
  constructionWork: "Construction work",
  maintenanceWork: "Maintenance work",
  emergencyEngineeringWork: "Emergency engineering work",
  escalatorFailure: "Escalator failure",
  liftFailure: "Lift failure",
  fog: "Fog",
  heavySnowFall: "Heavy snowfall",
  heavyRain: "Heavy rain",
  ice: "Ice",
  highTemperatures: "High temperatures",
  flooding: "Flooding",
};

const httpGetAsync = (url, callback) => {
  const request = new XMLHttpRequest();

  if (!request) {
    alert("Giving up :( Cannot create an XMLHTTP instance");
    return false;
  }
  request.onreadystatechange = function () {
    if (request.readyState === 4 && request.status === 200)
      callback(request.responseText);
  };
  request.open("GET", url, true); // true for asynchronous
  request.send();
};

const initOrgMap = (apiRoot, orgId, disruptionId) => {
  const url = disruptionId
    ? apiRoot +
    "disruption_detail_map_data/?orgId=" +
    orgId.toString() +
    "&disruptionId=" +
    disruptionId.toString()
    : apiRoot + "organisation_map_data/?orgId=" + orgId.toString();

  // Initialise Map
  mapboxgl.accessToken = mapboxKey;
  const map = new mapboxgl.Map({
    container: "map",
    style: "mapbox://styles/mapbox/streets-v12",
    center: [-1.1743, 52.3555],
    zoom: 5,
    maxzoom: 12,
  });

  // Add zoom and rotation controls to the map.
  map.addControl(new mapboxgl.NavigationControl({ showCompass: false }));

  // Prevent focus on map when tabbing through page
  // canvas
  map["_canvas"].setAttribute("tabindex", -1);
  // logo
  let logoArray = map["_controls"].find((o) => o.hasOwnProperty("_updateLogo"))[
    "_container"
  ]["children"];
  for (let i = 0; i < logoArray.length; i++) {
    logoArray[i].setAttribute("tabindex", -1);
  }
  // zoom buttons
  let zoomObject = map["_controls"].find((o) =>
    o.hasOwnProperty("_zoomInButton")
  );
  zoomObject["_zoomInButton"].setAttribute("tabindex", -1);
  zoomObject["_zoomOutButton"].setAttribute("tabindex", -1);

  const formatOrganisationDetailPageDisruptions = (disruptions) => {
    let stopsDisruptions = []
    let serviceDisruptions = []
    return disruptions.flatMap((disruption) => {
      if (disruption.services && disruption.services.length > 0) {
        serviceDisruptions = disruption.services.map((service) => {
          if (service.coordinates.longitude && service.coordinates.latitude) {
            return {
              type: "Feature",
              geometry: {
                type: "Point",
                coordinates: [
                  service.coordinates.longitude,
                  service.coordinates.latitude,
                ],
              },
              properties: {
                icon: getIconForDisruption(disruption.disruptionReason),
                consequenceType: "services",
                disruptionReason: disruption.disruptionReason,
                disruptionId: disruption.disruptionId,
                lineDisplayName: `${service.lineName} - ${service.origin} - ${service.destination}`,
                operatorName: service.operatorName,
                disruptionStartDateTime: `${disruption.disruptionStartDate} ${disruption.disruptionStartTime}`,
                disruptionEndDateTime: disruption.disruptionNoEndDateTime ? "No end date time" : `${disruption.disruptionEndDate} ${disruption.disruptionEndTime}`,
                disruptionNoEndDateTime: service.disruptionNoEndDateTime
              }
            }
          }
        })
      }

      if (disruption.stops && disruption.stops.length > 0) {
        stopsDisruptions = disruption.stops.map((stop) => ({
          type: "Feature",
          geometry: {
            type: "Point",
            coordinates: [
              stop.coordinates.longitude,
              stop.coordinates.latitude,
            ],
          },
          properties: {
            icon: getIconForDisruption(disruption.disruptionReason),
            consequenceType: "stops",
            disruptionReason: disruption.disruptionReason,
            disruptionId: disruption.disruptionId,
            atcoCode: stop.atcoCode,
            commonName: stop.commonName,
            bearing: stop.bearing ?? "N/A",
            disruptionStartDateTime: `${disruption.disruptionStartDate} ${disruption.disruptionStartTime}`,
            disruptionEndDateTime: disruption.disruptionNoEndDateTime ? "No end date time" : `${disruption.disruptionEndDate} ${disruption.disruptionEndTime}`,
            disruptionNoEndDateTime: stop.disruptionNoEndDateTime
          }
        }))
      }
      return [...serviceDisruptions, ...stopsDisruptions]
    }).filter(val => val !== undefined)
  }

  httpGetAsync(url, function (responseText) {
    const response = JSON.parse(responseText);

    if (!response) {
      return;
    }

    let formattedDisruptions = []
    if (disruptionId) {
      formattedDisruptions = response.map(resp => {
        const properties = resp.properties
        return { ...resp, properties: { ...properties, ...(properties?.disruptionReason ? { icon: getIconForDisruption(properties?.disruptionReason) } : {}) } }
      })
    }
    else {
      formattedDisruptions = formatOrganisationDetailPageDisruptions(response);
    }

    const bounds = new mapboxgl.LngLatBounds();

    formattedDisruptions.forEach((feature) => {
      bounds.extend(feature.geometry.coordinates);
    });

    map.fitBounds(bounds, { padding: 20 });

    Promise.all([
      ...images.map(
        (img) =>
          new Promise((resolve, reject) => {
            map.loadImage(img.url, (error, image) => {
              if (error) {
                reject(error);
                return;
              }
              map.addImage(img.id, image);
              resolve();
            });
          })
      ),
      new Promise((resolve, reject) => {
        map.loadImage(circle, (error, image) => {
          if (error) {
            reject(error);
            return;
          }

          map.addImage("cluster", image, { sdf: true });
          resolve();
        });
      }),
    ]).then(() => {
      const popup = new mapboxgl.Popup({
        closeButton: false,
        closeOnClick: true,
        closeOnMove: true,
      });
      map.addSource("disruptions", {
        type: "geojson",
        data: {
          type: "FeatureCollection",
          features: formattedDisruptions,
        },
        cluster: true,
        clusterMaxZoom: 14,
        clusterRadius: 50,
      });

      map.addLayer({
        id: "clusters",
        type: "symbol",
        layout: {
          "icon-image": "cluster",
          "icon-allow-overlap": true,
        },
        source: "disruptions",
        filter: ["has", "point_count"],
        paint: {
          "icon-color": "black",
        },
      });

      map.addLayer({
        id: "cluster-counts",
        type: "symbol",
        source: "disruptions",
        filter: ["has", "point_count"],
        layout: {
          "text-field": "{point_count_abbreviated}",
          "text-size": 12,
        },
        paint: {
          "text-color": "white",
        },
      });

      map.addLayer({
        id: "individual-points",
        type: "symbol",
        source: "disruptions",
        filter: ["!", ["has", "point_count"]],
        layout: {
          "icon-image": ["get", "icon"],
          "icon-size": 0.25,
        },
      });
      const spiderfy = new Spiderfy(map, {
        onLeafClick: (e) => {
          if (e.properties.consequenceType === "stops") {
            createStopsPopUp(e, map, popup, true);
            return;
          }
          if (e.properties.consequenceType === "services") {
            createServicesPopUp(e, map, popup, true);
            return;
          } else return;
        },
        minZoomLevel: 14,
        zoomIncrement: 2,
        closeOnLeafClick: false,
        circleSpiralSwitchover: 10,
        circleOptions: {
          leavesSeparation: 110,
          leavesOffset: [3, 3],
        },
        spiralOptions: {
          legLengthStart: 110,
          legLengthFactor: 6,
          leavesSeparation: 110,
          leavesOffset: [3, 3],
        },
        spiderLegsAreHidden: true,
        spiderLegsWidth: 2,
        spiderLegsColor: "black",
        spiderLeavesPaint: {
          "icon-color": "black",
        },
        spiderLeavesLayout: {
          "icon-image": ["get", "icon"],
          "icon-size": 0.25,
          "icon-allow-overlap": false,
        },
        maxLeaves: 255,
        renderMethod: "flat",
      });

      spiderfy.applyTo("clusters");
    });
  });

  map.on("load", function () {
    const popupSecondary = new mapboxgl.Popup({
      closeButton: false,
      closeOnClick: true,
      closeOnMove: true,
    });
    if (!disruptionId) {
      iconDisruptions.forEach((icon) => {
        map.on("mousemove", icon, () => {
          map.getCanvas().style.cursor = "pointer";
        });

        map.on("mouseleave", icon, () => {
          map.getCanvas().style.cursor = "";
        });

        map.on("click", icon, (e) => {
          if (e.features[0].properties.consequenceType === "stops") {
            createStopsPopUp(e, map, popupSecondary);
            return;
          }
          if (e.features[0].properties.consequenceType === "services") {
            createServicesPopUp(e, map, popupSecondary);
            return;
          } else return;
        });
      });
    }
  });
};

export { initOrgMap };

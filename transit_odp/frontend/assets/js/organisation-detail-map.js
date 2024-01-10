import cross from '../images/disruptions-map/cross.png'
import diversion from '../images/disruptions-map/diversion.png'
import engineering from '../images/disruptions-map/engineering.png'
import event from '../images/disruptions-map/event.png'
import industrialAction from '../images/disruptions-map/industrial-action.png'
import questionMark from '../images/disruptions-map/question-mark.png'
import roadworks from '../images/disruptions-map/roadworks.png'
import traffic from '../images/disruptions-map/traffic.png'
import weather from '../images/disruptions-map/weather.png'

const mapboxgl = require("mapbox-gl");

const iconDisruptions = [
  "cross-icon-disruptions",
  "diversion-icon-disruptions",
  "engineering-icon-disruptions",
  "event-icon-disruptions",
  "industrial-action-icon-disruptions",
  "question-mark-icon-disruptions",
  "roadworks-icon-disruptions",
  "traffic-icon-disruptions",
  "weather-icon-disruptions",
]

const images = [
  {url: cross, id: 'cross'},
  {url: diversion, id: 'diversion'},
  {url: engineering, id: 'engineering'},
  {url: event, id: 'event'},
  {url: industrialAction, id: 'industrial-action'},
  {url: questionMark, id: 'question-mark'},
  {url: roadworks, id: 'roadworks'},
  {url: traffic, id: 'traffic'},
  {url: weather, id: 'weather'},
]

const disruptionReasonByIcon = {
  crossIcon: ["operatorCeasedTrading"],
  diversionIcon: ["routeDiversion"],
  engineeringIcon: ["emergencyEngineeringWork", "escalatorFailure", "liftFailure", "repairWork", "securityAlert", "signalFailure", "signalProblem", "vandalism"],
  eventIcon: ["specialEvent"],
  industrialActionIcon: ["industrialAction"],
  questionMarkIcon: ["unknown"],
  roadworksIcon: ["constructionWork", "maintenanceWork", "roadClosed", "roadworks"],
  trafficIcon: ["accident", "breakdown", "congestion", "incident", "overcrowded"],
  weatherIcon: ["flooding", "fog", "heavyRain", "heavySnowFall", "highTemperatures", "ice"]
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
}

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

  const url = disruptionId ? apiRoot + "disruption_detail_map_data/?orgId=" + orgId.toString() + "&disruptionId=" + disruptionId.toString() : apiRoot + "organisation_map_data/?orgId=" + orgId.toString();

  // Initialise Map
  mapboxgl.accessToken =
    "pk.eyJ1IjoiaGFsYmVydHJhbSIsImEiOiJjaXFiNXVnazIwMDA0aTJuaGxlaTU1M2ZtIn0.85dXvyj6V2LbBFvXfpQyYA";
  const map = new mapboxgl.Map({
    container: "map",
    style: "mapbox://styles/mapbox/streets-v12",
    center: [-1.1743, 52.3555],
    zoom: 5,
    maxzoom: 12,
  });

  // Add zoom and rotation controls to the map.
  map.addControl(new mapboxgl.NavigationControl({showCompass: false}));

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
    return disruptions.flatMap((disruption) => {
      if (disruption.services && disruption.services.length > 0) {
        const serviceDisruptions = disruption.services.map((service) => {
          if(service.coordinates.longitude && service.coordinates.latitude) {
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
                consequenceType: "services",
                disruptionReason: disruption.disruptionReason,
                disruptionId: disruption.disruptionId,
                lineDisplayName: `${service.lineName} - ${service.origin} - ${service.destination}`,
                operatorName: service.operatorName,
                disruptionStartDateTime: `${disruption.disruptionStartDate} ${disruption.disruptionStartTime}`,
                disruptionEndDateTime: disruption.disruptionNoEndDateTime ? "No end date time" : `${disruption.disruptionEndDate} ${disruption.disruptionEndTime}`,
                disruptionNoEndDateTime: service.disruptionNoEndDateTime
              }
            }}
        })
        return serviceDisruptions
      }

      if (disruption.stops && disruption.stops.length > 0) {
        const stopsDisruptions = disruption.stops.map((stop) => ({
          type: "Feature",
          geometry: {
            type: "Point",
            coordinates: [
              stop.coordinates.longitude,
              stop.coordinates.latitude,
            ],
          },
          properties: {
            consequenceType: "stops",
            disruptionReason: disruption.disruptionReason,
            disruptionId: disruption.disruptionId,
            atcoCode: stop.atcoCode,
            commonName: stop.commonName,
            bearing: stop.bearing,
            disruptionStartDateTime: `${disruption.disruptionStartDate} ${disruption.disruptionStartTime}`,
            disruptionEndDateTime: disruption.disruptionNoEndDateTime ? "No end date time" : `${disruption.disruptionEndDate} ${disruption.disruptionEndTime}`,
            disruptionNoEndDateTime: stop.disruptionNoEndDateTime
          }
        }))
        return stopsDisruptions
      }
      return [...serviceDisruptions, ...stopsDisruptions]
    }).filter(val => val !== undefined)
  }

  httpGetAsync(url, function (responseText) {
    const disruptions = JSON.parse(responseText);

    const formattedDisruptions = disruptionId ? disruptions : formatOrganisationDetailPageDisruptions(disruptions)

    const bounds = new mapboxgl.LngLatBounds();

    formattedDisruptions.forEach((feature) => {
      bounds.extend(feature.geometry.coordinates);
    });

    map.fitBounds(bounds, {padding: 20});

    Promise.all(images.map(img => new Promise((resolve, reject) => {
        map.loadImage(img.url, (error, image) => {
          map.addImage(img.id, image)
          resolve();
        })
      }))
    ).then(() => {
      map.addSource('cross-icon-disruptions', {
        'type': 'geojson',
        'data': {
          "type": "FeatureCollection",
          "features": formattedDisruptions.filter((disruption) => disruptionReasonByIcon.crossIcon.includes(disruption.properties.disruptionReason))
        }
      });

      map.addLayer({
        id: "cross-icon-disruptions",
        type: "symbol",
        source: "cross-icon-disruptions",
        layout: {
          'icon-image': 'cross',
          'icon-size': 0.25
        }
      });

      map.addSource('diversion-icon-disruptions', {
        'type': 'geojson',
        'data': {
          "type": "FeatureCollection",
          "features": formattedDisruptions.filter((disruption) => disruptionReasonByIcon.diversionIcon.includes(disruption.properties.disruptionReason))
        }
      });

      map.addLayer({
        id: "diversion-icon-disruptions",
        type: "symbol",
        source: "diversion-icon-disruptions",
        layout: {
          'icon-image': 'diversion',
          'icon-size': 0.25
        }
      });

      map.addSource('engineering-icon-disruptions', {
        'type': 'geojson',
        'data': {
          "type": "FeatureCollection",
          "features": formattedDisruptions.filter((disruption) => disruptionReasonByIcon.engineeringIcon.includes(disruption.properties.disruptionReason))
        }
      });

      map.addLayer({
        id: "engineering-icon-disruptions",
        type: "symbol",
        source: "engineering-icon-disruptions",
        layout: {
          'icon-image': 'engineering',
          'icon-size': 0.25
        }
      });

      map.addSource('event-icon-disruptions', {
        'type': 'geojson',
        'data': {
          "type": "FeatureCollection",
          "features": formattedDisruptions.filter((disruption) => disruptionReasonByIcon.eventIcon.includes(disruption.properties.disruptionReason))
        }
      });

      map.addLayer({
        id: "event-icon-disruptions",
        type: "symbol",
        source: "event-icon-disruptions",
        layout: {
          'icon-image': 'event',
          'icon-size': 0.25
        }
      });

      map.addSource('industrial-action-icon-disruptions', {
        'type': 'geojson',
        'data': {
          "type": "FeatureCollection",
          "features": formattedDisruptions.filter((disruption) => disruptionReasonByIcon.industrialActionIcon.includes(disruption.properties.disruptionReason))
        }
      });

      map.addLayer({
        id: "industrial-action-icon-disruptions",
        type: "symbol",
        source: "industrial-action-icon-disruptions",
        layout: {
          'icon-image': 'industrial-action',
          'icon-size': 0.25
        }
      });

      map.addSource('question-mark-icon-disruptions', {
        'type': 'geojson',
        'data': {
          "type": "FeatureCollection",
          "features": formattedDisruptions.filter((disruption) => disruptionReasonByIcon.questionMarkIcon.includes(disruption.properties.disruptionReason))
        }
      });

      map.addLayer({
        id: "question-mark-icon-disruptions",
        type: "symbol",
        source: "question-mark-icon-disruptions",
        layout: {
          'icon-image': 'question-mark',
          'icon-size': 0.25
        }
      });

      map.addSource('roadworks-icon-disruptions', {
        'type': 'geojson',
        'data': {
          "type": "FeatureCollection",
          "features": formattedDisruptions.filter((disruption) => disruptionReasonByIcon.roadworksIcon.includes(disruption.properties.disruptionReason))
        }
      });

      map.addLayer({
        id: "roadworks-icon-disruptions",
        type: "symbol",
        source: "roadworks-icon-disruptions",
        layout: {
          'icon-image': 'roadworks',
          'icon-size': 0.25
        }
      });

      map.addSource("traffic-icon-disruptions", {
        type: "geojson",
        data: {
          "type": "FeatureCollection",
          "features": formattedDisruptions.filter((disruption) => disruptionReasonByIcon.trafficIcon.includes(disruption.properties.disruptionReason))
        }
      });

      map.addLayer({
        id: "traffic-icon-disruptions",
        type: "symbol",
        source: "traffic-icon-disruptions",
        layout: {
          'icon-image': 'traffic',
          'icon-size': 0.25
        }
      });

      map.addSource('weather-icon-disruptions', {
        'type': 'geojson',
        'data': {
          "type": "FeatureCollection",
          "features": formattedDisruptions.filter((disruption) => disruptionReasonByIcon.weatherIcon.includes(disruption.properties.disruptionReason))
        }
      });

      map.addLayer({
        id: "weather-icon-disruptions",
        type: "symbol",
        source: "weather-icon-disruptions",
        layout: {
          'icon-image': 'weather',
          'icon-size': 0.25
        }
      });
    })
  });

  map.on("load", function () {
    const popup = new mapboxgl.Popup({
      closeButton: false,
      closeOnClick: true,
      closeOnMove: true,
    });

    const createStopsPopUp = (e) => {
      const disruptionReason = disruptionReasonText[e.features[0].properties.disruptionReason];
      const name = e.features[0].properties.commonName;
      const disruptionDates = `${e.features[0].properties.disruptionStartDateTime} - ${e.features[0].properties.disruptionEndDateTime}`;
      const atcoCode = `Atco code: ${e.features[0].properties.atcoCode}`;
      const bearing = `Bearing: ${e.features[0].properties.bearing}`
      const disruptionLink = `disruption-detail/${e.features[0].properties.disruptionId}`
      const popup_content = `<h2>${disruptionReason}</h2><h3>${name}</h3><div><p>${disruptionDates}</p><p>${atcoCode}</p><p>${bearing}</p><a href=${disruptionLink}>See more</a></div>`

      popup.setLngLat(e.lngLat).setHTML(popup_content).addTo(map);
    }

    const createServicesPopUp = (e) => {
      const disruptionReason = disruptionReasonText[e.features[0].properties.disruptionReason];
      const name = e.features[0].properties.lineDisplayName;
      const disruptionDates = `${e.features[0].properties.disruptionStartDateTime} - ${e.features[0].properties.disruptionEndDateTime}`;
      const operatorName = `Operator: ${e.features[0].properties.operatorName}`;
      const disruptionLink = `disruption-detail/${e.features[0].properties.disruptionId}`
      const popup_content = `<h2>${disruptionReason}</h2><h3>${name}</h3><div><p>${disruptionDates}</p><p>${operatorName}</p><a href=${disruptionLink}>See more</a></div>`

      popup.setLngLat(e.lngLat).setHTML(popup_content).addTo(map);
    }

    iconDisruptions.forEach((icon) => {
      map.on("mousemove", icon, () => {
        map.getCanvas().style.cursor = "pointer";
      })

      map.on("mouseleave", icon, () => {
        map.getCanvas().style.cursor = "";
      })

      map.on("click", icon, (e) => {
        if(e.features[0].properties.consequenceType === "stops"){
          createStopsPopUp(e)
          return;
        }
        if(e.features[0].properties.consequenceType === "services"){
          createServicesPopUp(e)
          return;
        } else return;
      });
    })
  })

};

export { initOrgMap };

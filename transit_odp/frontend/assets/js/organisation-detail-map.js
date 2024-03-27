import cross from '../images/disruptions-map/cross.png'
import diversion from '../images/disruptions-map/diversion.png'
import engineering from '../images/disruptions-map/engineering.png'
import event from '../images/disruptions-map/event.png'
import industrialAction from '../images/disruptions-map/industrial-action.png'
import questionMark from '../images/disruptions-map/question-mark.png'
import roadworks from '../images/disruptions-map/roadworks.png'
import traffic from '../images/disruptions-map/traffic.png'
import weather from '../images/disruptions-map/weather.png'
import Spiderfy from '@nazka/map-gl-js-spiderfy';
import circle from '../images/disruptions-map/circle-sdf.png'

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
  { url: cross, id: 'cross' },
  { url: diversion, id: 'diversion' },
  { url: engineering, id: 'engineering' },
  { url: event, id: 'event' },
  { url: industrialAction, id: 'industrialaction' },
  { url: questionMark, id: 'questionmark' },
  { url: roadworks, id: 'roadworks' },
  { url: traffic, id: 'traffic' },
  { url: weather, id: 'weather' },
]

const disruptionReasonByIcon = {
  cross: ["operatorceasedtrading"],
  diversion: ["routediversion"],
  engineering: ["emergencyengineeringwork", "escalatorfailure", "liftfailure", "repairwork", "securityalert", "signalfailure", "signalproblem", "vandalism"],
  event: ["specialevent"],
  industrialaction: ["industrialaction"],
  questionmark: ["unknown"],
  roadworks: ["constructionwork", "maintenancework", "roadclosed", "roadworks"],
  traffic: ["accident", "breakdown", "congestion", "incident", "overcrowded"],
  weather: ["flooding", "fog", "heavyrain", "heavysnowfall", "hightemperatures", "ice"]
};

function getIconForDisruption(disruptionReason) {
  for (const [icon, reasons] of Object.entries(disruptionReasonByIcon)) {
    if (reasons.includes(disruptionReason.toLowerCase())) {
      console.log(`Mapping ${disruptionReason} to icon ${icon}`);
      return icon;
    }
  }
  console.log(`Defaulting to questionmark for ${disruptionReason}`);
  return 'questionmark';
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
    return disruptions.flatMap((disruption) => {
      if (disruption.services && disruption.services.length > 0) {
        const serviceDisruptions = disruption.services.map((service) => {
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
        return stopsDisruptions
      }
      return [...serviceDisruptions, ...stopsDisruptions]
    }).filter(val => val !== undefined)
  }

  httpGetAsync(url, function (responseText) {
    const response = JSON.parse(responseText);

    if (!response) {
      return;
    }

    const formattedDisruptions = disruptionId ? response : formatOrganisationDetailPageDisruptions(response)

    const bounds = new mapboxgl.LngLatBounds();

    formattedDisruptions.forEach((feature) => {
      bounds.extend(feature.geometry.coordinates);
    });
    console.log(formattedDisruptions)

    map.fitBounds(bounds, { padding: 20 });

    Promise.all([...images.map(img => new Promise((resolve, reject) => {
      console.log(`Loading image: ${img.id}`); // Debugging line


      map.loadImage(img.url, (error, image) => {
        if (error) {
          console.error(`Error loading image: ${img.id}`, error);
          reject(error);
          return;
        }
        console.log(`Adding image: ${img.id}`); // Confirm image is added
        map.addImage(img.id, image);
        resolve();
      })
    }))
      , new Promise((resolve, reject) => {
        map.loadImage(circle, (error, image) => {
          if (error) {

            reject(error);
            return;
          }

          map.addImage('cluster', image, { sdf: true });
          resolve()
        })
      })]).then(() => {

        map.addSource('disruptions', {
          type: 'geojson',
          data: {
            type: 'FeatureCollection',
            features: formattedDisruptions // Make sure this is the correct GeoJSON structure
          },
          cluster: true,
          clusterMaxZoom: 14, // Max zoom level to cluster
          clusterRadius: 50 // Cluster radius in pixels
        });




        // Add a layer for clusters
        map.addLayer({
          id: 'clusters',
          'type': 'symbol', // must be symbol
          'layout': {
            'icon-image': 'cluster',
            'icon-allow-overlap': true // recommended
          },
          source: 'disruptions',
          filter: ['has', 'point_count'], // Filter for clusters
          paint: {
            'icon-color': 'red'
          }
        });

        // Add a layer for cluster counts
        map.addLayer({
          id: 'cluster-counts',
          type: 'symbol',
          source: 'disruptions',
          filter: ['has', 'point_count'], // Filter for clusters
          layout: {
            'text-field': '{point_count_abbreviated}',
            'text-size': 12
          }
        });

        map.addLayer({
          id: 'individual-points',
          type: 'symbol',
          source: 'disruptions',
          filter: ['!', ['has', 'point_count']], // Filter for non-clustered points
          layout: {
            'icon-image': ['get', 'icon'], // This should match the property in your GeoJSON
            'icon-size': 0.25,
          }
        });
        // create a new spiderfy object
        const spiderfy = new Spiderfy(map, {
          onLeafClick: f => console.log(f),
          minZoomLevel: 12,
          zoomIncrement: 2,
          closeOnLeafClick: true,
          circleSpiralSwitchover: 10,
          circleOptions: {
            leavesSeparation: 50,
            leavesOffset: [0, 0],
          },
          spiralOptions: {
            legLengthStart: 25,
            legLengthFactor: 2.2,
            leavesSeparation: 30,
            leavesOffset: [0, 0],
          },
          spiderLegsAreHidden: false,
          spiderLegsWidth: 2,
          spiderLegsColor: 'black',
              spiderLeavesPaint: {
                'icon-color': [
                  'match',
                  ['get', 'wheelchair'],
                  'yes',
                  'green',
          /* other */ 'red'
                ],
              },
          spiderLeavesLayout: {
            'icon-image': ['get', 'icon'], // This should match the property in your GeoJSON
            'icon-size': 0.25,
            'icon-allow-overlap': true,
          },
            maxLeaves: 255,
            renderMethod: 'flat',
          }); // create a new spiderfy object


        // enable spiderfy on a layer
        // IMPORTANT: the layer must have a cluster source
        spiderfy.applyTo('clusters');

      })
  });

  map.on("load", function () {
    const popup = new mapboxgl.Popup({
      closeButton: false,
      closeOnClick: true,
      closeOnMove: true,
    });

    if (!disruptionId) {
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
          if (e.features[0].properties.consequenceType === "stops") {
            createStopsPopUp(e)
            return;
          }
          if (e.features[0].properties.consequenceType === "services") {
            createServicesPopUp(e)
            return;
          } else return;
        });
      })
    }
  })

};

export { initOrgMap };

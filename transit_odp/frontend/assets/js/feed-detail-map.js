const mapboxgl = require("mapbox-gl");
var feed_map = null
var feed_map_markers = {}
const svgIcon = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" x="0px" y="0px" viewBox="0 0 100 125" style="enable-background:new 0 0 100 100;" xml:space="preserve"><style type="text/css">
	.st0{fill-rule:evenodd;clip-rule:evenodd;}
</style><path class="st0" d="M64.2,78.4h14.2v4.7c0,2.6-2.1,4.7-4.7,4.7h-4.7c-2.6,0-4.7-2.1-4.7-4.7V78.4z"/><path class="st0" d="M21.6,78.4h14.2v4.7c0,2.6-2.1,4.7-4.7,4.7h-4.7c-2.6,0-4.7-2.1-4.7-4.7V78.4z"/><path class="st0" d="M87,27h1.6c2.4,0,4.4,1.7,4.4,3.8v4.5c0,2.1-2,3.8-4.4,3.8H87V27z"/><path class="st0" d="M75.4,12.2H24.6c-5.2,0-9.5,4.2-9.5,9.5V67c0,5.2,4.2,9.5,9.5,9.5h50.7c5.2,0,9.5-4.2,9.5-9.5V21.6  C84.8,16.4,80.6,12.2,75.4,12.2z M28.7,68.9c-3.2,0-5.8-2.5-5.8-5.7c0-3.1,2.6-5.7,5.8-5.7s5.8,2.5,5.8,5.7  C34.5,66.4,31.9,68.9,28.7,68.9z M71.3,68.9c-3.2,0-5.8-2.5-5.8-5.7c0-3.1,2.6-5.7,5.8-5.7s5.8,2.5,5.8,5.7  C77.1,66.4,74.5,68.9,71.3,68.9z M78.4,43.3c0,2.6-2.1,4.7-4.7,4.7H26.4c-2.6,0-4.7-2.1-4.7-4.7V24.4c0-2.6,2.1-4.7,4.7-4.7h47.3  c2.6,0,4.7,2.1,4.7,4.7V43.3z"/><path class="st0" d="M12.9,27h-1.6c-2.4,0-4.4,1.7-4.4,3.8v4.5c0,2.1,2,3.8,4.4,3.8h1.6V27z"/></svg>`;
const customMarker = document.createElement('div');
customMarker.innerHTML = svgIcon
customMarker.style.width = '30px';
customMarker.style.height = '30px';
customMarker.style.backgroundSize = 'cover';

const httpGetAsync = (theUrl, callback) => {
  const request = new XMLHttpRequest();

  if (!request) {
    alert("Giving up :( Cannot create an XMLHTTP instance");
    return false;
  }
  request.onreadystatechange = function () {
    if (request.readyState === 4 && request.status === 200)
      callback(request.responseText);
  };
  request.open("GET", theUrl, true); // true for asynchronous
  request.send();
};

const getLineStringBounds = (coordinates) => {
  return coordinates.reduce(function (bounds, coord) {
    return bounds.extend(coord);
  }, new mapboxgl.LngLatBounds(coordinates[0], coordinates[0]));
};

const getMapDataUrl = (apiRoot, revisionId, lineName, serviceCodes, licenceNumber) => {
  var servicePatternUrl = apiRoot + "service_pattern/"
  var delimetor = "?"

  if (revisionId) {
    servicePatternUrl += delimetor + "revision=" + revisionId.toString();
    delimetor = "&"
  }
    
  if (lineName) {
    servicePatternUrl += delimetor + "line_name=" + lineName.toString();
    delimetor = "&"
  }
  if (serviceCodes) {
    servicePatternUrl += delimetor + "service_codes=" + serviceCodes.toString();
    delimetor = "&"
  }
  if (licenceNumber) {
    servicePatternUrl += delimetor + "licence_number=" + licenceNumber.toString()
  }
  return servicePatternUrl;
};

const initMap = (apiRoot, revisionId, lineName, serviceCodes, licenceNumber) => {
  var servicePatternUrl = getMapDataUrl(apiRoot, revisionId, lineName, serviceCodes, licenceNumber);

  // Initialise Map
  mapboxgl.accessToken = mapboxKey;
  feed_map = new mapboxgl.Map({
    container: "map",
    style: "mapbox://styles/mapbox/light-v9",
    center: [-1.1743, 52.3555],
    zoom: 5,
    maxzoom: 12,
  });

  // Add zoom and rotation controls to the feed_map.
  feed_map.addControl(new mapboxgl.NavigationControl({ showCompass: false }));

  // Prevent focus on map when tabbing through page
  // canvas
  feed_map["_canvas"].setAttribute("tabindex", -1);
  // logo
  let logoArray = feed_map["_controls"].find((o) => o.hasOwnProperty("_updateLogo"))[
    "_container"
  ]["children"];
  for (var i = 0; i < logoArray.length; i++) {
    logoArray[i].setAttribute("tabindex", -1);
  }
  // zoom buttons
  let zoomObject = feed_map["_controls"].find((o) =>
    o.hasOwnProperty("_zoomInButton")
  );
  zoomObject["_zoomInButton"].setAttribute("tabindex", -1);
  zoomObject["_zoomOutButton"].setAttribute("tabindex", -1);

  var hoveredStateId = null;

  // Fetch ServicePattern GeoJSON
  feed_map.on("load", function () {
    httpGetAsync(servicePatternUrl, function (responseText) {
      var geojson = JSON.parse(responseText);

      feed_map.addSource("service-patterns", { type: "geojson", data: geojson });

      // Add line markers
      feed_map.addLayer({
        id: "service-patterns",
        type: "line",
        source: "service-patterns",
        layout: {
          "line-join": "round",
          "line-cap": "round",
        },
        paint: {
          "line-color": "#49A39A",
          "line-width": 2,
        },
      });

      // Add hover effect
      feed_map.addLayer({
        id: "service-patterns-hover",
        type: "line",
        source: "service-patterns",
        layout: {},
        paint: {
          "line-color": "#34746e",
          "line-width": [
            "case",
            ["boolean", ["feature-state", "hover"], false],
            4.5,
            0,
          ],
        },
      });

      // When the user moves their mouse over the state-fill layer, we'll update the
      // feature state for the feature under the mouse.
      feed_map.on("mousemove", "service-patterns", function (e) {
        if (e.features.length > 0) {
          if (hoveredStateId) {
            feed_map.setFeatureState(
              { source: "service-patterns", id: hoveredStateId },
              { hover: false }
            );
          }
          hoveredStateId = e.features[0].id;
          feed_map.setFeatureState(
            { source: "service-patterns", id: hoveredStateId },
            { hover: true }
          );
        }
      });

      // When the mouse leaves the state-fill layer, update the feature state of the
      // previously hovered feature.
      feed_map.on("mouseleave", "service-patterns", function () {
        if (hoveredStateId) {
          feed_map.setFeatureState(
            { source: "service-patterns", id: hoveredStateId },
            { hover: false }
          );
        }
        hoveredStateId = null;
      });

      // Fit map to features
      var bounds = new mapboxgl.LngLatBounds();

      // loop over LineString features and calculate bounds
      geojson.features.forEach(function (feature) {
        if (feature.geometry && feature.geometry.coordinates) {
          bounds.extend(getLineStringBounds(feature.geometry.coordinates));
        }
      });

      if (!bounds.isEmpty()) {
        feed_map.fitBounds(bounds, {
          padding: 20,
        });
      }

      // After initially fitting the map, on pan fetch new data at location
      // feed_map.on('moveend', onMoveEndHandler)
    });

    // Create a popup, but don't add it to the map yet.
    var popup = new mapboxgl.Popup({
      closeButton: false,
      closeOnClick: false,
    });

    feed_map.on("mouseenter", "service-patterns", function (e) {
      // Change the cursor style as a UI indicator.
      feed_map.getCanvas().style.cursor = "pointer";

      var description =
        "Service number: " + e.features[0].properties.line_name;

      // Populate the popup and set its coordinates
      // based on the feature found.
      popup.setLongLat(e.lngLat).setHTML(description).addTo(map);
    });

    feed_map.on("mouseleave", "service-patterns", function () {
      feed_map.getCanvas().style.cursor = "";
      popup.remove();
    });
  });
};

const getCurrentDateTime = () => {
  const now = new Date();
  const day = String(now.getDate()).padStart(2, '0');
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const seconds = String(now.getSeconds()).padStart(2, '0');
  const year = now.getFullYear();
  let hours = now.getHours();
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const ampm = hours >= 12 ? 'PM' : 'AM';
  hours = hours % 12 || 12; // Convert 0 to 12 for 12-hour format
  return `${day}/${month}/${year} ${String(hours).padStart(2, '0')}:${minutes}:${seconds} ${ampm}`;
}

const addMarker = (feed_map, vehicle_ref, long, lat, vehicle_journey_code) => {
  if (feed_map_markers.hasOwnProperty(vehicle_ref)) {
    feed_map_markers[vehicle_ref].setLongLat([long, lat])
  } else {
    feed_map_markers[vehicle_ref] = new mapboxgl.Marker(customMarker.cloneNode(true))
      .setLongLat([long, lat]) // Longitude, Latitude
      .setPopup(new mapboxgl.Popup().setHTML(`<h3>Vehicle Ref: ${vehicle_ref}</h3>
        <p>Vehicle Journey Code: ${vehicle_journey_code}</p>
        `))
      .addTo(feed_map);
    }
}

const removeExtraVehicleMarkers = (data) => {
  for (const key in feed_map_markers) {
    if (!data.hasOwnProperty(key)) {
        feed_map_markers[key].remove()
        delete feed_map_markers[key]
    }
  }
}

const fetchAvlLiveLocation = (apiUrl) => {
  fetch(apiUrl)
      .then(response => response.json())
      .then(data => {
        for (const key in data) {
          console.log("data is >> " + data[key].VehicleJourneyCode)
          if (data.hasOwnProperty(key)) {
              addMarker(feed_map, key, data[key].Longitude, data[key].Latitude, data[key].VehicleJourneyCode)
          }
        }
        removeExtraVehicleMarkers(data)
      })
      .catch(error => {
          console.log("Error while calling AVL real time data API" + error)
      });
      var updated_at_text = `Last updated at - ${getCurrentDateTime()}`
      document.getElementById("map-updated-timestamp").innerText = updated_at_text;
  setTimeout(fetchAvlLiveLocation, 10000, apiUrl);
}

export { initMap, fetchAvlLiveLocation };

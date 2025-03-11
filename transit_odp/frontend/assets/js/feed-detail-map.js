const mapboxgl = require("mapbox-gl");
var feed_map = null
var feed_map_markers = {}
const customMarker = document.createElement('div');
customMarker.style.backgroundImage = 'url(data:image/png;base64,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)'; // Replace with your icon URL
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
      popup.setLngLat(e.lngLat).setHTML(description).addTo(map);
    });

    feed_map.on("mouseleave", "service-patterns", function () {
      feed_map.getCanvas().style.cursor = "";
      popup.remove();
    });
  });
};

const addMarker = (feed_map, vehicle_ref, long, lat) => {
  if (feed_map_markers.hasOwnProperty(vehicle_ref)) {
    feed_map_markers[vehicle_ref].setLngLat([long, lat])
  } else {
    feed_map_markers[vehicle_ref] = new mapboxgl.Marker(customMarker.cloneNode(true))
      .setLngLat([long, lat]) // Longitude, Latitude
      .setPopup(new mapboxgl.Popup().setHTML(`<h3>Vehicle Ref: ${vehicle_ref}</h3>`))
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
  console.log("Called and received the following url" + apiUrl)
  fetch(apiUrl)
      .then(response => response.json())
      .then(data => {
        for (const key in data) {
          if (data.hasOwnProperty(key)) {
              addMarker(feed_map, key, data[key].Longitude, data[key].Latitude)
          }
        }
        removeExtraVehicleMarkers(data)
      })
      .catch(error => {
          console.log("ERRRORR" + error)
      });
  setTimeout(fetchAvlLiveLocation, 10000, apiUrl);
}

export { initMap, fetchAvlLiveLocation };

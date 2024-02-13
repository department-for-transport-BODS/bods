const mapboxgl = require("mapbox-gl");

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

const getMapDataUrl = (apiRoot, revisionId, serviceName) => {
  var servicePatternUrl =
    apiRoot + "service_pattern/?revision=" + revisionId.toString();
  if (serviceName) {
    servicePatternUrl += "&service_name=" + serviceName.toString();
  }
  return servicePatternUrl;
};

const initMap = (apiRoot, revisionId, serviceName) => {
  var servicePatternUrl = getMapDataUrl(apiRoot, revisionId, serviceName);

  // Initialise Map
  mapboxgl.accessToken =
    "pk.eyJ1IjoiaGFsYmVydHJhbSIsImEiOiJjaXFiNXVnazIwMDA0aTJuaGxlaTU1M2ZtIn0.85dXvyj6V2LbBFvXfpQyYA";
  var map = new mapboxgl.Map({
    container: "map",
    style: "mapbox://styles/mapbox/light-v9",
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
  for (var i = 0; i < logoArray.length; i++) {
    logoArray[i].setAttribute("tabindex", -1);
  }
  // zoom buttons
  let zoomObject = map["_controls"].find((o) =>
    o.hasOwnProperty("_zoomInButton")
  );
  zoomObject["_zoomInButton"].setAttribute("tabindex", -1);
  zoomObject["_zoomOutButton"].setAttribute("tabindex", -1);

  var hoveredStateId = null;

  // Fetch ServicePattern GeoJSON
  map.on("load", function () {
    httpGetAsync(servicePatternUrl, function (responseText) {
      var geojson = JSON.parse(responseText);

      map.addSource("service-patterns", { type: "geojson", data: geojson });

      // Add line markers
      map.addLayer({
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
      map.addLayer({
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
      map.on("mousemove", "service-patterns", function (e) {
        if (e.features.length > 0) {
          if (hoveredStateId) {
            map.setFeatureState(
              { source: "service-patterns", id: hoveredStateId },
              { hover: false }
            );
          }
          hoveredStateId = e.features[0].id;
          map.setFeatureState(
            { source: "service-patterns", id: hoveredStateId },
            { hover: true }
          );
        }
      });

      // When the mouse leaves the state-fill layer, update the feature state of the
      // previously hovered feature.
      map.on("mouseleave", "service-patterns", function () {
        if (hoveredStateId) {
          map.setFeatureState(
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
        map.fitBounds(bounds, {
          padding: 20,
        });
      }

      // After initially fitting the map, on pan fetch new data at location
      // map.on('moveend', onMoveEndHandler)
    });

    // Create a popup, but don't add it to the map yet.
    var popup = new mapboxgl.Popup({
      closeButton: false,
      closeOnClick: false,
    });

    map.on("mouseenter", "service-patterns", function (e) {
      // Change the cursor style as a UI indicator.
      map.getCanvas().style.cursor = "pointer";

      var description =
        "Service number: " + e.features[0].properties.service_name;

      // Populate the popup and set its coordinates
      // based on the feature found.
      popup.setLngLat(e.lngLat).setHTML(description).addTo(map);
    });

    map.on("mouseleave", "service-patterns", function () {
      map.getCanvas().style.cursor = "";
      popup.remove();
    });
  });
};

export { initMap };

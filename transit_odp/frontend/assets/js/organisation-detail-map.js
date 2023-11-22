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

const initOrgMap = (apiRoot, orgId) => {
  var servicePatternUrl =
    apiRoot + "organisation_map_data/?pk=" + orgId.toString();

  // Initialise Map
  mapboxgl.accessToken =
    "pk.eyJ1IjoiaGFsYmVydHJhbSIsImEiOiJjaXFiNXVnazIwMDA0aTJuaGxlaTU1M2ZtIn0.85dXvyj6V2LbBFvXfpQyYA";
  var map = new mapboxgl.Map({
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
    // Create a popup, but don't add it to the map yet.
    var stopsPopup = new mapboxgl.Popup({
      closeButton: false,
      closeOnClick: false,
    });

    httpGetAsync(servicePatternUrl, function (responseText) {
      var geojson = JSON.parse(responseText);

      var servicesGeoJSON = {};
      var stopsGeoJSON = {};

      if (geojson) {
        servicesGeoJSON = geojson.services;
        stopsGeoJSON = geojson.stops;
      }

      map.addSource("organisation-services", {
        type: "geojson",
        data: servicesGeoJSON,
      });

      map.addSource("organisation-stops", {
        type: "geojson",
        data: stopsGeoJSON,
      });

      map.getSource("organisation-stops");

      // Add point markers
      map.addLayer({
        id: "organisation-stops",
        type: "circle",
        source: "organisation-stops",
        paint: {
          "circle-color": "#2E8CD2",
          "circle-radius": 5,
        },
      });

      // Add line markers
      map.addLayer({
        id: "organisation-services",
        type: "line",
        source: "organisation-services",
        layout: {
          "line-join": "round",
          "line-cap": "round",
        },
        paint: {
          "line-color": "#2E8CD2",
          "line-width": 2,
        },
      });

      // Add hover effect
      map.addLayer({
        id: "organisation-services-hover",
        type: "line",
        source: "organisation-services",
        layout: {},
      });

      // When the user moves their mouse over the state-fill layer, we'll update the
      // feature state for the feature under the mouse.
      map.on("mousemove", "organisation-services", function (e) {
        if (e.features.length > 0) {
          if (hoveredStateId) {
            map.setFeatureState(
              { source: "organisation-services", id: hoveredStateId },
              { hover: false }
            );
          }
          hoveredStateId = e.features[0].properties.service_line_id;
          map.setFeatureState(
            { source: "organisation-services", id: hoveredStateId },
            { hover: true }
          );
        }
      });

      // When the mouse leaves the state-fill layer, update the feature state of the
      // previously hovered feature.
      map.on("mouseleave", "organisation-services", function () {
        if (hoveredStateId) {
          map.setFeatureState(
            { source: "organisation-services", id: hoveredStateId },
            { hover: false }
          );
        }
        hoveredStateId = null;
      });

      // Fit map to features
      var bounds = new mapboxgl.LngLatBounds();

      // loop over LineString features and calculate bounds
      servicesGeoJSON.features.forEach(function (feature) {
        if (feature.geometry && feature.geometry.coordinates) {
          bounds.extend(getLineStringBounds(feature.geometry.coordinates));
        }
      });

      // Fit map to features
      stopsGeoJSON.features.forEach(function (feature) {
        if (feature.geometry && feature.geometry.coordinates) {
          bounds.extend(feature.geometry.coordinates);
        }
      });

      if (!bounds.isEmpty()) {
        map.fitBounds(bounds, {
          padding: 20,
        });
      }
    });

    map.on("mouseenter", "organisation-stops", (e) => {
      // Change the cursor style as a UI indicator.
      map.getCanvas().style.cursor = "pointer";

      var display_str =
        "Atco: " +
        e.features[0].properties.atco_code +
        ", Name: " +
        e.features[0].properties.common_name;

      // Populate the popup and set its coordinates
      // based on the feature found.
      stopsPopup.setLngLat(e.lngLat).setHTML(display_str).addTo(map);
    });

    map.on("mouseleave", "organisation-stops", function () {
      map.getCanvas().style.cursor = "";
      stopsPopup.remove();
    });

    // Create a popup, but don't add it to the map yet.
    var popup = new mapboxgl.Popup({
      closeButton: false,
      closeOnClick: false,
    });

    map.on("mouseenter", "organisation-services", function (e) {
      // Change the cursor style as a UI indicator.
      map.getCanvas().style.cursor = "pointer";

      var description =
        "Service number: " + e.features[0].properties.service_line_name;

      // Populate the popup and set its coordinates
      // based on the feature found.
      popup.setLngLat(e.lngLat).setHTML(description).addTo(map);
    });

    map.on("mouseleave", "organisation-services", function () {
      map.getCanvas().style.cursor = "";
      popup.remove();
    });
  });
};

export { initOrgMap };

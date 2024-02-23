// Largely duplicates feed-detail-map. As DQ maps progress, refactor to remove
// duplication

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

const showPopup = (event, map, popup) => {
  const generateDescription = (feature) => {
    let properties = feature.properties;
    let description = "";
    const useServiceName = ["service-links", "service-patterns"];

    if (useServiceName.includes(feature.source)) {
      description = `Service: ${properties.service_name}`;
    } else if (feature.source === "stop-points") {
      description = `Stop point: ${properties.name} (${properties.atco_code})`;
    }
    return description;
  };

  // Change the cursor style as a UI indicator.
  map.getCanvas().style.cursor = "pointer";

  let feature = event.features[0];
  let description = generateDescription(feature);

  // Populate the popup and set its coordinates based on the feature found.
  popup.setLngLat(event.lngLat).setHTML(description).addTo(map);
};

const hidePopup = (event, map, popup) => {
  map.getCanvas().style.cursor = "";
  popup.remove();
};

const addHover = (e, map) => {
  // When the user moves their mouse over the layer, update the
  // feature state for the feature under the mouse.
  if (e.features.length > 0) {
    let feature = e.features[0];
    map.setFeatureState(
      { source: feature.source, id: feature.id },
      { hover: true }
    );
  }
};

const removeHover = (e, map, layer) => {
  // When the mouse leaves the layer, update the feature state of the
  // previously hovered feature.
  let features = map.queryRenderedFeatures({ layers: [layer] });
  features.forEach((feature) =>
    map.setFeatureState(
      { source: feature.source, id: feature.id },
      { hover: false }
    )
  );
};

const fitToBounds = (geojson, map) => {
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
};

// refactor to reduce number of params? Maybe expect apiRoot + one other argument,
// then unpack in function?
const initWarningDetailMap = (
  apiRoot,
  servicePatternId,
  stopPointIds,
  effectedStopIds,
  serviceLinkIds
) => {
  // Define API urls
  let [serviceLinkUrl, servicePatternUrl, stopPointUrl] = Array(3).fill(null);

  // Try to do more concisely in a loop?
  if (serviceLinkIds !== "") {
    serviceLinkUrl =
      apiRoot + "service_link/?id__in=" + serviceLinkIds.toString();
  }
  if (servicePatternId !== "") {
    servicePatternUrl =
      apiRoot + "service_pattern/?id=" + servicePatternId.toString();
  }
  if (stopPointIds !== "") {
    stopPointUrl = apiRoot + "stop_point/?id__in=" + stopPointIds.toString();
    if (effectedStopIds !== "") {
      stopPointUrl = stopPointUrl + "&effected=" + effectedStopIds.toString();
    }
  }

  // Initialise Map
  mapboxgl.accessToken = mapboxKey;
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

  map.on("load", function () {
    // Create a popup, but don't add it to the map yet.
    var popup = new mapboxgl.Popup({
      closeButton: false,
      closeOnClick: false,
    });

    // Fetch StopPoint GeoJSON
    if (stopPointUrl) {
      httpGetAsync(stopPointUrl, function (responseText) {
        var stopPointGeoJson = JSON.parse(responseText);

        map.addSource("stop-points", {
          type: "geojson",
          data: stopPointGeoJson,
        });
        map.getSource("stop-points");

        // Add point markers
        map.addLayer({
          id: "stop-points",
          type: "circle",
          source: "stop-points",
          paint: {
            "circle-color": [
              "case",
              ["boolean", ["get", "effected"], true],
              "#ff0000",
              "#49A39A",
            ],
            "circle-radius": [
              "case",
              ["boolean", ["feature-state", "hover"], false],
              7,
              5,
            ],
          },
        });

        // consider moving to OOP approach (see dqs-review-panel.js) rather than this functional approach
        map.on("mouseenter", "stop-points", (e) => {
          showPopup(e, map, popup);
          addHover(e, map);
        });
        map.on("mouseleave", "stop-points", (e) => {
          hidePopup(e, map, popup);
          removeHover(e, map, "stop-points");
        });
      });
    }

    if (serviceLinkUrl) {
      httpGetAsync(serviceLinkUrl, function (responseText) {
        var serviceLinkGeojson = JSON.parse(responseText);

        map.addSource("service-links", {
          type: "geojson",
          data: serviceLinkGeojson,
        });
        map.getSource("service-links");

        // Add line markers
        map.addLayer({
          id: "service-links",
          type: "line",
          source: "service-links",
          layout: {
            "line-join": "round",
            "line-cap": "round",
          },
          paint: {
            "line-color": "#49A39A",
            "line-width": [
              "case",
              ["boolean", ["feature-state", "hover"], false],
              4.5,
              2,
            ],
          },
        });

        // Only fit map to bounds based on service links if no service pattern
        if (!servicePatternUrl) {
          fitToBounds(serviceLinkGeojson, map);
        }

        // consider moving to OOP approach (see dqs-review-panel.js) rather than this functional approach
        map.on("mouseenter", "service-links", (e) => {
          showPopup(e, map, popup);
          addHover(e, map);
        });
        map.on("mouseleave", "service-links", (e) => {
          hidePopup(e, map, popup);
          removeHover(e, map, "service-links");
        });
      });
    }

    if (servicePatternUrl) {
      httpGetAsync(servicePatternUrl, function (responseText) {
        var geojson = JSON.parse(responseText);

        map.addSource("service-patterns", { type: "geojson", data: geojson });
        map.getSource("service-patterns");

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
            "line-width": [
              "case",
              ["boolean", ["feature-state", "hover"], false],
              4.5,
              2,
            ],
          },
        });

        // Fit map to features
        fitToBounds(geojson, map);
      });

      // consider moving to OOP approach (see dqs-review-panel.js) rather than this
      // functional approach
      map.on("mouseenter", "service-patterns", (e) => {
        showPopup(e, map, popup);
        addHover(e, map);
      });
      map.on("mouseleave", "service-patterns", (e) => {
        hidePopup(e, map, popup);
        removeHover(e, map, "service-patterns");
      });
    }
  });
};

export { initWarningDetailMap };

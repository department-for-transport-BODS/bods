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

const fitToBounds = (geojson, map) => {
  // Fit map to features
  var bounds = new mapboxgl.LngLatBounds();

  // loop over LineString features and calculate bounds
  geojson.features.forEach(function (feature) {
    if (feature.geometry && feature.geometry.coordinates) {
      bounds.extend(feature.geometry.coordinates);
    }
  });

  if (!bounds.isEmpty()) {
    map.fitBounds(bounds, {
      padding: 20,
    });
  }
};

// refactor to reduce number of params? Maybe expect apiRoot + one other argument, then unpack in function?
const initFaresDetailMap = (apiRoot, revisionId) => {
  var stopPointUrl = apiRoot + "fare_stops/?revision=" + revisionId.toString();

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

  map.on("load", function () {
    // Create a popup, but don't add it to the map yet.
    var popup = new mapboxgl.Popup({
      closeButton: false,
      closeOnClick: false,
    });

    // Fetch StopPoint GeoJSON
    if (stopPointUrl) {
      httpGetAsync(stopPointUrl, function (responseText) {
        var geojson = JSON.parse(responseText);

        map.addSource("stop-points", {
          type: "geojson",
          data: geojson,
        });

        map.getSource("stop-points");

        // Add point markers
        map.addLayer({
          id: "stop-points",
          type: "circle",
          source: "stop-points",
          paint: {
            "circle-color": "#49A39A",
            "circle-radius": 5,
          },
        });
        // Fit map to features
        fitToBounds(geojson, map);
      });
      map.on("mouseenter", "stop-points", (e) => {
        // Change the cursor style as a UI indicator.
        map.getCanvas().style.cursor = "pointer";

        var display_str =
          "Atco: " +
          e.features[0].properties.atco_code +
          ", Name: " +
          e.features[0].properties.common_name;

        // Populate the popup and set its coordinates
        // based on the feature found.
        popup.setLngLat(e.lngLat).setHTML(display_str).addTo(map);
      });

      map.on("mouseleave", "stop-points", function () {
        map.getCanvas().style.cursor = "";
        popup.remove();
      });
    }
  });
};

export { initFaresDetailMap };

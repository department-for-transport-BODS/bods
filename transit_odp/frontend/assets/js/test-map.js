const mapboxgl = require("mapbox-gl");
const MapboxglSpiderifier = require('mapboxgl-spiderifier')
const _ = require('lodash');
const $ = require('jquery');
const initOrgMap=()=>{
  mapboxgl.accessToken = mapboxKey;
  var iconTypes = ['car', 'bicycle', 'bus', 'cab', 'truck', 'train', 'rocket', 'ship'];
  var iconColors = ['red', 'blue', 'green', 'orange', '#ab1234', '#112312'];
  var randomMarker = function(index){
    return {
      id: index,
      type: _.sample(iconTypes),
      color: _.sample(iconColors)
    }
  };

  
  window.onload=function(){
    var map = new mapboxgl.Map({
      container: 'map',
      style: 'mapbox://styles/mapbox/streets-v9',
      center: [-74.50, 40],
      zoom: 7,
    });
    var spiderifier = new MapboxglSpiderifier(map, {
      animate: true,
      animationSpeed: 200,
      customPin: true,
      initializeLeg: function(spiderLeg) {
        var $spiderPinCustom = $('<div>', {class: 'spider-point-circle'});
  
        $(spiderLeg.elements.pin).append($spiderPinCustom);
        $spiderPinCustom.css({
          'width': '40px',
          'height':'40px',
          'margin-left': '-20px',
          'margin-top': '-20px',
          'background-color': spiderLeg.feature.color,
          'opacity': 0.8,
          'position': 'relative',
          "font-size": "20px"
        });
  
        var popup = new mapboxgl.Popup({
          closeButton: true,
          closeOnClick: false,
          offset: MapboxglSpiderifier.popupOffsetForSpiderLeg(spiderLeg)
        });
  
        popup.setHTML('Feature type is ' + spiderLeg.feature.type);
        spiderLeg.mapboxMarker.setPopup(popup);
  
        $(spiderLeg.elements.container)
          .on('mouseenter', function(){
            popup.addTo(map);
          })
          .on('mouseleave', function(){
            popup.remove();
          });
      }
    })


    map.on('style.load', function() {
      map.addSource('circle', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: [
            {type: 'feature',
            properties: {count: 6},
            geometry: {
              type: 'Point',
              coordinates: [-74.50, 40]
            }},
            {type: 'feature',
            properties: {count: 20},
            geometry: {
              type: 'Point',
              coordinates: [-75.50, 40.5]
            }},
            {type: 'feature',
            properties: {count: 50},
            geometry: {
              type: 'Point',
              coordinates: [-76.0, 39.5]
            }}
          ]
        }
      });

      map.addLayer({
        'id': 'circle',
        'type': 'circle',
        'source': 'circle',
        'paint': {
          'circle-radius': 30,
          'circle-color': '#288DC1',
          'circle-opacity': 0.8
        },
      });
      map.on('mousemove', mouseMove);
      map.on('click', mouseClick);
    });
    
    function mouseClick(e) {
      var clickedOnFeatures = map.queryRenderedFeatures(e.point, {
        layers: ['circle']
      });

      if (!clickedOnFeatures.length) {
        spiderifier.unspiderfy();
        return;
      }

      var clickedOnFeature = clickedOnFeatures[0];
      var features = _.map(_.range(clickedOnFeature.properties.count), randomMarker);
      spiderifier.spiderfy(clickedOnFeature.geometry.coordinates, features);
    }

    function mouseMove(e) {
      var features = map.queryRenderedFeatures(e.point, {
        layers: ['circle']
      });
      map.getCanvas().style.cursor = (features.length) ? 'pointer' : '';
    }
    
}
}

export { initOrgMap };
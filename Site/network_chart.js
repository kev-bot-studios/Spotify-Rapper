
var chart;
anychart.onDocumentReady(function () {
  anychart.data.loadJsonFile(
    // The data used in this sample can be obtained from the CDN
    'artist_map.json',
    function (data) {
      // create graph chart
      chart = anychart.graph(data);

      // set chart layout settings
      chart.layout({ iterationCount: 0 });

      // set node labels settings
      chart
        .nodes()
        .labels()
        .fontSize(12)
        .enabled(true)
        .anchor('auto')
        .autoRotate(true);

      // set container id for the chart
      chart.container('container');

      // initiate chart drawing
      chart.draw();

      // set default zoom
      chart.zoom(
        .95,
        chart.getPixelBounds().width / 2,
        chart.getPixelBounds().height / 2
      );
      
      //
      chart.tooltip(false);  

      // disable drag and drop
      chart.interactivity().enabled(false);
      
      // disable zoom with mouse wheel
      chart.interactivity().zoomOnMouseWheel(false);  

    }
  );
});
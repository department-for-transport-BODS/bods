var $ = require("jquery");

const INTERVAL_LENGTH = 1000;

const move = width => {
  let elem = document.getElementById("progressInnerDiv");
  elem.style.width = width + "%";
  // elem.setAttribute('aria-valuenow', width);
  // elem.innerText = width + '%';
  let para_elem = document.getElementById("progressSpan");
  para_elem.innerText = width + "%";
};

const getProgress = datasetId => {
  const url = `/dataset/${datasetId}/progress/`;
  let interval;

  const poll = url =>
    $.ajax({
      type: "GET",
      url: url,
      headers: {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        Pragma: "no-cache",
        Expires: "0"
      },
      // data: {
      //     task_id : task_id,
      // },
      success: response => {
        let progress = response["progress"];
        // console.log('progress: ' + progress);
        move(progress);
        if (progress === 100) {
          clearInterval(interval);
          // refresh the page after progress is 100
          window.location.reload(false);
        }
      },
      complete: (jqXHR, response) => {
        if (jqXHR.status !== 200) {
          clearInterval(interval);
          // request.abort();
        }
      }
    });

  interval = setInterval(poll, INTERVAL_LENGTH, url);
};

module.exports = getProgress;

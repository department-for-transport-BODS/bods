/**
 * Add the class to show the tooltip
 * @param {documentEvent} event - Event to get the triggered point
 * @param {string} rowIndex - Row index of the table
 * @param {string} direction - Direction whether the inbound or outbound
 *
 * @example toggleTooltip('1', 'inbound') will add the class to show the tooltip
 */
function showTooltip(event, rowIndex, direction=null, type=null) {
  hideAllTooltips();
  if (type === "observation") {
  const TARGET = document.getElementById(rowIndex);
  TARGET.classList.add("showtooltip");
  return;
  }
  // Only call the function when the event is triggered by the stop
  if (event.target.id.startsWith("stop-")) {
    const elemId = "tooltip-" + direction + "-" + rowIndex;
    document.getElementById(elemId).classList.add("showtooltip");
  }
}

/**
 * Remove all the tooltip(s) if present
 *
 */
function hideAllTooltips() {
  document.querySelectorAll("p.tooltiptext.showtooltip, div.tooltiptext.showtooltip").forEach((element) => {
    element.classList.remove("showtooltip");
  });
}

/**
 *
 * Remove the class to hide the tooltip
 * @param {string} rowIndex - Row index of the table
 * @param {string} direction - Direction whether the inbound or outbound
 */
function hideTooltip(event) {
  event.target.parentElement.classList.remove("showtooltip");
}

/**
 *
 * Add the eventListener to close all the tooltips if clicked on the document having tooltips
 */
if (document.querySelectorAll("p.tooltiptext").length > 0) {
  document.addEventListener("click", function (event) {
    if (!event.target.id.startsWith("stop-")) {
      hideAllTooltips();
    }
  });
}

function disableClick(event) {
  event.stopPropagation();
}

export { showTooltip, hideTooltip, disableClick };

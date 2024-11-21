/**
 * Add the class to show the tooltip
 * @param {documentEvent} event - Event to get the triggered point
 * @param {string} rowIndex - Row index of the table
 * @param {string} direction - Direction whether the inbound or outbound
 *
 * @example toggleTooltip('1','0', 'inbound') will add the class to show the tooltip
 */

function showTooltip(event, rowIndex, direction = null, type = null) {
  const manageTooltip = (id) => {
    hideAllTooltips(id);
    const target = document.getElementById(id);
    if (isToolTipOpen(target)) {
      target.classList.remove("showtooltip");
    } else {
      target.classList.add("showtooltip");
    }
  };
  if (type === "observation") {
    manageTooltip(rowIndex);
    return;
  }
  if (event.target.id.startsWith("stop-")) {
    const elemId = `tooltip-${direction}-${rowIndex}`;
    manageTooltip(elemId);
  }
}

function isToolTipOpen(element) {
  // Check if element has showtooltip class
  const classes = element.classList;
  if (element.classList.contains("showtooltip")) {
    return true;
  }
  return false;
}
/**
 * Remove all the tooltip(s) if present
 *
 */
function hideAllTooltips(exception = null) {
  document.querySelectorAll(".tooltiptext.showtooltip").forEach((element) => {
    if (!(exception && element.id === exception)) {
      element.classList.remove("showtooltip");
    }
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

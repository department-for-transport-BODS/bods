const copyToClipboard = (text) => {
  let tempInput = document.createElement("textArea");
  tempInput.setAttribute(
    "style",
    "position: absolute; left: -1000px; top: -1000px"
  );
  // The value property needs to be changed not the value attribute see
  // https://stackoverflow.com/questions/29929797/setattribute-doesnt-work-the-way-i-expect-it-to
  tempInput.value = text;

  document.body.appendChild(tempInput);

  if (isOS()) {
    let range = document.createRange();
    range.selectNodeContents(tempInput);
    let selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    tempInput.setSelectionRange(0, 999999);
  } else {
    tempInput.select();
  }
  document.execCommand("copy");
  document.body.removeChild(tempInput);
};

const isOS = () => {
  return navigator.userAgent.match(/ipad|iphone/i);
};

export { copyToClipboard };

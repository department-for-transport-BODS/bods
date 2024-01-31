// TODO - create CrispyFormsGovUK.init() method which creates onClick listeners implicitly rather than in HTML
//  Use querySelectorAll('[data-module="app-radio-accordion"]') to select component rather than imperatively passing id

var CrispyFormsGovUK = {
  onRadioSelect: function(accordionId, hiddenContentId) {
    var allInputs = document.querySelectorAll(
      "#" + accordionId + " input:not([name='selected_item'])"
    );
    for (var i = 0; i < allInputs.length; i++) {
      allInputs[i].disabled = true;
    }

    var inputs = document.querySelectorAll("#" + hiddenContentId + " input");

    for (i = 0; i < inputs.length; i++) {
      inputs[i].disabled = false;
    }
  }
};

// Ideally this would be packaged as a UMD to work both directly linked from the DOM and with a bundler.
// The latter is the approach taken in BODS, see main.js.
module.exports = CrispyFormsGovUK;

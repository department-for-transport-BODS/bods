export class CrispyFormsGovUK {
  static onRadioSelect(accordionId, hiddenContentId) {
    let allInputs = document.querySelectorAll(
      "#" + accordionId + " input:not([name='selected_item'])"
    );
    allInputs.forEach((item) => {
      item.disabled = true;
    });

    let inputs = document.querySelectorAll("#" + hiddenContentId + " input");
    inputs.forEach((item) => {
      item.disabled = false;
    });
  }
}

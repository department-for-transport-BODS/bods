const TOTAL_FORM_SELECTOR = "input[name$=-TOTAL_FORMS]";
const ADD_BUTTON_SELECTOR = "button[name$=-ADD]";
const PARENT_CONTAINER_TAG = "tr";

export function upToParent(element, tagName) {
  tagName = tagName.toLowerCase();

  while (element && element.parentNode) {
    element = element.parentNode;
    if (element.tagName && element.tagName.toLowerCase() == tagName) {
      return element;
    }
  }
  return null;
}

export class FormSet {
  constructor(formContainer) {
    this._formContainer = formContainer;
    this._tableBody =
      formContainer.getElementsByClassName("govuk-table__body")[0];
    this._forms = [...formContainer.getElementsByClassName("form-container")];
    this._copyTemplate = this._forms.pop();
    this._mgmtFormTotal =
      this._formContainer.querySelector(TOTAL_FORM_SELECTOR);
    this._addButton = this._formContainer.querySelector(ADD_BUTTON_SELECTOR);
    this._addButton.addEventListener("click", this.onAddButton.bind(this));

    for (const form of this._forms) {
      const deleteButton = form.getElementsByTagName("button")[0];
      deleteButton.previousElementSibling.value = "";
      deleteButton.addEventListener("click", this.onDeleteButton.bind(this));

      const selectBox = form.getElementsByTagName("select")[0];
      selectBox.addEventListener("change", this.onChangeLicence.bind(this));

      const inputDiv = form.getElementsByClassName("service-code-widget")[0];
      inputDiv.lastElementChild.addEventListener(
        "change",
        this.onChangeServiceCode.bind(this)
      );
    }
  }

  _reIndexTable() {
    // reindexes tag attributes so there are no gaps, this is important otherwise
    // django formsets will instantiate blank forms in the backend and it will be
    // treated like the user is sending up blank forms.

    const regex = /\d+/g;
    const tags = ["td", "input", "select"];
    const attributes = ["name", "aria-label", "id"];

    this._forms.forEach((row, index) => {
      row.id = row.id.replace(regex, index);
      for (const tag of tags) {
        for (const element of row.getElementsByTagName(tag)) {
          for (const attribute of attributes) {
            const oldAttribute = element.getAttribute(attribute);
            if (oldAttribute) {
              element.setAttribute(
                attribute,
                oldAttribute.replace(regex, index)
              );
            }
          }
        }
      }
    });
  }

  get TotalForms() {
    return parseInt(this._mgmtFormTotal.value);
  }

  set TotalForms(value) {
    this._mgmtFormTotal.value = value;
  }

  onAddButton(event) {
    this._tableBody.insertAdjacentHTML(
      "beforeend",
      this._copyTemplate.outerHTML.replace(
        /__prefix__/g,
        this.TotalForms.toString()
      )
    );
    const newForm = this._tableBody.lastElementChild;
    this._forms.push(newForm);
    const deleteButton = newForm.getElementsByTagName("button")[0];
    deleteButton.addEventListener("click", this.onDeleteButton.bind(this));

    const selectBox = newForm.getElementsByTagName("select")[0];
    selectBox.addEventListener("change", this.onChangeLicence.bind(this));

    const ptag = newForm.getElementsByTagName("p")[0];
    ptag.style.display = "none";

    const inputDiv = newForm.getElementsByClassName("service-code-widget")[0];
    inputDiv.lastElementChild.addEventListener(
      "change",
      this.onChangeServiceCode.bind(this)
    );

    this.TotalForms++;
  }

  onDeleteButton(event) {
    const deleteInput = event.target.previousElementSibling;
    const id = deleteInput.getAttribute("name").replace(/DELETE/, "id");
    const containerRow = upToParent(deleteInput, PARENT_CONTAINER_TAG);
    const idInput = containerRow.querySelector(`[name=${id}]`);

    if (idInput.value) {
      // django created objects
      deleteInput.value = "on";
      containerRow.style.display = "none";
    } else {
      // javascript created objects
      containerRow.remove();
      this._forms = this._forms.filter((item) => item !== containerRow);
      this._reIndexTable();
      this.TotalForms--;
    }
  }

  onChangeLicence(event) {
    const selectBox = event.target;
    const index = selectBox.selectedIndex;
    const value = selectBox.options[index].text;
    const row = upToParent(selectBox, PARENT_CONTAINER_TAG);
    const ptag = row.getElementsByTagName("p")[0];
    const input = row.getElementsByClassName("service-code-widget")[0]
      .lastElementChild;
    if (index > 0 && input.value !== "") {
      // Not a placeholder value
      ptag.innerText = `${value}/`;
      ptag.style.display = "block";
    } else {
      ptag.style.display = "none";
    }
  }

  onChangeServiceCode(event) {
    const input = event.target;
    const row = upToParent(input, PARENT_CONTAINER_TAG);
    const ptag = row.getElementsByTagName("p")[0];
    const selectBox =
      row.getElementsByClassName("select-wrapper")[0].firstElementChild;
    const index = selectBox.selectedIndex;
    const value = selectBox.options[index].text;
    if (index > 0 && input.value !== "") {
      // Not a placeholder
      ptag.innerText = `${value}/`;
      ptag.style.display = "block";
    } else {
      ptag.style.display = "none";
    }
  }
}

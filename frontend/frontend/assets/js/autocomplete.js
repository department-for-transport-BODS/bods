const keyDownCode = 40;
const keyUpCode = 38;
const keyEnterCode = 13;
const activeClass = "autocomplete-active";
const containerID = "autocomplete-list";
const itemsClass = "autocomplete-items";

/** Class representing an autocomplete search box.*/
export class AutoCompleteSearch {
  /**
   * Create an autocomplete search box.
   * @param {string} searchBoxId - The search box to add autocomplete to.
   * @param {array[string]} terms - The list of terms to use to autocomplete.
   */
  constructor(searchBoxId, terms) {
    this.terms = terms;
    this.searchBox = document.getElementById(searchBoxId);
    this.currentFocus = -1;
    this.button = this.searchBox.nextElementSibling;
    this.id = this.searchBox.id;
    this.init();
  }

  /**
   * Initialise event listeners for searchBox.
   */
  init() {
    this.searchBox.addEventListener("input", () => {
      this.search(this.searchBox.value);
    });
    document.addEventListener("click", (clickEvent) => {
      this.removeSuggestions(clickEvent.target);
    });
    this.searchBox.addEventListener("keydown", (keyboardEvent) => {
      this.handleKeyboardInput(keyboardEvent);
    });
  }

  /**
   * Handle inputs from the keyboard.
   * @param {} keyboardEvent - The keyboard event to handle.
   */
  handleKeyboardInput(keyboardEvent) {
    const container = document.getElementById(this.id + containerID);

    let suggestions;
    if (container) {
      suggestions = container.getElementsByTagName("div");
    }

    if (keyboardEvent.keyCode == keyDownCode) {
      this.currentFocus++;
      this.addActiveCSSClass(suggestions);
    } else if (keyboardEvent.keyCode == keyUpCode) {
      this.currentFocus--;
      this.addActiveCSSClass(suggestions);
    } else if (keyboardEvent.keyCode == keyEnterCode) {
      if (this.currentFocus > -1 && suggestions) {
        suggestions[this.currentFocus].click();
      }
    }
  }

  /**
   * Remove the active CSS class from a list of elements.
   * param {} suggestions - The list of elements to remove the active CSS class from.
   */
  removeActiveCSSClass(suggestions) {
    for (let item of suggestions) {
      item.classList.remove(activeClass);
    }
  }

  /**
   * Add the active CSS class to an element.
   * param {} autoList - The element to add the active CSS class to.
   */
  addActiveCSSClass(suggestions) {
    if (!suggestions) {
      return false;
    }

    this.removeActiveCSSClass(suggestions);

    if (this.currentFocus >= suggestions.length) {
      this.currentFocus = 0;
    }

    if (this.currentFocus < 0) {
      this.currentFocus = suggestions.length - 1;
    }

    suggestions[this.currentFocus].classList.add(activeClass);
  }

  /**
   *
   * param {} element - The element to remove from the auto-complete items.
   */
  removeSuggestions(element) {
    const items = document.getElementsByClassName(itemsClass);
    for (let item of items) {
      if (element != item && element != this.searchBox) {
        item.parentNode.removeChild(item);
      }
    }
    this.currentFocus = -1;
  }

  /**
   * Create a suggestion element with `term`.
   * param {string} term - The term to use when creating the input.
   */
  createSuggestion(term) {
    let suggestion = document.createElement("div");
    suggestion.innerHTML = "<strong>" + term + "</strong>";
    suggestion.innerHTML += "<input type='hidden' value='" + term + "'>";

    suggestion.addEventListener("click", () => {
      const value = suggestion.getElementsByTagName("input")[0].value;
      this.searchBox.value = value;
      this.removeSuggestions();
      this.button.click();
    });

    return suggestion;
  }

  /**
   * Search the list of search terms by searchTerm.
   * param {string} searchTerm - The string to search for.
   */
  search(searchTerm) {
    this.removeSuggestions();

    if (!searchTerm || searchTerm.length < 3) {
      return false;
    }

    let container = document.createElement("div");
    container.setAttribute("id", this.id + containerID);
    container.setAttribute("class", itemsClass);
    this.searchBox.parentNode.appendChild(container);

    for (let term of this.terms) {
      let substring = term.substr(0, searchTerm.length);
      if (substring.toUpperCase() == searchTerm.toUpperCase()) {
        container.appendChild(this.createSuggestion(term));
      }
    }
  }
}

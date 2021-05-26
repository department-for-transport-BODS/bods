import { describeArc } from "./bods-maths";

const HEADERS = {
  "Cache-Control": "no-cache, no-store, must-revalidate",
  Pragma: "no-cache",
  Expires: "0"
};

const FETCH_CONF = {
  credentials: "same-origin",
  method: "get",
  mode: "cors",
  headers: HEADERS
};

class Dataset {
  TAB = "tab";
  ACTIVE = "active";
  STATUS_CSS = "status-indicator";
  LINK_CSS = "govuk-link";
  ERROR = { value: "error", title: "Error", css: this.STATUS_CSS + "--error" };
  INDEXING = { value: "indexing", title: "Processing", css: null };
  DRAFT = {
    value: "success",
    title: "Draft",
    css: this.STATUS_CSS + "--draft"
  };
  UNKNOWN = {
    value: "indexing",
    title: "Processing",
    css: this.STATUS_CSS + "--success"
  };
  current_url = new URL(window.location.href);

  constructor(progressCentreDiv) {
    this.progressCentreDiv = progressCentreDiv;
    this.parentDiv = progressCentreDiv.parentElement;
    this.datasetID = progressCentreDiv.firstElementChild.getAttribute("id");
    this._percentProgress = progressCentreDiv.getElementsByClassName(
      "progress-percent"
    )[0];
    this.interval = null;
    this.queryAPI();
    this._path = progressCentreDiv.getElementsByTagName("path")[0];
    this.interval = setInterval(() => this.queryAPI(), 10000);
  }

  get center() {
    const circle = this.progressCentreDiv.getElementsByTagName("circle")[0];
    return parseInt(circle.getAttribute("cx"));
  }

  get radius() {
    return this.center - parseInt(this._path.getAttribute("stroke-width")) / 2;
  }

  set percentage_text(value) {
    this._percentProgress.textContent = value + "%";
  }

  set percentage_path(value) {
    this._path.setAttribute("d", value);
  }

  queryAPI() {
    fetch(`/dataset/${this.datasetID}/progress/`, FETCH_CONF)
      .then(response => {
        if (!response.ok) {
          throw new Error(response.status);
        }
        return response.json();
      })
      .then(data => {
        if (data.status === this.INDEXING.value && data.progress < 100) {
          this.updatePercentage(data.progress);
        } else if (data.status === this.DRAFT.value) {
          this.toDraft();
        } else if (data.status === this.ERROR.value) {
          this.toError();
        } else {
          this.toUnknown();
        }
      })
      .catch(e => {
        console.error(`Cannot contact API, giving up: ${e}`);
        this.toUnknown();
      });
  }

  updatePercentage(value) {
    this.percentage_path = describeArc(
      this.center,
      this.center,
      this.radius,
      0,
      (360 / 100) * (value + 1)
    );
    this.percentage_text = value;
  }

  replaceIndicator(indicator) {
    const new_span = document.createElement("span");
    new_span.classList.add(this.STATUS_CSS, indicator.css);
    new_span.textContent = indicator.title;
    this.progressCentreDiv.replaceWith(new_span);
    const queryParam =
      this.current_url.searchParams.get(this.TAB) || this.ACTIVE;
    if (queryParam === this.ACTIVE) {
      // We only have a view link on the Active tab otherwise the dataset name
      // is the link.
      new_span.after(this.createViewLink());
    }
  }

  createViewLink() {
    const atag = document.createElement("a");
    atag.classList.add(this.LINK_CSS, "govuk-!-padding-left-1");
    atag.href = `${this.current_url.pathname}${this.datasetID}/update/review`;
    atag.textContent = "View";
    return atag;
  }

  toError() {
    this.replaceIndicator(this.ERROR);
    clearInterval(this.interval);
  }

  toUnknown() {
    this.replaceIndicator(this.UNKNOWN);
    clearInterval(this.interval);
  }

  toDraft() {
    this.replaceIndicator(this.DRAFT);
    clearInterval(this.interval);
  }
}

export function initDatasetListLoaders() {
  const spinners = document.getElementsByClassName("progress-centre");
  spinners.forEach(spinner => {
    new Dataset(spinner);
  });
}

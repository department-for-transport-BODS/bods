import AirDatepicker from 'air-datepicker'
import 'air-datepicker/air-datepicker.css'
import localeEn from 'air-datepicker/locale/en';

/**
 * Encodes the query parameters
 * @param {Object} data - Object of query params
 * 
 * @returns Query parameters in string 
 * 
 * @example encodeQueryParam({'param1': 'value1', 'param2': 'value2'} ) will return 'param1=value1&param2=value2'
 */
function encodeQueryParam(data) {
  return Object.keys(data)
    .map(function (key) {
      return [key, data[key]].map(encodeURIComponent).join("=");
    })
    .join("&");
}

/**
 *
 * @param {date} date Date to in the format of yyyy-MM-dd
 *
 * @returns Return the date in string format (yyyy-MM-dd)
 *
 * @example formatDate(new Date()) will return 2024-03-22
 */
function formatDate(date) {
  if (date !== null) {
    return (
      date.getFullYear() +
      "-" +
      ("0" + (date.getMonth() + 1)).slice(-2) +
      "-" +
      ("0" + date.getDate()).slice(-2)
    );
  }

  return formatDate(new Date());
}

/**
 *
 * Reloads the current page after adding/updating the query parameter in the query string
 *
 * @param {string} paramKey Key of the query parameter which will be added if not present in query string
 * @param {string} paramValue Value of the query parameter
 */
const reloadPageOnDate = (paramKey, paramValue) => {
  const urlParams = new URLSearchParams(window.location.search);
  urlParams.set(paramKey, paramValue);
  const newUrl =
    window.location.origin +
    window.location.pathname +
    "?" +
    encodeQueryParam(Object.fromEntries(urlParams));
  window.location.assign(newUrl);
};

/**
 * Exit Button to show on the date picker
 */
let exitButton = {
  content: "Exit",
  onClick: (dp) => {
    dp.hide();
  },
};

/**
 * Today button to show on the date picker
 */
let todayButton = {
  content: "Today",
  onClick: (dp) => {
    dp.update({
      selectedDates: [new Date()],
    });
  },
};

/**
 * Change the target date and apply filter to show timetable for selected date
 */
const changeTargetDate = (domId) => {
  const dpValue = document.getElementById(domId).value;
  const dpValuesArr = dpValue.split("/"); // format will be DD/MM/YYYY
  const dateRegex = /^(0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[012])\/(19|20)\d{2}$/;
  const isValid = dateRegex.test(dpValue);

  if (isValid & (dpValuesArr.length == 3)) {
    let day = dpValuesArr[0];
    let month = dpValuesArr[1];
    let year = dpValuesArr[2];
    let dt = new Date(year, month - 1, day);
    reloadPageOnDate("date", formatDate(dt));
  }
}

/**
 *
 * @param {string} domId ElementId in DOM in which the datepicker is to be initialized
 * @param {*} selectedDate Date to be selected in the calendar
 * @param {*} startDate Start date of the calendar to be enabled
 * @param {*} endDate Last date for the calendar to be enabled
 * @param {Array} disabledDays Array of the dates to be disabled in calendar
 *
 * initDatePicker("#date", null, "2024-03-23", "2025-03-22", ["2024-02-23", "2024-03-27","2024-04-29"])
 */
const initDatePicker = (
  domId,
  selectedDate,
  startDate,
  endDate,
  enabledDays = ""
) => {
  // If there is no selected date, default to today date
  if (selectedDate === null) {
    selectedDate = new Date();
  } else {
    selectedDate = new Date(selectedDate);
  }

  enabledDays = enabledDays.split(",");
  const dp = new AirDatepicker(domId, {
    locale: localeEn,
    dateFormat: "dd/MM/yyyy",
    selectedDates: [selectedDate],
    buttons: [exitButton, todayButton],
    // minDate: new Date(startDate),
    // maxDate: new Date(endDate),
    navTitles: {
      days: "MMMM yyyy",
      months: "yyyy",
      years: "yyyy1 - yyyy2",
    },
    // Hiding the datepicker instance on selecting date
    onSelect({ date, formattedDate, datepicker }) {
      datepicker.hide();
    },
    // Trigger when the calendar is shown
    onRenderCell: function onRenderCell({ date, cellType }) {
      // If calendar type is viewing days
      if (cellType === "day") {
        let isDisabled = false;
        let day = formatDate(date);

        // enabled the days, if empty array is found, enable for all days
        if (enabledDays.length != 0) {
          isDisabled = enabledDays.indexOf(day) > -1;
        }

        return {
          disabled: isDisabled,
        };
      }
    },
  });
};

export { initDatePicker, changeTargetDate };

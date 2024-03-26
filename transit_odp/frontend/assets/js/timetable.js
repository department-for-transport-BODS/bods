const flatpickr = require("flatpickr").default;
//import flatpickr from "flatpickr";
import AirDatepicker from 'air-datepicker'
import 'air-datepicker/air-datepicker.css'
import localeEn from 'air-datepicker/locale/en';

function encodeQueryParam(data) {
  return Object.keys(data).map(function(key) {
      console.log(key)
      return [key, data[key]].map(encodeURIComponent).join("=");
  }).join("&");
}

const reloadPageOnDate = (query_param_date, dateVal) => {

  const urlParams = new URLSearchParams(window.location.search);
  urlParams.set(query_param_date, dateVal);  
  const newUrl = window.location.origin + window.location.pathname + "?"+ encodeQueryParam(Object.fromEntries(urlParams));
  window.location.assign(newUrl);
};

// Check if disabled date is in the range
const isDisabledDateIsInRange = ({date, datepicker}) => {
    const selectedDate = datepicker.selectedDates[0];
    if (date.getDate() === 29) {
      console.log("Disabling isDisabledDateIsInRange date: ", date);
      return true;
    }

    if (selectedDate && datepicker.selectedDates.length === 1) {

        const sortedDates = [selectedDate, date].toSorted((a, b) => {
            if (a.getTime() > b.getTime()) {
                return 1;
            }
            return -1;
        })

        return true;
    }

    

    // if (date.getDate() === 29) {
    //   console.log("Disabling date: ", date);
    //     return {
    //         disabled: true,
    //         classes: 'disabled-class',
    //         attrs: {
    //             title: 'Cell is disabled'
    //         }
    //     }
    // }
}

const initDatePicker = (domId, selectedDate, startDate, endDate) => {
  console.log("Calling datepicker");
  console.log("Selected: ", selectedDate, startDate, endDate);
  if (selectedDate === null) {
    selectedDate = new Date();
    console.log("Selecting date");
  }
  const disabledDays = ['2024-02-23','2024-03-27','2024-04-29'];
  new AirDatepicker(domId, {
    locale: localeEn,
    dateFormat: "dd/MM/yyyy",
    selectedDates: [new Date(selectedDate)],
    onSelect: ({date, formattedDate, datepicker}) => {
      console.log(date);
    },
    onRenderCell: function onRenderCell(value) {
      const date = value["date"];
      const cellType = value["cellType"];
      //console.log("date: ", dt);
      //console.log("cellType: ", cellType);
      
      if (cellType === 'day' ) {
        //console.log("Disabling the date: ", dt.getDate());
        let isDisabled = false;
        // if (dt.getDate() == 29) {
        //   disabled = true;
        //   console.log("Disabling the date: 29, ", disabled);
        // }
         let day = (date.getFullYear()+'-'+(('0' + (date.getMonth()+1)).slice(-2))+'-'+(('0' + date.getDate()).slice(-2)));
         console.log(day);
         isDisabled = disabledDays.indexOf(day) > -1;
         return {
            disabled: isDisabled
         }
      }
   },
  //   onBeforeSelect: ({date, datepicker}) => {
  //     // Dont allow user to select date, if disabled date is in the range
  //     return false;
  //   },
  //   onFocus: ({date, datepicker}) => {
  //     if (isDisabledDateIsInRange({date, datepicker}) ) {
  //        datepicker.$datepicker.classList.add('-disabled-range-')
  //     } else {
  //        datepicker.$datepicker.classList.remove('-disabled-range-')
  //     }
  // },
  //   onRenderCell({date, cellType}) {
  //     console.log("checking date: ", date);
  //     return {
  //       html: "m2",
  //       disabled: true,
  //       classes: 'disabled-class',
  //       attrs: {
  //           title: 'Cell is disabled'
  //       }
  //   }
  //     // Disable all 12th dates in month
  //     //console.log("checking date: ", date)
      
  // }
    //selectedDates: ['27/03/2024', '29/03/2024']    
  });
  //flatpickr(domId, {});
  // flatpickr(domId, {
  //   defaultDate: selectedDate,
  //   minDate: startDate,
  //   maxDate: endDate,
  //   // return true to disable
  //   "disable": [function(date) {
  //     console.log(date);
  //       return (date.getDay() === 0 || date.getDay() === 6);
  //   }]
  // });
};

export { initDatePicker, reloadPageOnDate };

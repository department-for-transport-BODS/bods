const getFilterScopeStatus = () => {
    var scopeStatusList = []    
    if ($('input[name="scope_details"]:checked').length > 0) {
        $('input[name="scope_details"]:checked').each(function() {
            scopeStatusList.push($(this).val())
        });
    } else {
        scopeStatusList = ['service-in-scope', 'service-out-of-scope']   
    }
    return scopeStatusList
}

const getFilterSeasonStatus = () => {
    var seasonStatusList = []    
    if ($('input[name="season_details"]:checked').length > 0) {
        $('input[name="season_details"]:checked').each(function() {
            seasonStatusList.push($(this).val())
        });
    } else {
        seasonStatusList = ['service-in-season', 'service-out-of-season']   
    }
    return seasonStatusList
}

const getFilterLtas = () => {
    var ltasList = []    
    if ($('input[name="lta_details"]:checked').length > 0) {
        $('input[name="lta_details"]:checked').each(function() {
            ltasList.push($(this).val())
        });
    } 
    return ltasList
}

const getFilterFranchise = () => {
    var list = []    
    if ($('input[name="franchise_detailse"]:checked').length > 0) {
        $('input[name="franchise_detailse"]:checked').each(function() {
            list.push(parseInt($(this).val()))
        });
    } 
    return list
}

const getFilterOperator = () => {
    var list = []    
    if ($('input[name="operator_details"]:checked').length > 0) {
        $('input[name="operator_details"]:checked').each(function() {
            list.push(parseInt($(this).val()))
        });
    } 
    return list
}


export function refreshLicencesList() {
  const filterScopeStatus = getFilterScopeStatus();
  const filterSeasonStatus = getFilterSeasonStatus();
  const filterLtaList = getFilterLtas();
  const filterFranchise = getFilterFranchise();
  const filterOperator = getFilterOperator();

  $(".licence-details-service-row").each(function() {
    const scopeStatus = $(this).data("scope-status");
    const seasonStatus = $(this).data("season-status");
    const operator = $(this).data("operator");
    const ltasData = $(this).attr("data-local-authority") || "";
    
    var ltasList = []
    if (typeof ltasData === 'string' && ltasData.trim() !== '') {
        ltasList = ltasData.split(",").map(lta => lta.trim());
    }

    if (filterScopeStatus.includes(scopeStatus) && filterSeasonStatus.includes(seasonStatus) && (filterLtaList.length == 0 || ltasList.some(lta => filterLtaList.includes(lta))) && ((filterOperator.length == 0 && filterFranchise.length == 0) || filterOperator.includes(operator) || filterFranchise.includes(operator))) {
       if($(this).hasClass("js-hidden")) {
            $(this).removeClass("js-hidden");
       }
    } else {
        if(!$(this).hasClass("js-hidden")) {
            $(this).addClass("js-hidden");
       }
    }
  });
}

var sortDirections = {
    0: true
};

export function sortLicenceServicesTable(elem) {
    const $table = $("#licence-services-table");
    const $tbody = $table.find("tbody");
    const colIndex = elem.index();
    const $rows = $tbody.find('tr').get();
    sortDirections[colIndex] = !sortDirections[colIndex];
    const ascending = sortDirections[colIndex];
    $rows.sort(function(a, b) {
        const aCell = $(a).children('td').eq(colIndex);
        const bCell = $(b).children('td').eq(colIndex);

        const getValue = ($cell) => {
            const $find = $cell.find(".sra-dot");

            if ($($find).hasClass('sra-dot-green')) return 0;
            if ($($find).hasClass("sra-dot-red")) return 1;

            const text = $cell.text().trim().toLowerCase();
            return isNaN(text) ? text: parseFloat(text);
        }

        const aVal = getValue(aCell);
        const bVal = getValue(bCell);

        if (aVal < bVal) return ascending ? -1: 1;
        if (aVal > bVal) return ascending ? 1: -1;
        return 0
    });

    $table.find("th").removeClass('sorted').find(".sort-icon").remove();

    elem.addClass("sorted");
    const iconClass = ascending ? 'fa-sort-asc': 'fa-sort-desc';
    elem.append(`<i class="fa ${iconClass} sort-icon"></i>`);
    $.each($rows, (_, row) => $tbody.append(row));
}
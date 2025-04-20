export function addRow(tableId) {
    // console.log("addRow:"+tableId);
    const table = document.getElementById(tableId)?.querySelector("tbody");
    if (!table) return;
  
    const columnCount = table.parentElement.querySelectorAll("thead th").length;
    const row = document.createElement("tr");

    const forecastSetNameInput = document.querySelector("[name='forecast_set_name']");
    const forecastNameInput = document.querySelector("[name='forecast_name']");
    const startDateInput = document.querySelector("[name='start_date']");
    const endDateInput = document.querySelector("[name='end_date']");
    const approximateCheckbox = document.querySelector("[name='approximate']");

    let formValues = []; // declare outside
    if (tableId == "run-parameters-table") {
      formValues = [
        startDateInput?.value || "",
        endDateInput?.value || "",
        forecastNameInput?.value || "",
        approximateCheckbox?.checked ? "Yes" : "No"
      ];
    }
    

  
    for (let i = 0; i < columnCount; i++) {
      const cell = document.createElement("td");
      const input = document.createElement("input");
      input.type = "text";
      input.placeholder = "...";

      // i am not sure what needs to go here
      // ✨ Set the default value based on formValues
      if (formValues[i] !== undefined) {
        input.value = formValues[i];
      }

      cell.appendChild(input);
      row.appendChild(cell);
    }
  
    table.appendChild(row);
  }
  
  export function extractTableData(tableId) {
    const rows = document.querySelectorAll(`#${tableId} tbody tr`);

    // console.log(tableId);
    var fieldNames = [];
    if (tableId == 'run-parameters-table'){
       fieldNames = ["start_date", "end_date", "forecast_name", "approximate"];
    } else if (tableId == 'accounts-table'){
       fieldNames = ["name", "min_balance", "max_balance", "type",
        "billing_start_date", "interest_type", "apr", "interest_cadence",
      "minimum_payment", "primary_checking_ind"];
    } else if (tableId == 'lienitems-table'){
       fieldNames = ["name", "amount", "priority", "choice_index",
        "interest_cadence", "start_date", "end_date", "deferrable",
      "partial_payment_allowed"];
    } else if (tableId == 'decisionrules-table'){
       fieldNames = ["memo_regex","priority","account_from","account_to"];
    } else if (tableId == 'milestones-table'){
       fieldNames = ["name","type","field_1","field_2"];
    } else {
      console.log('failed to match table id to field names');
      console.log(tableId);
    }
    // console.log(fieldNames);
    
  
    return Array.from(rows).map(row => {
      const cells = row.querySelectorAll('td');
      const data = {};
  
      Array.from(cells).forEach((cell, index) => {
        const input = cell.querySelector('input, select');
        data[fieldNames[index]] = input?.value ?? null;
      });
  
      return data;
    });
  }
  
  
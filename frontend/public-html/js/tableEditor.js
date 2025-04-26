const getRadioInput = (name) => {
  console.log('getRadioInput(' + name + ')');
  const checkedRadio = document.querySelector(`input[type="radio"][name="${name}"]:checked`);
  return checkedRadio ? checkedRadio.value : null;
};

const getInput = (name) => document.querySelector(`[name='${name}']`)?.value || "";
const getCheck = (name) => document.querySelector(`[name='${name}']`)?.checked || false;

function parseOptionalFloat(id) {
  const val = getInput(id);
  return val === "" ? null : parseFloat(val);
}


export function addRow(tableId) {
  switch (tableId) {
    case "run-parameters-table":
      // console.log("start_date:");
      // console.log(getInput("start_date"));
      // console.log(new Date(getInput("start_date")));
      const startDate = new Date(getInput("start_date"));
      const endDate = new Date(getInput("end_date"));
      // console.log("🚨 Adding row to runParametersTable:", {
      //   start_date: startDate,
      //   end_date: endDate,
      //   forecast_name: getInput("forecast_name"),
      //   approximate: getCheck("approximate"),
      // });
      window.runParametersTable.addRow({
        start_date: new Date(getInput("start_date")),
        end_date: new Date(getInput("end_date")),
        forecast_name: getInput("forecast_name"),
        approximate: getCheck("approximate"),
      });
      break;

    case "accounts-table":
      console.log('accounts table new row');
      console.log({
        account_name: getInput("account_name"),
        account_type: getRadioInput("account_type"),
        interest_type: getRadioInput("interest_type") || null,
        interest_cadence: getRadioInput("interest_cadence") || null,
        balance: parseFloat(getInput("balance")) || 0,
        min_balance: parseOptionalFloat("min_balance"),
        max_balance: parseOptionalFloat("max_balance"),
        prev_cycle_balance: parseOptionalFloat("prev_cycle_balance"),
        apr: parseOptionalFloat("apr"),
        minimum_payment: parseOptionalFloat("minimum_payment"),
        billing_start_date: getInput("billing_start_date") || null,
        primary_checking: getCheck("primary_checking"),
      });
      window.accountsTable.addRow({
        account_name: getInput("account_name"),
        account_type: getRadioInput("account_type"),
        interest_type: getRadioInput("interest_type") || null,
        interest_cadence: getRadioInput("interest_cadence") || null,
        balance: parseFloat(getInput("balance")) || 0,
        min_balance: parseOptionalFloat("min_balance"),
        max_balance: parseOptionalFloat("max_balance"),
        prev_cycle_balance: parseOptionalFloat("prev_cycle_balance"),
        apr: parseOptionalFloat("apr"),
        minimum_payment: parseOptionalFloat("minimum_payment"),
        billing_start_date: getInput("billing_start_date") || null,
        primary_checking: getCheck("primary_checking"),
      });
      break;

    case "lineitems-table":
      window.lineItemsTable.addRow({
        name: getInput("line_item_name"),
        amount: getInput("amount"),
        priority: getInput("priority"),
        choice_index: getInput("choice"),
        cadence: getInput("cadence"),
        start: getInput("li_start_date"),
        end: getInput("li_end_date"),
        deferrable: getCheck("deferrable"),
        partial: getCheck("partial_allowed"),
      });
      break;

    case "decisionrules-table":
      window.decisionRulesTable.addRow({
        memo_regex: getInput("memo_regex"),
        priority: getInput("rule_priority"),
        account_from: getInput("account_from"),
        account_to: getInput("account_to"),
      });
      break;

    case "milestones-table":
      window.milestonesTable.addRow({
        name: getInput("milestone_name"),
        type: getInput("milestone_account"),
        field_1: getInput("milestone_min"),
        field_2: getInput("milestone_max"),
        memo: getInput("milestone_memo"),
        account_names: getInput("account_milestone_names"),
        memo_name: getInput("memo_milestone_name"),
      });
      break;

    default:
      console.warn(`Unknown tableId: ${tableId}`);
  }
}


  
// export function extractTableData(tableId) {
//   console.log('ENTER extractTableData');
//   const rows = document.querySelectorAll(`#${tableId} tbody tr`);

  
//   var fieldNames = [];
//   if (tableId == 'run-parameters-table'){
//       fieldNames = ["start_date", "end_date", "forecast_name", "approximate"];
//   } else if (tableId == 'accounts-table'){
//       fieldNames = ["name", "min_balance", "max_balance", "type",
//       "billing_start_date", "interest_type", "apr", "interest_cadence",
//     "minimum_payment", "primary_checking_ind"];
//   } else if (tableId == 'lienitems-table'){
//       fieldNames = ["name", "amount", "priority", "choice_index",
//       "interest_cadence", "start_date", "end_date", "deferrable",
//     "partial_payment_allowed"];
//   } else if (tableId == 'decisionrules-table'){
//       fieldNames = ["memo_regex","priority","account_from","account_to"];
//   } else if (tableId == 'milestones-table'){
//       fieldNames = ["name","type","field_1","field_2"];
//   } else {
//     console.log('failed to match table id to field names');
//     console.log(tableId);
//   }
//   // console.log(fieldNames);
  
//   let rv = Array.from(rows).map(row => {
//     const cells = row.querySelectorAll('td');
//     const data = {};

//     Array.from(cells).forEach((cell, index) => {
//       const input = cell.querySelector('input, select');
//       data[fieldNames[index]] = input?.value ?? null;
//     });

//     return data;
//   });
//   console.log(tableId + ' table data:');
//   console.log(rv);

//   return rv;
// }
  
export function extractTableData(tableId) {
  console.log("ENTER extractTableData:", tableId);

  // Reference the global Tabulator instance
  const tableMap = {
    "run-parameters-table": window.runParametersTable,
    "accounts-table": window.accountsTable,
    "lineitems-table": window.lineItemsTable,
    "decisionrules-table": window.decisionRulesTable,
    "milestones-table": window.milestonesTable,
  };

  const table = tableMap[tableId];

  if (!table) {
    console.error("No Tabulator instance found for table ID:", tableId);
    return [];
  }

  const data = table.getData(); // ← Tabulator's clean way to get all current row data

  // console.log(`${tableId} table data:`);
  console.log(data);

  return data;
}


export function populateTable(tableId, data) {
  console.log("ENTER populateTable:", tableId);
  console.log("Data:", data);

  const tableMap = {
    "run-parameters-table": window.runParametersTable,
    "accounts-table": window.accountsTable,
    "lineitems-table": window.lineItemsTable,
    "decisionrules-table": window.decisionRulesTable,
    "milestones-table": window.milestonesTable,
  };

  const table = tableMap[tableId];

  if (!table) {
    console.warn("⚠️ No Tabulator instance found for", tableId);
    return;
  }

  table.replaceData(data || []);
}

  
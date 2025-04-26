import { showTab } from "./tabs.js";
import { addRow } from "./tableEditor.js";
import { submitDraftData } from "./draftSubmit.js";
import { saveDraftData } from "./draftSubmit.js";
import { fetchAndUpdateChart } from "./chart.js";
import { loadSavedDraft } from "./draftSubmit.js";




// import { setupDraftRunParameterTable } from "./forecastTable.js";
// import { setupDraftAccountTable } from "./forecastTable.js";
// import { setupDraftLineItemTable } from "./forecastTable.js";
// import { setupDraftDecisionRuleTable } from "./forecastTable.js";
// import { setupDraftMilestoneTable } from "./forecastTable.js";

import { setupBrowseForecastTable } from "./forecastTable.js";
import { setupViewForecastTable } from "./forecastTable.js";
import { setupLineItemViewTable } from "./forecastTable.js";
import { setupMilestoneResultViewTable } from "./forecastTable.js";

import { drawSankey } from "./forecastTable.js";

// setupDraftRunParameterTable();
// setupDraftAccountTable();
// setupDraftLineItemTable();
// setupDraftDecisionRuleTable();
// setupDraftMilestoneTable();

setupBrowseForecastTable();
setupViewForecastTable();
setupLineItemViewTable();
setupMilestoneResultViewTable();


//todo move this code somewhere else
document.getElementById("submit-draft-button")?.addEventListener("click", submitDraftData);
document.getElementById("save-draft-button")?.addEventListener("click", saveDraftData);

document.getElementById("add-row-run-parameters-table")?.addEventListener("click", () => addRow('run-parameters-table'));
document.getElementById("add-row-accounts-table")?.addEventListener("click", () => addRow('accounts-table'));
document.getElementById("add-row-lineitems-table")?.addEventListener("click", () => addRow('lineitems-table'));
document.getElementById("add-row-decisionrules-table")?.addEventListener("click", () => addRow('decisionrules-table'));
document.getElementById("add-row-milestones-table")?.addEventListener("click", () => addRow('milestones-table'));

drawSankey();

// add event listeners to navbar
document.getElementById("draft-button").addEventListener("click", () => {
    showTab("draft");
});
document.getElementById("browse-button").addEventListener("click", () => {
    showTab("browse");
});
document.getElementById("view-button").addEventListener("click", () => {
    showTab("view");
});

window["runParametersTable"] = new Tabulator("#run-parameters-table", {
    debug: true,
    layout: "fitColumns",
    columns: [
      { title: "Start Date", field: "start_date", formatter: function (cell) {
    const rawValue = cell.getValue();
    const rowData = cell.getRow().getData();
    // console.log("🔍 Formatter called for Start Date");
    // console.log("Raw value:", rawValue);
    // console.log("Row data:", rowData);
    // console.log("Type of raw value:", typeof rawValue);
    
    try {
      const date = new Date(rawValue);
      // console.log("Parsed date:", date, "Is valid?", !isNaN(date));
      return !isNaN(date) ? date.toISOString().slice(0, 10) : "(invalid)";
    } catch (err) {
      console.error("Date parse error:", err);
      return "(error)";
    }
  }, 
        
        formatterParams: { outputFormat: "YYYY-MM-DD" } },
        { title: "End Date", field: "end_date", formatter: function (cell) {
          const rawValue = cell.getValue();
          const rowData = cell.getRow().getData();
          // console.log("🔍 Formatter called for End Date");
          // console.log("Raw value:", rawValue);
          // console.log("Row data:", rowData);
          // console.log("Type of raw value:", typeof rawValue);
          
          try {
            const date = new Date(rawValue);
            // console.log("Parsed date:", date, "Is valid?", !isNaN(date));
            return !isNaN(date) ? date.toISOString().slice(0, 10) : "(invalid)";
          } catch (err) {
            console.error("Date parse error:", err);
            return "(error)";
          }
        }, 
        
        
        formatterParams: { outputFormat: "YYYY-MM-DD" } },
      { title: "Name", field: "forecast_name" },
      { title: "Approx.", field: "approximate"},
      { 
        title: "", 
        formatter: "buttonCross", 
        width: 40, 
        hozAlign: "center", 
        cellClick: function (e, cell) {
          cell.getRow().delete();
        } 
      }
    ],
    data: [],
  });
  
window["accountsTable"] = new Tabulator("#accounts-table", {
    layout: "fitColumns",
    columns: [
      { title: "Name", field: "name" },
      { title: "Balance", field: "balance", formatter: "money" },
      { title: "Min", field: "min", formatter: "money" },
      { title: "Max", field: "max", formatter: "money" },
      { title: "Type", field: "type" },
      { title: "Billing Date", field: "billing_date" },
      { title: "Interest Type", field: "interest_type" },
      { title: "APR", field: "apr", formatter: "money" },
      { title: "Cadence", field: "cadence" },
      { title: "Min Pay", field: "min_pay", formatter: "money" },
      { title: "Primary", field: "primary" },
      { 
        title: "", 
        formatter: "buttonCross", 
        width: 40, 
        hozAlign: "center", 
        cellClick: function (e, cell) {
          cell.getRow().delete();
        } 
      }
    ],
    data: [],
  });

window["lineItemsTable"] = new Tabulator("#lineitems-table", {
layout: "fitColumns",
columns: [
    { title: "Name", field: "name" },
    { title: "Amount", field: "amount", formatter: "money" },
    { title: "Priority", field: "priority" },
    { title: "Choice Index", field: "choice_index" },
    { title: "Cadence", field: "cadence" },
    { title: "Start", field: "start" },
    { title: "End", field: "end" },
    { title: "Deferrable", field: "deferrable" },
    { title: "Partial", field: "partial" },
    { 
      title: "", 
      formatter: "buttonCross", 
      width: 40, 
      hozAlign: "center", 
      cellClick: function (e, cell) {
        cell.getRow().delete();
      } 
    }
],
data: [],
});


window["decisionRulesTable"] = new Tabulator("#decisionrules-table", {
layout: "fitColumns",
columns: [
    { title: "Memo Regex", field: "memo_regex" },
    { title: "Priority", field: "priority" },
    { title: "Account From", field: "account_from" },
    { title: "Account To", field: "account_to" },
    { 
      title: "", 
      formatter: "buttonCross", 
      width: 40, 
      hozAlign: "center", 
      cellClick: function (e, cell) {
        cell.getRow().delete();
      } 
    }
],
data: [],
});


window["milestonesTable"] = new Tabulator("#milestones-table", {
layout: "fitColumns",
columns: [
    { title: "Name", field: "name" },
    { title: "Type", field: "type" },
    { title: "Field 1", field: "field_1" },
    { title: "Field 2", field: "field_2" },
    { 
      title: "", 
      formatter: "buttonCross", 
      width: 40, 
      hozAlign: "center", 
      cellClick: function (e, cell) {
        cell.getRow().delete();
      } 
    }
],
data: [],
});




window.addEventListener("load", async () => {

  // Kick off polling
  setInterval(fetchAndUpdateChart, 50000);
  fetchAndUpdateChart();
  loadSavedDraft(); 
});

  


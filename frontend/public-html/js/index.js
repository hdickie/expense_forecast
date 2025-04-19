import { showTab } from "./tabs.js";
import { addRow } from "./tableEditor.js";
import { submitDraftData } from "./draftSubmit.js";
import { fetchAndUpdateChart } from "./chart.js";
// import { setupForecastTable } from "./forecastTable.js";
import { setupViewForecastTable, setupBrowseForecastTable } from "./forecastTable.js";
import { setupLineItemViewTable } from "./forecastTable.js";
import { setupMilestoneResultViewTable } from "./forecastTable.js";

import { drawSankey } from "./forecastTable.js";

// setupForecastTable(tableData);
setupBrowseForecastTable();

setupViewForecastTable();
setupLineItemViewTable();
setupMilestoneResultViewTable();

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


document.getElementById("submit-draft-button")?.addEventListener("click", submitDraftData);
document.getElementById("add-row-run-parameters-table")?.addEventListener("click", () => addRow('parameters-table'));
document.getElementById("add-row-accounts-table")?.addEventListener("click", () => addRow('accounts-table'));
document.getElementById("add-row-lineitems-table")?.addEventListener("click", () => addRow('lineitems-table'));
document.getElementById("add-row-decisionrules-table")?.addEventListener("click", () => addRow('decisionrules-table'));
document.getElementById("add-row-milestones-table")?.addEventListener("click", () => addRow('milestones-table'));


window.addEventListener("load", () => {
    // Kick off polling
    setInterval(fetchAndUpdateChart, 50000);
    fetchAndUpdateChart();
});

  


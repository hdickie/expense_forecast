import { showTab } from "./tabs.js";
import { addRow } from "./tableEditor.js";
import { submitDraftData } from "./draftSubmit.js";
import { fetchAndUpdateChart } from "./chart.js";

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

window.addEventListener("load", () => {
    // Kick off polling
    setInterval(fetchAndUpdateChart, 50000);
    fetchAndUpdateChart();
});

  


import { extractTableData } from "./tableEditor.js";

export async function submitDraftData() {
  const activeTab = document.querySelector('.tab-content.active');
  if (!activeTab || activeTab.id !== 'draft') {
    alert("You can only submit while the DRAFT tab is active.");
    return;
  }

  const payload = {
    parameters: extractTableData("parameters-table"),
    accounts: extractTableData("accounts-table"),
    line_items: extractTableData("lineitems-table"),
    decision_rules: extractTableData("decisionrules-table"),
    milestones: extractTableData("milestones-table"),
  };

  try {
    const response = await fetch("http://api.localhost/draft/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      credentials: "include"
    });

    alert(response.ok ? "Draft submitted successfully!" : "Failed to submit draft.");
  } catch (error) {
    console.error("Submission error:", error);
    alert("Submission failed due to a network error.");
  }
}

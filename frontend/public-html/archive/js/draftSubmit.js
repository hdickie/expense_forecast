import { extractTableData } from "./tableEditor.js";

function getQueryParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}

function showLoadingSpinner() {
  let spinner = document.getElementById('loading-spinner');
  if (!spinner) {
    spinner = document.createElement('div');
    spinner.id = 'loading-spinner';
    spinner.style.position = 'fixed';
    spinner.style.top = '50%';
    spinner.style.left = '50%';
    spinner.style.transform = 'translate(-50%, -50%)';
    spinner.style.border = '16px solid #f3f3f3';
    spinner.style.borderTop = '16px solid #3498db';
    spinner.style.borderRadius = '50%';
    spinner.style.width = '120px';
    spinner.style.height = '120px';
    spinner.style.animation = 'spin 2s linear infinite';
    document.body.appendChild(spinner);

    const style = document.createElement('style');
    style.innerHTML = `
      @keyframes spin {
        0% { transform: translate(-50%, -50%) rotate(0deg); }
        100% { transform: translate(-50%, -50%) rotate(360deg); }
      }
    `;
    document.head.appendChild(style);
  }
  spinner.style.display = 'block';
}

function hideLoadingSpinner() {
  const spinner = document.getElementById('loading-spinner');
  if (spinner) {
    spinner.style.display = 'none';
  }
}



export async function submitDraftData() {
  const activeTab = document.querySelector('.tab-content.active');
  if (!activeTab || activeTab.id !== 'draft') {
    alert("You can only submit while the DRAFT tab is active.");
    return;
  }

  const payload = {
    parameters: extractTableData("run-parameters-table"),
    accounts: extractTableData("accounts-table"),
    line_items: extractTableData("lineitems-table"),
    decision_rules: extractTableData("decisionrules-table"),
    milestones: extractTableData("milestones-table"),
  };

  try {
    console.log("Payload:");
    console.log(JSON.stringify(payload));

    // Show loading spinner
    showLoadingSpinner();

    const response = await fetch("http://api.localhost/draft/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      credentials: "include"
    });

    if (!response.ok) {
      hideLoadingSpinner();
      const errorData = await response.json();
      console.error("Submission failed!", errorData);
      alert("Failed to submit draft.");
      return;
    }

    const data = await response.json();
    const taskId = data.task_id;

    console.log("Task started with ID:", taskId);

    // Now open a WebSocket connection to listen for completion
    const ws = new WebSocket(`ws://api.localhost/ws/task_status/${taskId}`);

    ws.onopen = () => {
      console.log("WebSocket connection established for task monitoring.");
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      console.log("WebSocket message:", message);

      hideLoadingSpinner();

      if (message.status === "success") {
        alert("Draft submitted successfully!");
      } else if (message.status === "failure") {
        alert(`Error submitting draft: ${message.error}`);
      } else {
        alert(`Unknown task status: ${message.status}`);
      }

      ws.close();
    };

    ws.onerror = (error) => {
      hideLoadingSpinner();
      console.error("WebSocket error:", error);
      alert("An error occurred while monitoring draft submission.");
    };

    ws.onclose = () => {
      console.log("WebSocket connection closed.");
    };

  } catch (error) {
    hideLoadingSpinner();
    console.error("Submission error:", error);
    alert("Submission failed due to a network error.");
  }
}


export async function saveDraftData() {
  const activeTab = document.querySelector('.tab-content.active');
  if (!activeTab || activeTab.id !== 'draft') {
    alert("You can only submit while the DRAFT tab is active.");
    return;
  }

  const payload = {
    parameters: extractTableData("run-parameters-table"),
    accounts: extractTableData("accounts-table"),
    line_items: extractTableData("lineitems-table"),
    decision_rules: extractTableData("decisionrules-table"),
    milestones: extractTableData("milestones-table"),
  };

  try {
    console.log("Payload:");
    console.log(JSON.stringify(payload));

    const user = getQueryParam("user");
    const url = user
      ? `http://api.localhost/draft/save?user=${encodeURIComponent(user)}`
      : `http://api.localhost/draft/save`;

    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      credentials: "include"
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error("Save failed!", errorData);
    } else {
      const data = await response.json();
      console.log("Save succeeded!", data);
    }

    alert(response.ok ? "Draft saved successfully!" : "Failed to save draft.");
  } catch (error) {
    console.error("Submission error:", error);
    alert("Submission failed due to a network error.");
  }
}

import { populateTable } from "./tableEditor.js";
export async function loadSavedDraft() {
  const user = new URLSearchParams(window.location.search).get("user");
  if (!user) {
    console.warn("No user provided. Skipping draft load.");
    return;
  }

  try {
    const response = await fetch(`http://api.localhost/draft/load?user=${encodeURIComponent(user)}`, {
      method: "GET",
      credentials: "include"
    });

    if (!response.ok) {
      console.warn("No saved draft or error retrieving draft.");
      return;
    }

    const draft_raw = await response.json();
    const draft = JSON.parse(draft_raw);
    console.log("Loaded draft:", draft);

    // Now populate tables with this draft
    populateTable("accounts-table", draft.accounts);
    populateTable("lineitems-table", draft.line_items);
    populateTable("run-parameters-table", draft.parameters);
    populateTable("decisionrules-table", draft.decision_rules);
    populateTable("milestones-table", draft.milestones);
  } catch (error) {
    console.error("Error loading draft:", error);
  }
}

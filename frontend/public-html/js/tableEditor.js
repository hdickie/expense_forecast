export function addRow(tableId) {
    const table = document.getElementById(tableId)?.querySelector("tbody");
    if (!table) return;
  
    const columnCount = table.parentElement.querySelectorAll("thead th").length;
    const row = document.createElement("tr");
  
    for (let i = 0; i < columnCount; i++) {
      const cell = document.createElement("td");
      const input = document.createElement("input");
      input.type = "text";
      input.placeholder = "...";
      cell.appendChild(input);
      row.appendChild(cell);
    }
  
    table.appendChild(row);
  }
  
  export function extractTableData(tableId) {
    const rows = document.querySelectorAll(`#${tableId} tbody tr`);
    return Array.from(rows).map(row => {
      const cells = row.querySelectorAll('td');
      return Array.from(cells).map(cell => {
        const input = cell.querySelector('input, select');
        return input?.value ?? null;
      });
    });
  }
  
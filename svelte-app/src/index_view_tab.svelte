<script>
  // even an empty script tag is fine
</script>
<div id="view" class="tab-content">
    <div id="filter-panel" style="padding: 1rem; border: 1px solid #ccc; width: 300px;">
        <h3>Filter Forecasts</h3>
        
        <div id="date-filters">
          <label for="start-date">Start Date:</label>
          <input type="date" id="start-date">

          <label for="end-date">End Date:</label>
          <input type="date" id="end-date">
                  </div>
      
        <div id="account-filters">
          <p>Accounts:</p><br>
          <!-- Dynamically insert checkboxes here -->
        </div>
      
        <button id="apply-filters-button">Apply Filters</button>
      </div>      
<svg id="line-chart" width="800" height="400"></svg>
<div id="sankey"></div>

<div id="export-panel" style="padding: 1rem; border: 1px solid #ccc; margin-bottom: 1rem;">
  <h3>Export Report</h3>
  <button id="export-csv">Download CSV</button>
  <button id="export-excel">Download EXCEL</button>
  <button id="export-json">Download JSON</button>
  <button id="export-pdf">Download PDF</button>
  <button id="export-html">Download Interactive HTML</button>
  <div style="margin-bottom: 1rem;">
    <input type="checkbox" id="apply-filters-checkbox" name="apply-filters">
    <label for="apply-filters-checkbox">Apply Filters</label>
  </div>
  
</div>


<h3>Milestone Results</h3>
<input id="milestone-result-view-table-search" type="text" placeholder="Search forecast..." style="margin-bottom: 10px; width: 100%;" />
<div id="milestone-result-view-table"></div>

<h3>Line Items</h3>
<input id="lineitem-view-table-search" type="text" placeholder="Search forecast..." style="margin-bottom: 10px; width: 100%;" />
<div id="lineitem-view-table"></div>

<h3>Raw Data</h3>
<input id="forecast-view-table-search" type="text" placeholder="Search forecast..." style="margin-bottom: 10px; width: 100%;" />
<div id="forecast-view-table"></div>
</div>
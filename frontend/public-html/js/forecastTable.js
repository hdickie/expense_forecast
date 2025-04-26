export async function setupBrowseForecastTable() {

  try {
    const response = await fetch("http://api.localhost/browse/data");
    const data = await response.json();
      
    const forecastTable = new Tabulator("#browse-table", {
      data,
      layout: "fitColumns",
      placeholder: "No forecasts yet",
      rowMouseEnter: function(e, row){
        const id = row.getData().id;
        d3.select(`[data-id='${id}']`).classed("highlighted", true);
      },
      rowMouseLeave: function(e, row){
          const id = row.getData().id;
          d3.select(`[data-id='${id}']`).classed("highlighted", false);
      },
      columnDefaults:{
        tooltip: function(e, cell, onRendered) {
          const rowData = cell.getRow().getData();
        
          const el = document.createElement("div");
          el.style.backgroundColor = "white";
          el.style.padding = "8px";
          el.style.border = "1px solid #ccc";
          el.style.borderRadius = "8px";
          el.style.boxShadow = "0 2px 6px rgba(0,0,0,0.2)";
          el.style.maxWidth = "300px";
          el.style.fontSize = "12px";
          el.style.color = "#333";
        
          el.innerHTML = `
            <strong>Set:</strong> ${rowData.set_name || "(none)"}<br>
            <strong>Name:</strong> ${rowData.name || "(no name)"}<br>
            <strong>Status:</strong> ${rowData.status || "(unknown)"}<br>
            <strong>Progress:</strong> ${rowData.progress || "(n/a)"}<br>
            <strong>Start Date:</strong> ${rowData.start_date || "(n/a)"}<br>
            <strong>End Date:</strong> ${rowData.end_date || "(n/a)"}<br>
            <strong>Started:</strong> ${rowData.start_timestamp || "(n/a)"}<br>
            <strong>ETC:</strong> ${rowData.etc || "(n/a)"}
          `;
        
          return el;
        },
        
      },
      groupBy: function(row) {
        const setName = row.set_name;
        if (!setName) {
          return "default";
        }
        return setName; // otherwise group by set_name
      },  
      groupStartOpen: function(set_name) {
        if (set_name=="default") {
          return true; // 👈 open groups with empty set_name
        }
        return false; // 👈 collapse normal groups
      }, // Optional: groups are collapsed by default
      groupHeader: function(value, count, data) {
        return `${value} (${count} forecasts)`; // Customize group label
      },
      tooltips: function(cell) {
        const data = cell.getRow().getData();
        return `
          <div>
            <strong>Set:</strong> ${data.set_name || "(none)"}<br>
            <strong>Name:</strong> ${data.name || "(no name)"}<br>
            <strong>Status:</strong> ${data.status || "(unknown)"}<br>
            <strong>Progress:</strong> ${data.progress || "(n/a)"}<br>
            <strong>Start Date:</strong> ${data.start_date || "(n/a)"}<br>
            <strong>End Date:</strong> ${data.end_date || "(n/a)"}<br>
            <strong>Started:</strong> ${data.start_timestamp || "(n/a)"}<br>
            <strong>Elapsed:</strong> ${data.elapsed || "(n/a)"}<br>
            <strong>ETC:</strong> ${data.etc || "(n/a)"}
          </div>
        `;
      },

      columns: [
        {
          title: "",
          formatter: function(cell, formatterParams, onRendered) {
            const button = document.createElement("button");
            button.innerText = "Load";
            button.style.padding = "4px 8px";
            button.style.border = "none";
            button.style.borderRadius = "4px";
            button.style.background = "#007bff";
            button.style.color = "white";
            button.style.cursor = "pointer";

              // 👇 Center the content inside the cell
            const cellElement = cell.getElement();
            cellElement.style.textAlign = "center";
            cellElement.style.verticalAlign = "middle"; // optional, for perfect centering vertically

      
            button.addEventListener("click", function(e) {
              e.stopPropagation(); // prevent row selection or expansion
              const rowData = cell.getRow().getData();
              console.log("Clicked row:", rowData);
              alert(`You clicked on forecast: ${rowData.name}`);
            });
      
            return button;
          },
          headerSort: false,
          width: 100,
        },
        {
          title: "",
          formatter: function(cell, formatterParams, onRendered) {
            const button = document.createElement("button");
            button.innerText = "View";
            button.style.padding = "4px 8px";
            button.style.border = "none";
            button.style.borderRadius = "4px";
            button.style.background = "#007bff";
            button.style.color = "white";
            button.style.cursor = "pointer";

              // 👇 Center the content inside the cell
            const cellElement = cell.getElement();
            cellElement.style.textAlign = "center";
            cellElement.style.verticalAlign = "middle"; // optional, for perfect centering vertically

      
            button.addEventListener("click", function(e) {
              e.stopPropagation(); // prevent row selection or expansion
              const rowData = cell.getRow().getData();
              console.log("Clicked row:", rowData);
              alert(`You clicked on forecast: ${rowData.name}`);
            });
      
            return button;
          },
          headerSort: false,
          width: 100,
        },
        {
          title: "",
          formatter: function(cell, formatterParams, onRendered) {
            const button = document.createElement("button");
            button.innerText = "Run";
            button.style.padding = "4px 8px";
            button.style.border = "none";
            button.style.borderRadius = "4px";
            button.style.background = "#007bff";
            button.style.color = "white";
            button.style.cursor = "pointer";

              // 👇 Center the content inside the cell
            const cellElement = cell.getElement();
            cellElement.style.textAlign = "center";
            cellElement.style.verticalAlign = "middle"; // optional, for perfect centering vertically

      
            button.addEventListener("click", function(e) {
              e.stopPropagation(); // prevent row selection or expansion
              const rowData = cell.getRow().getData();
              console.log("Clicked row:", rowData);
              alert(`You clicked on forecast: ${rowData.name}`);
            });
      
            return button;
          },
          headerSort: false,
          width: 100,
        },
        {
          title: "",
          formatter: function(cell, formatterParams, onRendered) {
            const button = document.createElement("button");
            button.innerText = "Delete";
            button.style.padding = "4px 8px";
            button.style.border = "none";
            button.style.borderRadius = "4px";
            button.style.background = "#d61d00";
            button.style.color = "white";
            button.style.cursor = "pointer";

              // 👇 Center the content inside the cell
            const cellElement = cell.getElement();
            cellElement.style.textAlign = "center";
            cellElement.style.verticalAlign = "middle"; // optional, for perfect centering vertically

      
            button.addEventListener("click", function(e) {
              e.stopPropagation(); // prevent row selection or expansion
              const rowData = cell.getRow().getData();
              console.log("Clicked row:", rowData);
              alert(`You clicked on forecast: ${rowData.name}`);
            });
      
            return button;
          },
          headerSort: false,
          width: 100,
        },
        { title: "Forecast Name", field: "name", headerFilter: "input" },
        { title: "Start Date", field: "start_date", sorter: "date", headerFilter: "input" },
        { title: "End Date", field: "end_date", sorter: "date", headerFilter: "input" },
        { title: "Status", field: "status", headerFilter: "list", headerFilterParams: { values: true } },
        { title: "Progress", field: "progress", sorter: "string" },
        { title: "Start Timestamp", field: "start_timestamp", sorter: "datetime" },
        { title: "Elapsed", field: "elapsed" },
        { title: "ETC", field: "etc", sorter: "datetime" }
      ]
    });

    forecastTable.on("tableBuilt", async () => {
      try {
        const response = await fetch("http://api.localhost/browse/data");
        const data = await response.json();
        forecastTable.setData(data);
      } catch (err) {
        console.error("Failed to load browse table data #1:", err);
      }
    });

    // fetch("http://api.localhost/forecasts")
    // .then(res => res.json())
    // .then(data => forecastTable.setData(data))
    // .catch(err => console.error("Failed to load forecasts:", err));


    document.getElementById("browse-search").addEventListener("input", e => {
      forecastTable.setFilter([
        [
          { field: "name", type: "like", value: e.target.value },
          { field: "status", type: "like", value: e.target.value }
        ]
      ]);
    });

    return forecastTable;
  } catch (error) {
    console.error("Failed to load browse table data #2:", error);
  }
}

export async function setupViewForecastTable() {
  try {
    const response = await fetch("http://api.localhost/view/forecast/sample");
    const data = await response.json();

    const columns = Object.keys(data[0] || {}).map(key => ({
      title: key.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()),
      field: key,
      headerFilter: "input", // optional: add a filter to each column automatically
    }));

    columns.unshift({
      title: "",
      formatter: function(cell, formatterParams, onRendered) {
        const button = document.createElement("button");
        button.innerText = "Report Error";
        button.style.padding = "4px 8px";
        button.style.border = "none";
        button.style.borderRadius = "4px";
        button.style.background = "#d61d00";
        button.style.color = "white";
        button.style.cursor = "pointer";
    
        // Center the content inside the cell
        const cellElement = cell.getElement();
        cellElement.style.textAlign = "center";
        cellElement.style.verticalAlign = "middle";
    
        button.addEventListener("click", function(e) {
          e.stopPropagation();
          const rowData = cell.getRow().getData();
          console.log("Clicked row:", rowData);
          alert(`You clicked on forecast: ${rowData.name}`);
        });
    
        return button;
      },
      headerSort: false,
      width: 100,
    });

    const table = new Tabulator("#forecast-view-table", {
      data: data,
      columns: columns,
      layout: "fitColumns",
      placeholder: "No forecast available",
      rowMouseEnter: function(e, row){
        const id = row.getData().id;
        d3.select(`[data-id='${id}']`).classed("highlighted", true);
      },
      rowMouseLeave: function(e, row){
          const id = row.getData().id;
          d3.select(`[data-id='${id}']`).classed("highlighted", false);
      }
    });

    document.getElementById("forecast-view-table-search").addEventListener("input", e => {
      forecastTable.setFilter([
        [
          { field: "name", type: "like", value: e.target.value },
          { field: "status", type: "like", value: e.target.value }
        ]
      ]);
    });

  } catch (error) {
    console.error("Failed to load view forecast data:", error);
  }
}


export async function setupLineItemViewTable() {

  try {
    const response = await fetch("http://api.localhost/view/lineitem/sample");
    const data = await response.json();
      
      const forecastTable = new Tabulator("#lineitem-view-table", {
        data,
        layout: "fitColumns",
        placeholder: "No Line Items",
        rowMouseEnter: function(e, row){
          const id = row.getData().id;
          d3.select(`[data-id='${id}']`).classed("highlighted", true);
        },
        rowMouseLeave: function(e, row){
            const id = row.getData().id;
            d3.select(`[data-id='${id}']`).classed("highlighted", false);
        },
        columnDefaults:{
          tooltip: function(e, cell, onRendered) {
            const rowData = cell.getRow().getData();
          
            const el = document.createElement("div");
            el.style.backgroundColor = "white";
            el.style.padding = "8px";
            el.style.border = "1px solid #ccc";
            el.style.borderRadius = "8px";
            el.style.boxShadow = "0 2px 6px rgba(0,0,0,0.2)";
            el.style.maxWidth = "300px";
            el.style.fontSize = "12px";
            el.style.color = "#333";
          
            el.innerHTML = `
              <strong>Set:</strong> ${rowData.set_name || "(none)"}<br>
              <strong>Name:</strong> ${rowData.name || "(no name)"}<br>
              <strong>Status:</strong> ${rowData.status || "(unknown)"}<br>
              <strong>Progress:</strong> ${rowData.progress || "(n/a)"}<br>
              <strong>Start Date:</strong> ${rowData.start_date || "(n/a)"}<br>
              <strong>End Date:</strong> ${rowData.end_date || "(n/a)"}<br>
              <strong>Started:</strong> ${rowData.start_timestamp || "(n/a)"}<br>
              <strong>ETC:</strong> ${rowData.etc || "(n/a)"}
            `;
          
            return el;
          },
          
        },
        tooltips: function(cell) {
          const data = cell.getRow().getData();
          return `
            <div>
              <strong>Set:</strong> ${data.set_name || "(none)"}<br>
              <strong>Name:</strong> ${data.name || "(no name)"}<br>
              <strong>Status:</strong> ${data.status || "(unknown)"}<br>
              <strong>Progress:</strong> ${data.progress || "(n/a)"}<br>
              <strong>Start Date:</strong> ${data.start_date || "(n/a)"}<br>
              <strong>End Date:</strong> ${data.end_date || "(n/a)"}<br>
              <strong>Started:</strong> ${data.start_timestamp || "(n/a)"}<br>
              <strong>Elapsed:</strong> ${data.elapsed || "(n/a)"}<br>
              <strong>ETC:</strong> ${data.etc || "(n/a)"}
            </div>
          `;
        },
    
        columns: [
          {
            title: "",
            formatter: function(cell, formatterParams, onRendered) {
              const button = document.createElement("button");
              button.innerText = "Report Error";
              button.style.padding = "4px 8px";
              button.style.border = "none";
              button.style.borderRadius = "4px";
              button.style.background = "#d61d00";
              button.style.color = "white";
              button.style.cursor = "pointer";
  
                // 👇 Center the content inside the cell
              const cellElement = cell.getElement();
              cellElement.style.textAlign = "center";
              cellElement.style.verticalAlign = "middle"; // optional, for perfect centering vertically
  
        
              button.addEventListener("click", function(e) {
                e.stopPropagation(); // prevent row selection or expansion
                const rowData = cell.getRow().getData();
                console.log("Clicked row:", rowData);
                alert(`You clicked on forecast: ${rowData.name}`);
              });
        
              return button;
            },
            headerSort: false,
            width: 100,
          },
          { title: "Date", field: "Date", sorter: "date" },
          { title: "Amount", field: "Amount" },
          { title: "Memo", field: "Memo",  headerFilter: "input" }
        ]
      });
    
      forecastTable.on("tableBuilt", async () => {
        try {
          const response = await fetch("http://api.localhost/view/lineitem/sample");
          const data = await response.json();
          forecastTable.setData(data);
        } catch (err) {
          console.error("Failed to load forecast data:", err);
        }
      });
    
      // fetch("http://api.localhost/forecasts")
      // .then(res => res.json())
      // .then(data => forecastTable.setData(data))
      // .catch(err => console.error("Failed to load forecasts:", err));
    
    
      document.getElementById("lineitem-view-table-search").addEventListener("input", e => {
        forecastTable.setFilter([
          [
            { field: "name", type: "like", value: e.target.value },
            { field: "status", type: "like", value: e.target.value }
          ]
        ]);
      });
    
      return forecastTable;
    } catch (error) {
      console.error("Failed to load dynamic table:", error);
    }
  }


export async function setupMilestoneResultViewTable() {

  try {
    const response = await fetch("http://api.localhost/view/milestone/sample");
    const data = await response.json();
    // console.log('Milestone Result data:');
    // console.log(data);
      
    const forecastTable = new Tabulator("#milestone-result-view-table", {
      data,
      layout: "fitColumns",
      placeholder: "No Milestone Results",
      rowMouseEnter: function(e, row){
        const id = row.getData().id;
        d3.select(`[data-id='${id}']`).classed("highlighted", true);
      },
      rowMouseLeave: function(e, row){
          const id = row.getData().id;
          d3.select(`[data-id='${id}']`).classed("highlighted", false);
      },
      columnDefaults:{
        tooltip: function(e, cell, onRendered) {
          const rowData = cell.getRow().getData();
          // console.log(rowData);
        
          const el = document.createElement("div");
          el.style.backgroundColor = "white";
          el.style.padding = "8px";
          el.style.border = "1px solid #ccc";
          el.style.borderRadius = "8px";
          el.style.boxShadow = "0 2px 6px rgba(0,0,0,0.2)";
          el.style.maxWidth = "300px";
          el.style.fontSize = "12px";
          el.style.color = "#333";
        
          el.innerHTML = `
            <strong>Name:</strong> ${rowData.name || "(n/a)"}<br>
            <strong>Type:</strong> ${rowData.type || "(n/a)"}<br>
            <strong>Condition:</strong> ${rowData.condition || "(n/a)"}
          `;
        
          return el;
        },
        
      },
      tooltips: function(cell) {
        const data = cell.getRow().getData();
        return `
          <div>
            <strong>Set:</strong> ${data.set_name || "(none)"}<br>
            <strong>Name:</strong> ${data.name || "(no name)"}<br>
            <strong>Status:</strong> ${data.status || "(unknown)"}<br>
            <strong>Progress:</strong> ${data.progress || "(n/a)"}<br>
            <strong>Start Date:</strong> ${data.start_date || "(n/a)"}<br>
            <strong>End Date:</strong> ${data.end_date || "(n/a)"}<br>
            <strong>Started:</strong> ${data.start_timestamp || "(n/a)"}<br>
            <strong>Elapsed:</strong> ${data.elapsed || "(n/a)"}<br>
            <strong>ETC:</strong> ${data.etc || "(n/a)"}
          </div>
        `;
      },
  
      columns: [
        {
          title: "",
          formatter: function(cell, formatterParams, onRendered) {
            const button = document.createElement("button");
            button.innerText = "Report Error";
            button.style.padding = "4px 8px";
            button.style.border = "none";
            button.style.borderRadius = "4px";
            button.style.background = "#d61d00";
            button.style.color = "white";
            button.style.cursor = "pointer";

              // 👇 Center the content inside the cell
            const cellElement = cell.getElement();
            cellElement.style.textAlign = "center";
            cellElement.style.verticalAlign = "middle"; // optional, for perfect centering vertically

      
            button.addEventListener("click", function(e) {
              e.stopPropagation(); // prevent row selection or expansion
              const rowData = cell.getRow().getData();
              console.log("Clicked row:", rowData);
              alert(`You clicked on forecast: ${rowData.name}`);
            });
      
            return button;
          },
          headerSort: false,
          width: 100,
        },
        { title: "Name", field: "Name", headerFilter: "input" },
        { title: "Type", field: "Type", headerFilter: "input"  },
        { title: "Condition", field: "Condition", headerFilter: "input"  }
      ]
    });
  
    forecastTable.on("tableBuilt", async () => {
      try {
        const response = await fetch("http://api.localhost/view/milestone/sample");
        const data = await response.json();
        forecastTable.setData(data);
      } catch (err) {
        console.error("Failed to load milestone result data:", err);
      }
    });
  
    document.getElementById("milestone-result-view-table-search").addEventListener("input", e => {
      forecastTable.setFilter([
        [
          { field: "name", type: "like", value: e.target.value },
          { field: "status", type: "like", value: e.target.value }
        ]
      ]);
    });
  
    return forecastTable;
  } catch (error) {
    console.error("Failed to load dynamic table:", error);
  }
}

function transformSankeyData(rawData) {
  const nodeNames = new Set();
  
  rawData.forEach(link => {
    nodeNames.add(link.source);
    nodeNames.add(link.target);
  });

  const nodes = Array.from(nodeNames).map(name => ({ name }));
  const nameToIndex = Object.fromEntries(nodes.map((node, i) => [node.name, i]));

  const links = rawData.map(link => ({
    source: nameToIndex[link.source],
    target: nameToIndex[link.target],
    value: link.value
  }));

  return { nodes, links };
}


export async function drawSankey() {
  try {
    const response = await fetch("http://api.localhost/view/sankey/sample");
    const rawData = await response.json();
    // console.log("rawData:", rawData); // <-- you should see a flat array here

    const sankeyData = transformSankeyData(rawData); // <-- transform the flat array into {nodes, links}

    const width = 800;
    const height = 500;
    const svg = d3.select("#sankey").append("svg")
      .attr("width", width)
      .attr("height", height);

    const { sankey, sankeyLinkHorizontal } = d3;
    const sankeyGenerator = sankey()
      .nodeWidth(20)
      .nodePadding(10)
      .extent([[1, 1], [width - 1, height - 6]]);

    const graph = sankeyGenerator({
      nodes: sankeyData.nodes.map(d => Object.assign({}, d)),
      links: sankeyData.links.map(d => Object.assign({}, d))
    });

    svg.append("g")
      .attr("fill", "none")
      .selectAll("path")
      .data(graph.links)
      .join("path")
      .attr("d", sankeyLinkHorizontal())
      .attr("stroke", "#000")
      .attr("stroke-width", d => Math.max(1, d.width))
      .attr("stroke-opacity", 0.5);

    svg.append("g")
      .selectAll("rect")
      .data(graph.nodes)
      .join("rect")
      .attr("x", d => d.x0)
      .attr("y", d => d.y0)
      .attr("height", d => d.y1 - d.y0)
      .attr("width", d => d.x1 - d.x0)
      .attr("fill", "steelblue");

    svg.append("g")
      .attr("font-family", "sans-serif")
      .attr("font-size", 12)
      .selectAll("text")
      .data(graph.nodes)
      .join("text")
      .attr("x", d => d.x0 - 6)
      .attr("y", d => (d.y1 + d.y0) / 2)
      .attr("dy", "0.35em")
      .attr("text-anchor", "end")
      .text(d => d.name)
      .filter(d => d.x0 < width / 2)
      .attr("x", d => d.x1 + 6)
      .attr("text-anchor", "start");

  } catch (error) {
    console.error("Failed to draw Sankey diagram:", error);
  }
}

















// setupDraftRunParameterTable();
// setupDraftAccountTable();
// setupDraftLineItemTable();
// setupDraftDecisionRuleTable();
// setupDraftMilestoneTable();

export async function setupDraftRunParameterTable() {

  try {
    const response = await fetch("http://api.localhost/view/lineitem/sample");
    const data = await response.json();
      
      const forecastTable = new Tabulator("#lineitem-view-table", {
        data,
        layout: "fitColumns",
        placeholder: "No Line Items",
        rowMouseEnter: function(e, row){
          const id = row.getData().id;
          d3.select(`[data-id='${id}']`).classed("highlighted", true);
        },
        rowMouseLeave: function(e, row){
            const id = row.getData().id;
            d3.select(`[data-id='${id}']`).classed("highlighted", false);
        },
        columnDefaults:{
          tooltip: function(e, cell, onRendered) {
            const rowData = cell.getRow().getData();
          
            const el = document.createElement("div");
            el.style.backgroundColor = "white";
            el.style.padding = "8px";
            el.style.border = "1px solid #ccc";
            el.style.borderRadius = "8px";
            el.style.boxShadow = "0 2px 6px rgba(0,0,0,0.2)";
            el.style.maxWidth = "300px";
            el.style.fontSize = "12px";
            el.style.color = "#333";
          
            el.innerHTML = `
              <strong>Set:</strong> ${rowData.set_name || "(none)"}<br>
              <strong>Name:</strong> ${rowData.name || "(no name)"}<br>
              <strong>Status:</strong> ${rowData.status || "(unknown)"}<br>
              <strong>Progress:</strong> ${rowData.progress || "(n/a)"}<br>
              <strong>Start Date:</strong> ${rowData.start_date || "(n/a)"}<br>
              <strong>End Date:</strong> ${rowData.end_date || "(n/a)"}<br>
              <strong>Started:</strong> ${rowData.start_timestamp || "(n/a)"}<br>
              <strong>ETC:</strong> ${rowData.etc || "(n/a)"}
            `;
          
            return el;
          },
          
        },
        tooltips: function(cell) {
          const data = cell.getRow().getData();
          return `
            <div>
              <strong>Set:</strong> ${data.set_name || "(none)"}<br>
              <strong>Name:</strong> ${data.name || "(no name)"}<br>
              <strong>Status:</strong> ${data.status || "(unknown)"}<br>
              <strong>Progress:</strong> ${data.progress || "(n/a)"}<br>
              <strong>Start Date:</strong> ${data.start_date || "(n/a)"}<br>
              <strong>End Date:</strong> ${data.end_date || "(n/a)"}<br>
              <strong>Started:</strong> ${data.start_timestamp || "(n/a)"}<br>
              <strong>Elapsed:</strong> ${data.elapsed || "(n/a)"}<br>
              <strong>ETC:</strong> ${data.etc || "(n/a)"}
            </div>
          `;
        },
    
        columns: [
          {
            title: "",
            formatter: function(cell, formatterParams, onRendered) {
              const button = document.createElement("button");
              button.innerText = "Report Error";
              button.style.padding = "4px 8px";
              button.style.border = "none";
              button.style.borderRadius = "4px";
              button.style.background = "#d61d00";
              button.style.color = "white";
              button.style.cursor = "pointer";
  
                // 👇 Center the content inside the cell
              const cellElement = cell.getElement();
              cellElement.style.textAlign = "center";
              cellElement.style.verticalAlign = "middle"; // optional, for perfect centering vertically
  
        
              button.addEventListener("click", function(e) {
                e.stopPropagation(); // prevent row selection or expansion
                const rowData = cell.getRow().getData();
                console.log("Clicked row:", rowData);
                alert(`You clicked on forecast: ${rowData.name}`);
              });
        
              return button;
            },
            headerSort: false,
            width: 100,
          },
          { title: "Date", field: "Date", sorter: "date" },
          { title: "Amount", field: "Amount" },
          { title: "Memo", field: "Memo",  headerFilter: "input" }
        ]
      });
    
      forecastTable.on("tableBuilt", async () => {
        try {
          const response = await fetch("http://api.localhost/view/lineitem/sample");
          const data = await response.json();
          forecastTable.setData(data);
        } catch (err) {
          console.error("Failed to load forecast data:", err);
        }
      });
    
      // fetch("http://api.localhost/forecasts")
      // .then(res => res.json())
      // .then(data => forecastTable.setData(data))
      // .catch(err => console.error("Failed to load forecasts:", err));
    
    
      document.getElementById("lineitem-view-table-search").addEventListener("input", e => {
        forecastTable.setFilter([
          [
            { field: "name", type: "like", value: e.target.value },
            { field: "status", type: "like", value: e.target.value }
          ]
        ]);
      });
    
      return forecastTable;
    } catch (error) {
      console.error("Failed to load dynamic table:", error);
    }
  }
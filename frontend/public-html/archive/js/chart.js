const svg = d3.select("#line-chart"),
  width = +svg.attr("width"),
  height = +svg.attr("height"),
  margin = { top: 20, right: 30, bottom: 30, left: 40 },
  chartWidth = width - margin.left - margin.right,
  chartHeight = height - margin.top - margin.bottom;

const chart = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
const x = d3.scaleUtc().range([0, chartWidth]);
const y = d3.scaleLinear().range([chartHeight, 0]);
const color = d3.scaleOrdinal(d3.schemeCategory10);

const xAxis = chart.append("g").attr("transform", `translate(0,${chartHeight})`);
const yAxis = chart.append("g");

const tooltip = d3.select("body")
  .append("div")
  .attr("class", "tooltip")
  .style("opacity", 0)
  .style("position", "absolute")
  .style("background", "white")
  .style("border", "1px solid #aaa")
  .style("padding", "6px")
  .style("font-size", "12px")
  .style("pointer-events", "none");

const parseDate = d3.utcParse("%Y-%m-%d");

const line = d3.line()
  .x(d => x(new parseDate(d.timestamp)))
  .y(d => y(d.value));

  const filterState = {
    startDate: null,
    endDate: null,
    selectedAccounts: []
  };

  let normalizedSeries = [];
  

  function sanitizeFieldName(fieldName) {
    return fieldName
      .replace(/[^a-zA-Z0-9]/g, "-");  // replace all non-alphanum with -
  }
  



  // function redrawChart() {
  //   console.log('redrawChart');
  //   // Use normalizedSeries + filterState to determine what to draw
  //   const filteredSeries = normalizedSeries
  //     .filter(series => filterState.selectedAccounts.includes(series.name))
  //     .map(series => ({
  //       name: series.name,
  //       values: series.values.filter(d => 
  //         (!filterState.startDate || d.timestamp >= filterState.startDate) &&
  //         (!filterState.endDate || d.timestamp <= filterState.endDate)
  //       )
  //     }));
  
  //   // clear chart
  //   chart.selectAll(".line-series").remove();
  //   chart.selectAll(".dot").remove();
  
  //   const allFilteredData = filteredSeries.flatMap(s => s.values);
  
  //   if (allFilteredData.length > 0) {
  //     x.domain(d3.extent(allFilteredData, d => parseDate(d.timestamp)));
  //     y.domain([0, d3.max(allFilteredData, d => d.value)]);
  //   }
  
  //   xAxis.call(
  //     d3.axisBottom(x)
  //       .tickValues(
  //         d3.utcDay.range(
  //           d3.utcDay.floor(x.domain()[0]),
  //           d3.utcDay.offset(d3.utcDay.floor(x.domain()[1]), 1)
  //         )
  //       )
  //       .tickFormat(d3.utcFormat("%Y-%m-%d"))
  //   );
  //   yAxis.call(d3.axisLeft(y));
  
  //   const series = chart.selectAll(".line-series").data(filteredSeries, d => d.name);
  
  //   series.enter()
  //     .append("path")
  //     .attr("class", "line-series")
  //     .datum(d => d)
  //     .attr("fill", "none")
  //     .attr("stroke", d => color(d.name))
  //     .attr("stroke-width", 2)
  //     .attr("d", d => line(
  //       d.values.map(p => ({
  //         timestamp: parseDate(p.timestamp),
  //         value: p.value
  //       }))
  //     ));
  // }
  

  export function updateChart(dataSeries) {
    // drawEmptyChart()
    // Ensure all series use { timestamp, value } structure
    // console.log('ENTER updateChart');
    // console.log(dataSeries);

    


    normalizedSeries = dataSeries.map(series => {
      const { name, values } = series;
      const cleaned = values.map(d => ({
        timestamp: d.timestamp,
        value: d.value
      }));
      return { name, values: cleaned };
    });

    const allData = normalizedSeries.flatMap(s => s.values);

    // Find the min and max dates
    const dateExtent = d3.extent(allData, d => d.timestamp);
    
    // Set the inputs
    d3.select("#start-date")
      .property("value", dateExtent[0]);

    d3.select("#end-date")
      .property("value", dateExtent[1]);

    const filtersContainer = d3.select("#account-filters");

    // Clear previous checkboxes first, if any (important if reloading)
    filtersContainer.selectAll(".account-checkbox").remove();
  
    filtersContainer.selectAll("div.account-checkbox")
      .data(normalizedSeries)
      .enter()
      .append("div")
      .attr("class", "account-checkbox")
      .each(function(d) {
        const checkbox = d3.select(this)
          .append("input")
          .attr("type", "checkbox")
          .attr("id", `checkbox-${sanitizeFieldName(d.name)}`)
          .attr("value", d.name)
          .property("checked", true);
  
        d3.select(this)
          .append("label")
          .attr("for", `checkbox-${sanitizeFieldName(d.name)}`)
          .text(d.name);
      });

    // console.log(allData);

    
    // just for logging
    // const parsedAllData = allData.map(d => {
    //   const parsedTimestamp = parseDate(d.timestamp);
    //   console.log('Raw timestamp:', d.timestamp, 'Parsed:', parsedTimestamp, parsedTimestamp ? parsedTimestamp.toISOString() : "NULL");
    //   return {
    //     timestamp: parsedTimestamp,
    //     value: d.value
    //   };
    // });

    x.domain(d3.extent(allData, d => parseDate(d.timestamp)));
    y.domain([0, d3.max(allData, d => d.value)]);
  
    // xAxis.call(d3.axisBottom(x).tickFormat(d3.timeFormat("%Y-%m-%d")));
    const tickDates = d3.utcDay.range(
      d3.utcDay.floor(x.domain()[0]),
      d3.utcDay.offset(d3.utcDay.floor(x.domain()[1]), 1) // add one day to make sure last date included
    );
    
    xAxis.call(
      d3.axisBottom(x)
        .tickValues(tickDates)
        .tickFormat(d3.timeFormat("%Y-%m-%d"))
    );
    
    // xAxis.selectAll(".tick")
    // .attr("transform", function() {
    //   const transform = d3.select(this).attr("transform"); // eg: "translate(523,0)"
    //   const match = /translate\(([^,]+),([^)]+)\)/.exec(transform);
    //   if (!match) return transform; // fallback

    //   const x = parseFloat(match[1]);
    //   const y = parseFloat(match[2]);
    //   return `translate(${x + 125},${y})`; // <-- add 10 to x!
    // });
    // console.log("x domain:", x.domain());
    const ticks = x.ticks();
    // console.log("x ticks:", ticks.map(d => d.toISOString()));


    

    yAxis.call(d3.axisLeft(y));

    const series = chart.selectAll(".line-series").data(normalizedSeries, d => d.name);

    // console.log('series:');
    // console.log(series);
  
    series.enter()
      .append("path")
      .attr("class", "line-series")
      .merge(series)
      .transition()
      .duration(500)
      .attr("fill", "none")
      .attr("stroke", d => color(d.name))
      .attr("stroke-width", 2)
      .attr("d", d => line(d.values));
  
    series.exit().remove();
  
    // Remove old dots and add new ones
    chart.selectAll(".dot").remove();
  
    normalizedSeries.forEach((seriesData) => {
      chart.selectAll(`.dot-${sanitizeFieldName(seriesData.name)}`)
        .data(seriesData.values)
        .enter()
        .append("circle")
        .attr("class", `dot dot-${ sanitizeFieldName(seriesData.name)}`)
        .attr("cx", d => x(parseDate(d.timestamp)))
        .attr("cy", d => y(d.value))
        .attr("r", 4)
        .attr("fill", color(sanitizeFieldName(seriesData.name)))
        .on("mouseover", (event, d) => {
          tooltip.transition().duration(200).style("opacity", 0.9);
          tooltip.html(`${seriesData.name}<br>${d3.timeFormat("%Y-%m-%d")(parseDate(d.timestamp))}: $${d.value.toFixed(2)}`)
            .style("left", (event.pageX + 10) + "px")
            .style("top", (event.pageY - 28) + "px");
        })
        .on("mouseout", () => {
          tooltip.transition().duration(500).style("opacity", 0);
        });
    });
  
    // Create or update legend
    if (d3.select(".legend").empty()) {
      // const color = d3.scaleOrdinal(d3.schemeCategory10); // or whatever color scale you use

      // // After you've drawn the lines, add the legend
      // const legend = svg.append("g")
      //     .attr("class", "legend")
      //     .attr("transform", "translate(700,30)"); // adjust X,Y to shift legend to right

      // legend.selectAll("text")
      //   .data(normalizedSeries) // your pivoted series list
      //   .enter()
      //   .append("g")
      //   .attr("transform", (d, i) => `translate(0, ${i * 20})`) // 20px spacing between items
      //   .each(function(d, i) {
      //     d3.select(this)
      //       .append("rect")
      //       .attr("x", 0)
      //       .attr("y", -10)
      //       .attr("width", 10)
      //       .attr("height", 10)
      //       .attr("fill", color(d.name));

      //     d3.select(this)
      //       .append("text")
      //       .attr("x", 20)
      //       .attr("y", 0)
      //       .attr("dy", "0.32em")
      //       .style("font-size", "12px")
      //       .text(d.name);
      //   });
      const legend = svg.append("g")
        .attr("class", "legend")
        .attr("transform", "translate(700,30)");

      const legendItem = legend.selectAll(".legend-item")
        .data(normalizedSeries)
        .enter()
        .append("g")
        .attr("class", "legend-item")
        .attr("transform", (d, i) => `translate(0, ${i * 20})`);

      // Colored square
      legendItem.append("rect")
        .attr("x", 0)
        .attr("y", -10)
        .attr("width", 10)
        .attr("height", 10)
        .attr("fill", d => color(d.name));

      // Label text
      legendItem.append("text")
        .attr("x", 20)
        .attr("y", 0)
        .attr("dy", "0.32em")
        .style("font-size", "12px")
        .text(d => d.name);

      legendItem
        .on("mouseover", function(event, d) {
          // d = the series you're hovering on
          d3.selectAll(".line-series")
            .transition()
            .duration(200)
            .style("stroke", s => s.name === d.name ? color(d.name) : "#ccc");  // highlight hovered, grey out others

          // Highlight matching points
          d3.selectAll(".dot")
            .transition()
            .duration(200)
            .style("fill", s => s.name === d.name ? color(d.name) : "#ccc")
            .style("opacity", s => s.name === d.name ? 1 : 0.3); // optional: fade non-hovered points
        })
        .on("mouseout", function(event, d) {
          // Restore all lines to original colors
          d3.selectAll(".line-series")
            .transition()
            .duration(200)
            .style("stroke", s => color(s.name));

          // Restore points
          d3.selectAll(".dot")
            .transition()
            .duration(200)
            .style("fill", s => color(s.name))
            .style("opacity", 1);
        });
    }
  }
  
  d3.select("#apply-filters").on("click", function() {
    console.log("Apply Filters clicked");
  
    const startDate = new Date(d3.select("#start-date").property("value"));
    const endDate = new Date(d3.select("#end-date").property("value"));
  
    // Get list of selected accounts
    const selectedAccounts = [];
    d3.selectAll("#account-filters input[type=checkbox]").each(function() {
      const cb = d3.select(this);
      if (cb.property("checked")) {
        selectedAccounts.push(cb.property("value"));
      }
    });
  
    console.log("Selected accounts:", selectedAccounts);
    console.log("Date range:", startDate, "to", endDate);
  
    // Filter normalizedSeries
    const filteredSeries = normalizedSeries
      .filter(series => selectedAccounts.includes(series.name))
      .map(series => ({
        name: series.name,
        values: series.values.filter(d => {
          const date = d.timestamp instanceof Date ? d.timestamp : parseDate(d.timestamp);
          return date >= startDate && date <= endDate;
        })
      }));
  
    console.log("Filtered series:", filteredSeries);
  
    // 🧹 Clear old lines
    chart.selectAll(".line-series").remove();
    chart.selectAll(".dot").remove();
  
    // 🛠 Update domains
    const allFilteredData = filteredSeries.flatMap(s => s.values);
  
    if (allFilteredData.length > 0) {
      x.domain(d3.extent(allFilteredData, d => parseDate(d.timestamp)));
      y.domain([0, d3.max(allFilteredData, d => d.value)]);
    }
  
    xAxis.call(
      d3.axisBottom(x)
        .tickValues(
          d3.utcDay.range(
            d3.utcDay.floor(x.domain()[0]),
            d3.utcDay.offset(d3.utcDay.floor(x.domain()[1]), 1)
          )
        )
        .tickFormat(d3.utcFormat("%Y-%m-%d"))
    );
  
    yAxis.call(d3.axisLeft(y));
  
    // 🖌 Redraw lines
    const series = chart.selectAll(".line-series").data(filteredSeries, d => d.name);
    console.log('series:');
    console.log(series);
    series.enter()
      .append("path")
      .attr("class", "line-series")
      .datum(d => d)  // <-- bind datum manually again here!
      .attr("fill", "none")
      .attr("stroke", d => color(d.name))
      .attr("stroke-width", 2)
      .attr("d", d => line(
        d.values.map(p => ({
          timestamp: parseDate(p.timestamp),
          value: p.value
        }))
      ));
    
    // TODO 🖌 If you have dots too, you would redraw them here
    // redrawChart(); // <-- always apply current filters
  });
  

  export async function fetchAndUpdateChart() {
    try {
      const response = await fetch("http://api.localhost/view/forecast/sample");
      const data = await response.json();
  
      if (!data || data.length === 0) {
        console.log("No forecast data yet — drawing empty chart.");
        drawEmptyChart();
        return;
      }
  
      // Find all the keys except "Date" and maybe "Memo" etc.
      const allKeys = Object.keys(data[0]).filter(key => !["Date", "Memo", "Memo Directives", "Next Income Date"].includes(key));

      // Now pivot it into the structure D3 expects
      const pivotedSeries = allKeys.map(key => {
        return {
          name: key,
          values: data.map(row => ({
            timestamp: row.Date,
            value: parseFloat(row[key]) || 0  // defensive: turn to float, fallback to 0 if missing
          }))
        };
      });

      // console.log(pivotedSeries);

      // Now pass pivotedSeries to D3!
      updateChart(pivotedSeries);

  
    } catch (err) {
      console.error("Polling failed:", err);
      drawEmptyChart();
    }
  }
  
  function drawEmptyChart() {
    const now = new Date();
    const xExtent = [new Date(now - 3 * 24 * 60 * 60 * 1000), now]; // 3 days of fake x-range
    const yExtent = [0, 100]; // some dummy y-range
  
    x.domain(xExtent);
    y.domain(yExtent);
  
    xAxis.call(d3.axisBottom(x));
    yAxis.call(d3.axisLeft(y));
  
    chart.selectAll(".line-series").remove();
    chart.selectAll(".dot").remove();
  
    // Optional: show "No data" message
    const placeholder = chart.selectAll(".no-data-label").data([1]);
    placeholder.enter()
      .append("text")
      .attr("class", "no-data-label")
      .attr("x", chartWidth / 2)
      .attr("y", chartHeight / 2)
      .attr("text-anchor", "middle")
      .attr("fill", "#888")
      .text("No data to display");
  
    placeholder.exit().remove();
  }
  
    

function drawExpenseForecastPlot(evt, plotTitle, tabName, data_path) {
    //console.log('ENTER drawExpenseForecastPlot');
    form = document.getElementById("dynamicaccounttogglelist");

    var formData = new FormData(form);
  // output as an object
  // console.log('formData:')
  // console.log(formData);

    var filter_ON_array = [];
    for (const p of formData) {
        if ( p[0] == 'account_toggle_checkbox_list' ){
            filter_ON_array.push(p[1]);
        }
    }



  //will be 0 on first load, so we treat 0 the same as max
    var DO_APPLY_FILTER = ( filter_ON_array.length > 0 );

// Declare all variables
    var i, tabcontent, tablinks;

//     if ( evt != -1 && evt !== undefined ){
// // Get all elements with class="tablinks" and remove the class "active"
//         viewtablinks = document.getElementsByClassName("viewtablinks");
//         for (i = 0; i < viewtablinks.length; i++) {
//             viewtablinks[i].className = viewtablinks[i].className.replace(" active", "");
//         }

// // Show the current tab, and add an "active" class to the button that opened the tab

//         console.log('evt:');
//         console.log(evt);
//         console.log('evt.className:');
//         console.log(evt.className);
//         evt.currentTarget.className += " active";
//     } else {
//     //tabName is whichever has active class
//     //tabName = document.getElementsByClassName("viewtablinks active")[0].id.replace('Link','');
//         tabName = localStorage.getItem('activeDashboardView');
//     }


    d3.selectAll("svg").remove();

    var main_bkg_color = '#e9e9e9';
    var legend_bkg_color = '#ffffff';

    var width = 940;
    var height = 400;
    var marginBottom = 70;
    var marginTop = 50;
    var marginLeft = 70;
    var marginRight = 15;

    var legendLeftMargin = 0;
    var legendRightMargin = 15;
    var legendTopMargin = 15;
    var legendBottomMargin = 15;

    var legendEntryHeight = 20;
    var tooltip_row_height = 20;

    var innerLegendLeftMargin = 10;
    var innerLegendTopMargin = 20;
    var innerLegendBottomMargin = 20;
    var legendMarkSideLength = 10;

    var right_legend_panel_width = 250;

    var tooltip_height = 20;
    var tooltip_margin_left = 10;


    var plot_color_cycle = [ '#ff0000', '#ff9900', '#ffff00','#00ff00', '#0000ff', '#ff00ff', '#996633', '#ffffff', '#000000'];

    var tooltip_bkg_color = '#ffffff';

//Create SVG element
    var svg = d3.select("#svg-plot-parent")
    .append("svg")
    .attr("width", width)
    .attr("height", height);

    svg.append("rect")
    .attr("x", 0)
    .attr("y", 0)
    .attr("width", width)
    .attr("height", height)
    .attr("fill", main_bkg_color);





//Main title
// Max title length: 94 chars. Offset = 400. so 400/94
    var title_text = plotTitle;
    var nchar_of_title = title_text.length;
    svg.append("text")
    .attr("x", ((width - right_legend_panel_width ) / 2) - ( 400/94 * nchar_of_title ) )
    .attr("y", marginTop / 2)
    .text(title_text);


    const date_format_options = {
      year: 'numeric',
      month: 'numeric',
      day: 'numeric'
  };
  const dateTimeFormat = new Intl.DateTimeFormat('en', date_format_options);



//Y axis title
//max left axis title length: 40 chars, w offset 130, so 130/40
  var left_axis_title_text = 'Dollars';
  var nchar_of_left_axis_title = left_axis_title_text.length;
  svg.append("text")
  .attr("transform", "translate("+(marginLeft/3)+"," + (height/2.075 + ( 140/40 * nchar_of_left_axis_title ) ) + ")rotate(-90)")
//.attr("dy", "1em")
  .text(left_axis_title_text);




//draw using bound data
  d3.csv(data_path, function(error, data) {
  //d3.csv("../data/current_forecast_data.csv", function(error, data) {
      if (error) throw error;


      //draw legend bkg panel
      svg.append("rect")
      .attr("x", width - right_legend_panel_width + legendLeftMargin)
      .attr("y",legendTopMargin)
      .attr("width", right_legend_panel_width - ( legendRightMargin + legendLeftMargin ) )
  //.attr("height", innerLegendTopMargin  + (data.columns.length - 0.5) * legendEntryHeight )
      .attr("height", height - innerLegendTopMargin - innerLegendBottomMargin )
      .attr("fill", legend_bkg_color);

      svg.append("text")
      .attr("x", width - right_legend_panel_width*0.67 )
      .attr("y", legendTopMargin + innerLegendTopMargin )
      .attr("font-weight", "bold")
      .text("Legend");



      var input_date_range_string = d3.select("#vizfilterdaterange").property("value");
      var input_date_values_raw = input_date_range_string.split('-');

      var lb_date = input_date_values_raw[0];
      var rb_date = input_date_values_raw[1];



      const date_format_options = {
          year: 'numeric',
          month: 'numeric',
          day: 'numeric'
      };
      const dateTimeFormat = new Intl.DateTimeFormat('en', date_format_options)

//these need to parse m/d/yyyy and add ' 00:00:00'
      var input_min_date = new Date(dateTimeFormat.format(Date.parse(lb_date))+' 00:00:00');
      var input_max_date = new Date(dateTimeFormat.format(Date.parse(rb_date))+' 00:00:00');

      var subtitle_text = dateTimeFormat.format(min_date)+' -> '+dateTimeFormat.format(max_date);
      var nchar_of_subtitle = subtitle_text.length;
//Subtitle
      svg.append("text")
      .attr("x", ((width - right_legend_panel_width ) / 2) - ( 400/94 * nchar_of_subtitle ) )
      .attr("y", marginTop / 2)
      .attr("dy", "1em")
      .text(subtitle_text);

      //console.log(data);

//filtered_data = data;
      filtered_data = data.filter(function(d){ return input_max_date >= new Date(d.Date.substring(0,4)+'-'+d.Date.substring(4,6)+'-'+d.Date.substring(6,8)+' 00:00:00') & new Date(d.Date.substring(0,4)+'-'+d.Date.substring(4,6)+'-'+d.Date.substring(6,8)+' 00:00:00') >= input_min_date })

// console.log('data:');
// console.log(data);
// console.log('filtered_data:');
// console.log(filtered_data);

      min_date = d3.min(filtered_data, function(d){
        return new Date(d.Date.substring(0,4)+'-'+d.Date.substring(4,6)+'-'+d.Date.substring(6,8)+' 00:00:00')
    });
      max_date = d3.max(filtered_data, function(d){
        return new Date(d.Date.substring(0,4)+'-'+d.Date.substring(4,6)+'-'+d.Date.substring(6,8)+' 00:00:00')
    });

// console.log('input_min_date:');
// console.log(input_min_date);
// console.log('input_max_date:');
// console.log(input_max_date);
// console.log('min_date:');
// console.log(min_date);
// console.log('max_date:');
// console.log(max_date);

      line_minima = [];
      line_maxima = [];
      plot_lower_y_bound = 0;
      plot_upper_y_bound = 0;
      for ( let column_index = 1; column_index < ( data.columns.length - 1) ; column_index++ ){

        current_column_name = data.columns[column_index]


        if ( DO_APPLY_FILTER ) {
            //console.log('Applying filter');
            var skip_flag = true;
            for ( c_index in filter_ON_array ) {
                if ( current_column_name == filter_ON_array[c_index] ){
                    skip_flag = false;
                }
                
            }
            if ( skip_flag ){
                    //console.log('Skipping column: '+current_column_name)
                continue;
            }
        }


        if ( tabName == 'NetWorth' ) {

            if ( current_column_name != 'Net Worth' ){
                continue
            }

        } else if ( tabName == 'NetGainLoss' ) {

            if ( current_column_name != 'Net Gain' & current_column_name != 'Net Loss' ){
                continue
            }

        } else if ( tabName == 'AccountType' ) {

            if ( current_column_name != 'Loan Total' & current_column_name != 'CC Debt Total' & current_column_name != 'Liquid Total' ){
                continue
            }

        } else if ( tabName == 'Interest' ) {

            if ( current_column_name != 'Marginal Interest' ){
                continue
            }

        }






        single_line_minima = d3.max(filtered_data, function(d){
            plot_lower_y_bound = Math.min(d[data.columns[column_index]],plot_lower_y_bound);
        });

        single_line_maxima = d3.max(filtered_data, function(d){
            plot_upper_y_bound = Math.max(d[data.columns[column_index]],plot_upper_y_bound);
        });


    }

    //I want the range plot_lower_y_bound -> plot_upper_y_bound to contain 0
    if ( plot_lower_y_bound > 0 ) {
        plot_lower_y_bound = 0
    }
    if ( plot_upper_y_bound < 0 ) {
        plot_upper_y_bound = 0
    }


// Create a scale: transform value in pixel
    var date_to_x = d3.scaleTime()
    .domain([input_min_date, input_max_date])
    .range([0,width - ( marginLeft + marginRight ) - right_legend_panel_width ])


    var y = d3.scaleLinear()
    .domain([plot_lower_y_bound, plot_upper_y_bound*1.1 ])      
    .range([height - ( marginTop + marginBottom ), 0 ]);  

    const gx_bottom = svg.append("g")
    .attr("transform", `translate(${marginLeft},${height - marginBottom})`)
    .call(d3.axisBottom(date_to_x).tickFormat(d3.timeFormat("%Y-%m-%d")))
    .selectAll("text")  
    .style("text-anchor", "end")
    .attr("dx", "-.8em")
    .attr("dy", "-0.5em")
    .attr("transform", "rotate(-90)" );


    const gx_left = svg.append("g")
    .attr("transform", `translate(${marginLeft},${ marginTop })`)
    .call(d3.axisLeft(y));


//assumes first column is Date, last column is Memo
    var no_of_lines_on_plot = 0;
    for ( let column_index = 1 ; column_index < ( data.columns.length - 1) ; column_index++ ) {

        current_column_name = data.columns[column_index]

        if ( DO_APPLY_FILTER ) {
            //console.log('Applying filter');
            var skip_flag = true;
            for ( c_index in filter_ON_array ) {
                if ( current_column_name == filter_ON_array[c_index] ){
                    skip_flag = false;
                }
                
            }
            if ( skip_flag ){
                    //console.log('Skipping column: '+current_column_name)
                continue;
            }
        }

        if ( tabName == 'NetWorth' ) {

            current_plot_color = '#0000ff';

            if ( current_column_name != 'Net Worth' ){
                continue
            }

        } else if ( tabName == 'NetGainLoss' ) {

            if ( current_column_name != 'Net Gain' & current_column_name != 'Net Loss' ){
                continue
            }

            if ( current_column_name == 'Net Loss' ) {
                current_plot_color = '#ff0000';
            }

            if ( current_column_name == 'Net Gain' ) {
                current_plot_color = '#00ff00';
            }

        } else if ( tabName == 'AccountType' ) {

            if ( current_column_name != 'Loan Total' & current_column_name != 'CC Debt Total' & current_column_name != 'Liquid Total' ){
                continue
            }

            if ( current_column_name == 'Loan Total' ) {
                current_plot_color = '#0000ff';
            }

            if ( current_column_name == 'CC Debt Total' ) {
                current_plot_color = '#ff9900';
            }

            if ( current_column_name == 'Liquid Total' ) {
                current_plot_color = '#00ff00';
            }

        } else if ( tabName == 'Interest' ) {

            if ( current_column_name != 'Marginal Interest' ){
                continue
            }

            if ( current_column_name == 'Marginal Interest' ) {
                current_plot_color = '#ff9900';
            }

        } else {
            current_plot_color = plot_color_cycle[(column_index-1) % plot_color_cycle.length ];
        }

        no_of_lines_on_plot = no_of_lines_on_plot + 1;




// draw path
        svg.append("path")
        .datum(filtered_data)
        .attr("fill", "none")
        .attr('class', 'plotline')
        .attr("stroke", current_plot_color)
        .attr("stroke-width", 2)
        .attr("d", d3.line()
            .x(function(d) { return marginLeft + date_to_x(new Date(d.Date.substring(0,4)+'-'+d.Date.substring(4,6)+'-'+d.Date.substring(6,8)+' 00:00:00')) })
            .y(function(d) { 

                return marginTop + y( d[data.columns[column_index]]) })
            );

  //draw legend mark
        svg.append("rect")
        .datum(filtered_data)
        .attr("x", width - right_legend_panel_width + innerLegendLeftMargin)
        .attr("y",function(d){
            return legendTopMargin + innerLegendTopMargin*1.5 + ( no_of_lines_on_plot - 1 ) * legendEntryHeight
        })
        .attr("width", legendMarkSideLength )
        .attr("height", legendMarkSideLength  )
        .attr("fill", current_plot_color)
        .attr("stroke", "black");

  //draw legend labels
        svg.append("text")
        .datum(filtered_data)
        .attr("x", width - right_legend_panel_width + innerLegendLeftMargin + legendMarkSideLength*1.5 )
        .attr("y",function(d){
            return legendTopMargin + innerLegendTopMargin*1.5 + ( no_of_lines_on_plot - 1 ) * legendEntryHeight + 0.5*legendEntryHeight
        })
        .text(data.columns[column_index]);


        circles = svg.selectAll('.dot')
        .data(filtered_data)
        .enter()   
        .append('circle')
        .attr('class', '.dot')
        .attr('cx', function(d){
            return marginLeft + date_to_x(new Date(d.Date.substring(0,4)+'-'+d.Date.substring(4,6)+'-'+d.Date.substring(6,8)+' 00:00:00'));
        })
        .attr('cy', function(d){
            return marginTop + y( d[data.columns[column_index]] )
        })
        .attr('r', 2)
        .attr("stroke", current_plot_color)
        .attr("fill", current_plot_color)
        .on('mouseover', function(d){

            var value_entry_width = d[data.columns[column_index]].length * 10;
            var date_entry_width = 140;
            var tooltip_background_width = tooltip_margin_left + Math.max(value_entry_width,date_entry_width);

            svg.append("rect")
            .attr("x", marginLeft + date_to_x(new Date(d.Date.substring(0,4)+'-'+d.Date.substring(4,6)+'-'+d.Date.substring(6,8)+' 00:00:00')) )
            .attr("y",  marginTop + y( d[data.columns[column_index]] )  )
        .attr("width", tooltip_background_width ) //this box is too short for values without decimal points
        .attr("height", tooltip_height * 2.1)
        .attr("fill", tooltip_bkg_color)
        .attr("stroke", '#000000')
        .attr("class","tooltip");

        // Column Name, dollar value
        svg.append("text")
        .attr("x", marginLeft + tooltip_margin_left + date_to_x(new Date(d.Date.substring(0,4)+'-'+d.Date.substring(4,6)+'-'+d.Date.substring(6,8)+' 00:00:00')) + 3 )
        .attr("y", marginTop + y( d[data.columns[column_index]] ) + tooltip_height * 0.8 )
        .text(data.columns[column_index]+': $'+d[data.columns[column_index]])
        .attr("class","tooltip");

        // "Date: ", Date
        svg.append("text")
        .attr("x", marginLeft + tooltip_margin_left + date_to_x(new Date( d.Date.substring(0,4)+'-'+d.Date.substring(4,6)+'-'+d.Date.substring(6,8)+' 00:00:00' ) ) + 3 )
        .attr("y", marginTop + y( d[data.columns[column_index]] ) + tooltip_row_height + tooltip_height * 0.8 )
        .text("Date: "+d.Date.substring(0,4)+'-'+d.Date.substring(4,6)+'-'+d.Date.substring(6,8))
        .attr("class","tooltip");

    })
        .on('mouseout', function(d){
            d3.selectAll(".tooltip").remove();
        });

        localStorage.setItem('activeDashboardView',tabName);
} //closes for loop



}); //closes d3.csv
}

function updateDashboardLeftBound(data_path) {
    d3.csv(data_path, function(error, data) {
    //d3.csv("../data/current_forecast_data.csv", function(error, data) {
      if (error) throw error;

      var input_date_string = d3.select("#msg").property("value")

  //console.log('input_date_string:'+input_date_string);

      min_date = d3.min(data, function(d){
        return new Date(input_date_string.substring(0,4)+'-'+input_date_string.substring(4,6)+'-'+input_date_string.substring(6,8))
    });


      max_date = d3.max(data, function(d){
        return new Date(d.Date.substring(0,4)+'-'+d.Date.substring(4,6)+'-'+d.Date.substring(6,8))
    });

      var date_to_x = d3.scaleTime()
      .domain([min_date, max_date])
      .range([0,width - ( marginLeft + marginRight ) - right_legend_panel_width ]);


      var y = d3.scaleLinear()
      .domain([0, plot_upper_y_bound*1.1 ])      
      .range([height - ( marginTop + marginBottom ), 0 ]);  




//assumes first column is Date, last column is Memo
      for ( let column_index = 1 ; column_index < ( data.columns.length - 1) ; column_index++ ) {


        current_plot_color = plot_color_cycle[(column_index-1) % plot_color_cycle.length ];



        svg.append("path")
        .datum(data)
        .attr("fill", "none")
        .attr('class', 'plotline')
        .attr("stroke", current_plot_color)
        .attr("stroke-width", 2)
        .attr("d", d3.line()
            .x(function(d) { return marginLeft + date_to_x(new Date(d.Date.substring(0,4)+'-'+d.Date.substring(4,6)+'-'+d.Date.substring(6,8))) })
            .y(function(d) { 

                return marginTop + y( d[data.columns[column_index]]) })
            );

    }

})}


// function getMessage() {
// d3.select("#d3").text("D3a:" + d3.select("#msg").property("value"));
// d3.select("#d3node").text("D3b:" + d3.select("#msg").node().value);
// document.getElementById("dom").innerHTML = "DOM:" + document.getElementById("msg").value;
// }


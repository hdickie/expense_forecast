scale_factor = 1/3;

width=1400 * scale_factor;
height=700 * scale_factor;

d3.select("#daylight_clock").append("svg").attr("width",width).attr("height",height);

g = d3.select("#daylight_clock").select("svg");

// background
d3.select("#daylight_clock").select("svg").append("rect")
	.attr("width",width)
	.attr("height",height)
	.attr("fill","lightgrey");
	
//plot canvas
d3.select("#daylight_clock").select("svg").append("rect")
	.attr("x",10)
	.attr("y",10)
	.attr("width",width-20)
	.attr("height",height-20)
	.attr("id","main_canvas")
	.attr("fill","white");
	
	
d3.select("#daylight_clock").select("svg").append("circle")
	.attr("cx", width/2)
	.attr("cy", height/2)
	.attr("r", height/2 - 20)
	.attr("fill","black");
	
let radius = height/2 - 20;
let PI = 3.141592653;

function draw_pie_wedge(g,x,y,radius,rotation_angle,wedge_fill_angle) {
	
	//the starting point of the arc (before rotation) will be at 0 degrees
	PI = 3.141592653;
	wedge_fill_angle_radians = wedge_fill_angle*PI/180;
	rotation_angle_radians = rotation_angle*PI/180
	
	//we first draw the wedge in standard position
	x1 = x + radius*Math.cos(rotation_angle_radians)
	y1 = y - radius*Math.sin(rotation_angle_radians);
	
	x2 = x + radius*Math.cos(wedge_fill_angle_radians + rotation_angle_radians);
	y2 = y - radius*Math.sin(wedge_fill_angle_radians + rotation_angle_radians);

	rx = radius;
	ry = radius;
	
	x_axis_rotation = 0;
	
	if ( wedge_fill_angle > 180 ){
		large_arc_flag = 1;
	} else {
		large_arc_flag = 0;
	}
	sweep_flag = 0;
	
	x2_to_origin_dx = -1*radius*Math.cos(wedge_fill_angle_radians+rotation_angle_radians);
	y2_to_origin_dy = radius*Math.sin(wedge_fill_angle_radians+rotation_angle_radians);
	origin_to_x1_dx = radius*Math.cos(rotation_angle_radians);
	origin_to_y1_dy = -1*radius*Math.sin(rotation_angle_radians);
	
	path_string = "M "+x1+" "+y1+" A "+rx+" "+ry+" "+x_axis_rotation+" "+large_arc_flag+" "+sweep_flag+" "+x2+" "+y2+" L"+ x + " " + y + " l " + origin_to_x1_dx + " " + origin_to_y1_dy + " Z"
	
	g.append('path')
	.attr('d', path_string)
	.attr("fill","grey");
}

   
function convert_HH_MM_SS_to_radians(time_string){
	values = time_string.split(':');
	
	time_index = parseInt(values[2],10) + parseInt(values[1]*60,10) + parseInt(values[0]*3600,10);
	time_factor = time_index / (59 + 59*60 + 23*3600);
	
	return time_factor*2*PI;
	
}
	
function draw_sunlight_wedge(g,x,y,radius,sunrise_HHMMSS,sunset_HHMMS){

	sunrise_radians = convert_HH_MM_SS_to_radians(sunrise_HHMMSS);
	sunset_radians = convert_HH_MM_SS_to_radians(sunset_HHMMS);

	// time goes clockwise, but trig goes counter clockwise, so we do this to make math and code easier to understand
	left_boundary_radians = sunset_radians;
	right_boundary_radians = sunrise_radians;

	left_boundary_degrees = (left_boundary_radians * 180 / PI); 
	right_boundary_degrees = (right_boundary_radians * 180 / PI); 

	left_boundary_degrees = left_boundary_degrees * -1;
	right_boundary_degrees = right_boundary_degrees * -1;

	//usually midnight is at 0 degrees, but we want 6pm at 0 degrees, so rotate by pi/2
	left_boundary_degrees = left_boundary_degrees - 90;
	right_boundary_degrees = right_boundary_degrees - 90;
	
	//given start and end angles
	//rotation and wedge
	draw_pie_wedge(g,x,y,radius,left_boundary_degrees,right_boundary_degrees - left_boundary_degrees )
}

d3.csv("../data/sun_data.csv", function(data) {
	
	let today = new Date(); 
	let dd = today.getDate(); 
	let mm = today.getMonth()+1; 

	dd = ('0'+dd).slice(-2);
	mm = ('0'+mm).slice(-2);

	let yyyy = today.getFullYear(); 
	
	let todays_date_string = yyyy+'-'+mm+'-'+dd;
	
	let current_time_string = today.getHours()+':'+today.getMinutes()+':00'
	
	var sunrise_time = 0;
	var sunset_time = 0;
    for (let i = 0; i < data.length; i++) {
		if (data[i].Date == todays_date_string){
			sunrise_time = data[i].Sunrise;
			sunset_time = data[i].Sunset;		}
	}
	
	draw_sunlight_wedge(g,width/2,height/2,radius,sunrise_time,sunset_time);
	
	time_radians = convert_HH_MM_SS_to_radians(current_time_string) + PI/2;
	
	if (time_radians < 0){
		time_radians = time_radians + 2*PI
	}
	time_radians = time_radians % (2*PI);
	
	x2 = width/2 + radius*Math.cos( time_radians );
	y2 = height/2 + radius*Math.sin( time_radians );
	
	sunrise_time_radians = convert_HH_MM_SS_to_radians(sunrise_time) + PI/2;
	//console.log('sunrise_time_radians:'+sunrise_time_radians);
	sunset_time_radians = convert_HH_MM_SS_to_radians(sunset_time) + PI/2;
	//console.log('sunset_time_radians:'+sunset_time_radians);
	
	
	if ( sunrise_time_radians <= time_radians && time_radians <= sunset_time_radians ){
		//daytime
		remaining_night = "";
		remaining_day = ((sunset_time_radians - time_radians)*24/(2*PI)).toFixed(2);
		if (remaining_day < 1) {
			remaining_day = (remaining_day*60).toFixed(0) +" min of light left";
		} else {
			remaining_day = remaining_day +" hrs of light left";
		}
		
	} else {
		remaining_day = "";
		
		if ( sunset_time_radians <= time_radians && time_radians <= 2*PI){
			//just became night time, about go over 2PI but hasnt yet
			remaining_night = (sunrise_time_radians + ( 2*PI - time_radians ))*24/(2*PI)
		} else {
			remaining_night = (sunrise_time_radians - time_radians)*24/(2*PI)
		}
		if (remaining_night < 1) {
			remaining_night = (remaining_night*60).toFixed(0) +" min of dark left";
		} else {
			remaining_night = remaining_night.toFixed(0) +" hrs of dark left";
		}
	}
	
	
	g.append("line")
	.attr("x1", width/2)
	.attr("y1", height/2)
	.attr("x2", x2)
	.attr("y2", y2)
	.attr("stroke-width","5px")
	.attr("stroke","red"); 
	
	g.append("text")
	.attr("x", width/10)
	.attr("y", 9*height/10)
	.attr("font-size",(40*scale_factor)+"px")
	.text("Dawn "+sunrise_time); 
	
	g.append("text")
	.attr("x", 7*width/10)
	.attr("y", 9*height/10)
	.attr("font-size",(40*scale_factor)+"px")
	.text("Dusk "+sunset_time); 
	
	g.append("text")
	.attr("x", width/10)
	.attr("y", 8*height/10)
	.attr("font-size",(40*scale_factor)+"px")
	.text(remaining_night); 
	
	g.append("text")
	.attr("x", 7*width/10)
	.attr("y", 8*height/10)
	.attr("font-size",(40*scale_factor)+"px")
	.text(remaining_day); 

});

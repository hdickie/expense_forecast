# Expense_Forecast

The expense_forecast module is a tool that allows anyone with a beginner understanding of python to compute future trends of their spend. Different sets of decision rules can implemented to compute long-term trends and compare the impact on milestone dates. This module allows the user to "map dollars to days", yielding answers to questions such as: "if I spend $1000 today, how much longer will it take to pay off all my loans?".

This tool is useful for:
<ul>
<li>Amortizing lifestyle costs</li>
<li>Managing impulse spending</li>
<li>Tracking a large number of financial goals</li>
</ul>

I am excited about this because it is scalable and has applications in monte carlo simulations for risk assessment.

The v2 of this project will implement time dependencies between tasks. That is, maybe you have the money but not the time. e.g. I have paid for a new passport, but I need to wait for it to come in the mail before I can go spend money in Mexico.
I think I want to use the Trello API for this, as that would allow the simulations created by this module to stay up-to-date with my project statuses automatically.
On the other hand, I think opening a port on my home internet and setting up a database server at home is a better long-term choice, and also serves the meta-purpose of this project as something to add to my portfolio.

This object-oriented approach may seem like overkill, but I have tried and failed several times to do this using only DataFrames.

Developed on a windows device so probably only works on window. I haven't checked though.

## Plans
Releases
v1.0 - MVP
v1.1 - plus Google Analytics
v2.0 - plus databases for history
v3.0 - plus BlueHost backend for daily updates
v4.0 - plus Trello for app interface
v5.0 - plus d3 for animated plots

## How to Use
1. Download the .zip from github
2. Write a script to input your values. A template is provided.
3. Run the module. report.html will be created in the same directory as the module (unless you provided a different value)

## In-Depth Tutorial
An example of this script and the output it creates are here: <a href="tutorial.html">Tutorial</a>

## Documentation
<a href="https://hdickie.github.io/expense_forecast/build/html/"/>Documentation></a>

## Contact
The best way to contact me is via LinkedIn: https://www.linkedin.com/in/humedickie/. You can also reach me at hume.dickie@live.com.

## Notes to Self
1. Microsoft SQL Server Management Studio & Azure Data Studio to run sql server and client

Website + Documentation
- Github Readme
- Sphinx Documentation
- Tutorial doc
- Professional Website
	- Portfolio
	- Internet-facing GUI for expense_forecast


## Notes to Self: Todo
Documentation
 - Move exhaustive doctests to other files
	- get doctests in other files to count for code coverage 
	
HTML
 - finalize CSS
	- organize it
# expense_forecast

This project has not had its first release.

The expense_forecast module is a tool that allows anyone with a beginner understanding of python to compute future trends of their spend. Different sets of decision rules can implemented to compute long-term trends and compare the impact on milestone dates. This module allows the user to "map dollars to days", yielding answers to questions such as: "if I spend $1000 today, how much longer will it take to pay off all my loans?".

This tool is useful for:
<ul>
<li>Amortizing lifestyle costs</li>
<li>Managing impulse spending</li>
<li>Tracking long-term financial goals</li>
</ul>

<table style="border-collapse: collapse; width: 60%; font-family: Arial, sans-serif;">
<tr>
	<th style="border: 1px solid #ddd; padding: 8px; width: 100px;">Test Suite</th>
	<th style="border: 1px solid #ddd; padding: 8px; width: 100px;"><a href="https://github.com/hdickie/expense_forecast/actions/workflows/python-app.yml">
		<img src="https://github.com/hdickie/expense_forecast/actions/workflows/python-app.yml/badge.svg" alt="Build Status">
	</a></th>
</tr>
<tr>
	<td style="border: 1px solid #ddd; padding: 8px;">Coverage</td>
	<td style="border: 1px solid #ddd; padding: 8px;"><img src="https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/hdickie/69631cca73647a817c2678cf0250a54a/raw/all_tests_coverage.json" alt="Build Status"></td>
</tr>

<tr>
	<td style="border: 1px solid #ddd; padding: 8px;">Unit Tests</td>
	<td style="border: 1px solid #ddd; padding: 8px;"><img src="https://github.com/hdickie/expense_forecast/actions/workflows/unit-tests-status-badge.yml/badge.svg" alt="Build Status"></td>
</tr>
<tr>
	<td style="border: 1px solid #ddd; padding: 8px;">Integration Tests</td>
	<td style="border: 1px solid #ddd; padding: 8px;"><img src="https://github.com/hdickie/expense_forecast/actions/workflows/integration-tests-status-badge.yml/badge.svg" alt="Build Status"></td>
</tr>
<tr>
	<td style="border: 1px solid #ddd; padding: 8px;">E2E Tests</td>
	<td style="border: 1px solid #ddd; padding: 8px;"><img src="https://github.com/hdickie/expense_forecast/actions/workflows/E2E-tests-status-badge.yml/badge.svg" alt="Build Status"></td>
</tr>
</table>                                      |

## Next steps

The repository currently has working unit tests and a CLI skeleton. Helpful next tasks are:

- stabilize `ef_cli.py` by removing hard-coded local paths and making config loading more robust
- implement the placeholder integration tests under `tests/` so they validate real forecast flows
- add a clear installation and usage section to `README.md`
- provide a small example workflow for building a forecast, running it, and generating a report
# Github Pages
<a href="https://hdickie.github.io/expense_forecast/pages/collaborate.html">Expense Forecast Toolkit</a>

## License

This project is licensed under the GNU General Public License v3.0. See the [license.txt](./license.txt) file for details.


### Notes to self
Run tests: python3 -m pytest

What This UI Is  
The UI is a PHP/Apache app.  
Apache serves PHP pages from:  
[app/php/site-contents](/Users/hume/CodeProjects/Github/expense_forecast/app/php/site-contents)  
Main entry points:  
Login page: [index.php](/Users/hume/CodeProjects/Github/expense_forecast/app/php/site-contents/index.php)  
Register page: [register.php](/Users/hume/CodeProjects/Github/expense_forecast/app/php/site-contents/register.php)  
Main app page: [expense_forecast.php](/Users/hume/CodeProjects/Github/expense_forecast/app/php/site-contents/expense_forecast.php)  
Form handlers: [php_script/](/Users/hume/CodeProjects/Github/expense_forecast/app/php/site-contents/php_script)  
There is no active Jinja/template rendering flow here. There is a tiny FastAPI stub in [src/expense_forecast/main.py](/Users/hume/CodeProjects/Github/expense_forecast/src/expense_forecast/main.py), but it only returns {"message": "Hello World"} and is not used by compose.yaml.  
How The App Works  
The big page is [expense_forecast.php](/Users/hume/CodeProjects/Github/expense_forecast/app/php/site-contents/expense_forecast.php). It renders HTML directly with embedded PHP and JS.  
UI edits go mostly here:
Layout/forms/tabs/views: [expense_forecast.php](/Users/hume/CodeProjects/Github/expense_forecast/app/php/site-contents/expense_forecast.php)  
Styling: [css/expense_forecast.css](/Users/hume/CodeProjects/Github/expense_forecast/app/php/site-contents/css/expense_forecast.css) and [css/style.css](/Users/hume/CodeProjects/Github/expense_forecast/app/php/site-contents/css/style.css)  
Plot behavior: [drawExpenseForecastPlot.js](/Users/hume/CodeProjects/Github/expense_forecast/app/php/site-contents/script/drawExpenseForecastPlot.js) and [drawCompareExpenseForecastPlot.js](/Users/hume/CodeProjects/Github/expense_forecast/app/php/site-contents/script/drawCompareExpenseForecastPlot.js)  
DB/form actions: [php_script/](/Users/hume/CodeProjects/Github/expense_forecast/app/php/site-contents/php_script)  
Forms POST to PHP scripts. Those scripts update Postgres or run Python CLI commands like:  
python3 /var/www/html/src/expense_forecast/ef_cli.py ...  
The Python writes artifacts into /var/www/html/data, which maps to:  
[app/runtime/data](/Users/hume/CodeProjects/Github/expense_forecast/app/runtime/data)  
Then PHP/JS reads those generated CSV/JSON/image/report files.  
Registration  
Register is probably not fully healthy yet.  
Path:  
[register.php](/Users/hume/CodeProjects/Github/expense_forecast/app/php/site-contents/register.php) posts to  
[create_user_account.php](/Users/hume/CodeProjects/Github/expense_forecast/app/php/site-contents/php_script/create_user_account.php)  
That inserts into public.users  
Then it includes [prepare_database_for_new_expense_forecast_user.php](/Users/hume/CodeProjects/Github/expense_forecast/app/php/site-contents/php_script/prepare_database_for_new_expense_forecast_user.php), which creates per-user DB tables.  
Likely issues:  
It tries to send email with mail(...), which probably won’t work locally.  
The registration page has stale JS calling saveToLocalStorage(store.getState()), but store does not appear defined there.  
Feedback cookie cleanup is wrong: it reads account_registration_feedback but clears login_feedback.  
The DB/user/table setup is fragile and may fail silently because most pg_query(...) calls don’t check errors.  
So: the pathway exists, but I would not trust it until we do a focused registration repair pass.  

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


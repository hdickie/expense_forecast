# TODO

## Notes

Migration notes from Codex:  
Add ignored runtime dirs and app folder structure.  
Copy Docker/PHP/init SQL files, excluding generated artifacts and old Python source.  
Update compose.yaml paths and Dockerfile dependency install.  
Add shared PHP config for DB/env values.  
Start containers and fix first-order startup issues.  
Exercise login/register and basic table editing.  
Exercise ef_cli through the UI.  
Patch schema/model mismatches as they appear.  
Add a short docs/app.md with how to run it.  
Retire expense_forecast_app.  
  
Playwright test cases:  
Create a new Forecast.  
Edit transactions.  
Run the forecast.  
Verify the report loads.  
Create a ForecastSet.  
Compare multiple scenarios.  
Export a report.  
Confirm no JavaScript errors occurred.  

My Suggested First UI Refactor
I would start with the New Forecast view only:
Convert it into a left-to-right or top-to-bottom setup flow.
Keep the existing PHP handlers for now.
Replace repeated form sections with editable tables.
Add a review panel before stage/run.

A refactor of the loan allocaiton algorthm now overallocates by a few pennies in certain cases where marginal interest for multiple loans are very close together

## Human Tasks
- Add forecast_name to IO constructor and all downstream touche
- tests for approximate case
- IOSet ???? what is this for

## LLM Tasks
 - Refactor BudgetSet to be LineItemSet and BudgetSet to be LineItem
 - Refactor BudgetItem "cadence" to "interval"
 - Update docstrings

## Roadmap
 - Benchmarks
 - Step Size
 - Investment case

<!-- TODO:GENERATED:START -->
## Generated TODOs

_Updated by `python3 scripts/update_todo.py`._

<pre>
TODO:
TODO set primary_checking_account_name ; unclear if this is still being used after Codex-powered refactors                                      - <a href="src/expense_forecast/AccountSet.py#L139">src/expense_forecast/AccountSet.py:139</a>
TODO add warnings if interval is shorter than cadence and create test                                                                           - <a href="src/expense_forecast/BudgetItem.py#L24">src/expense_forecast/BudgetItem.py:24</a>
todo this may not be best practice bc this behaves like an optional parameters                                                                  - <a href="src/expense_forecast/BudgetItem.py#L66">src/expense_forecast/BudgetItem.py:66</a>
TODO validate unique names and add test                                                                                                         - <a href="src/expense_forecast/CompositeMilestone.py#L60">src/expense_forecast/CompositeMilestone.py:60</a>
TODO implement account_set_swap_set validation                                                                                                  - <a href="src/expense_forecast/ExpenseForecastInitialConditions.py#L371">src/expense_forecast/ExpenseForecastInitialConditions.py:371</a>
TODO implement budget_set_swap_set validation                                                                                                   - <a href="src/expense_forecast/ExpenseForecastInitialConditions.py#L374">src/expense_forecast/ExpenseForecastInitialConditions.py:374</a>
TODO implement memo_rule_set_swap_set validation                                                                                                - <a href="src/expense_forecast/ExpenseForecastInitialConditions.py#L377">src/expense_forecast/ExpenseForecastInitialConditions.py:377</a>
TODO IO::init.log_stack_depth be a kwarg instead of a param w default?                                                                          - <a href="src/expense_forecast/ExpenseForecastInitialConditions.py#L385">src/expense_forecast/ExpenseForecastInitialConditions.py:385</a>
TODO fix pylance type warning for IO::initialize_from_dict                                                                                      - <a href="src/expense_forecast/ExpenseForecastInitialConditions.py#L465">src/expense_forecast/ExpenseForecastInitialConditions.py:465</a>
TODO forecast name                                                                                                                              - <a href="src/expense_forecast/ExpenseForecastInitialConditions.py#L477">src/expense_forecast/ExpenseForecastInitialConditions.py:477</a>
TODO make this conditional on a --print flag                                                                                                    - <a href="src/expense_forecast/ForecastHandler.py#L259">src/expense_forecast/ForecastHandler.py:259</a>
todo this could probably have a better name                                                                                                     - <a href="src/expense_forecast/ForecastHandler.py#L269">src/expense_forecast/ForecastHandler.py:269</a>
todo this optimization had to be removed bc of cc prepayment                                                                                    - <a href="src/expense_forecast/ForecastHandler.py#L644">src/expense_forecast/ForecastHandler.py:644</a>
todo I have seen similar methods so I think that maybe this can be refactored                                                                   - <a href="src/expense_forecast/ForecastHandler.py#L882">src/expense_forecast/ForecastHandler.py:882</a>
todo unclear if this is still wrong ; pylance type warning                                                                                      - <a href="src/expense_forecast/ForecastHandler.py#L1086">src/expense_forecast/ForecastHandler.py:1086</a>
todo this is where the error occurred                                                                                                           - <a href="src/expense_forecast/ForecastHandler.py#L5739">src/expense_forecast/ForecastHandler.py:5739</a>
TODO unsure if include_debug_columns belongs here                                                                                               - <a href="src/expense_forecast/ForecastHandler.py#L6123">src/expense_forecast/ForecastHandler.py:6123</a>
todo consider adding interest accrual to memo directives                                                                                        - <a href="src/expense_forecast/ForecastHandler.py#L6800">src/expense_forecast/ForecastHandler.py:6800</a>
todo havent tested this, but forecast_df has been _satisficed so it has all the dates                                                           - <a href="src/expense_forecast/ForecastHandler.py#L7014">src/expense_forecast/ForecastHandler.py:7014</a>
todo maybe this could be moved down? not sure                                                                                                   - <a href="src/expense_forecast/ForecastHandler.py#L7071">src/expense_forecast/ForecastHandler.py:7071</a>
todo I added deferred_df without testing if that was correct                                                                                    - <a href="src/expense_forecast/ForecastHandler.py#L7326">src/expense_forecast/ForecastHandler.py:7326</a>
todo if _satisfice fails, should deferred transactions stay deferred?                                                                           - <a href="src/expense_forecast/ForecastHandler.py#L7338">src/expense_forecast/ForecastHandler.py:7338</a>
todo draw plots                                                                                                                                 - <a href="src/expense_forecast/ForecastHandler.py#L7988">src/expense_forecast/ForecastHandler.py:7988</a>
todo composite milestones may contain some milestones that arent listed in the composite #https://github.com/hdickie/expense_forecast/issues/22 - <a href="src/expense_forecast/ForecastHandler.py#L8280">src/expense_forecast/ForecastHandler.py:8280</a>
TODO list is not the best type for this                                                                                                         - <a href="src/expense_forecast/ForecastHandler.py#L8382">src/expense_forecast/ForecastHandler.py:8382</a>
todo income needs to not be in memo. this is a known vulnerability bc of this right here #https://github.com/hdickie/expense_forecast/issues/19 - <a href="src/expense_forecast/ForecastHandler.py#L8623">src/expense_forecast/ForecastHandler.py:8623</a>
todo date range match for forecastset does not happen in JSON bc json.load just worked                                                          - <a href="src/expense_forecast/ForecastSetInitialConditions.py#L69">src/expense_forecast/ForecastSetInitialConditions.py:69</a>
todo check for overwrites up front to prevent duplicated work                                                                                   - <a href="src/expense_forecast/ForecastSetInitialConditions.py#L307">src/expense_forecast/ForecastSetInitialConditions.py:307</a>
TODO implement MemoRuleSet::__str__                                                                                                             - <a href="src/expense_forecast/MemoRuleSet.py#L58">src/expense_forecast/MemoRuleSet.py:58</a>
TODO implement MemoRuleSet::__repr__                                                                                                            - <a href="src/expense_forecast/MemoRuleSet.py#L61">src/expense_forecast/MemoRuleSet.py:61</a>
todo                                                                                                                                            - <a href="src/expense_forecast/MemoRuleSet.py#L105">src/expense_forecast/MemoRuleSet.py:105</a>
todo rename?                                                                                                                                    - <a href="src/expense_forecast/MilestoneSet.py#L195">src/expense_forecast/MilestoneSet.py:195</a>
todo rename?                                                                                                                                    - <a href="src/expense_forecast/MilestoneSet.py#L225">src/expense_forecast/MilestoneSet.py:225</a>
todo rename?                                                                                                                                    - <a href="src/expense_forecast/MilestoneSet.py#L245">src/expense_forecast/MilestoneSet.py:245</a>
TODO add to self.choices                                                                                                                        - <a href="src/expense_forecast/ScenarioDimension.py#L39">src/expense_forecast/ScenarioDimension.py:39</a>
TODO conceivably I would need dropChoice, but not rn so tabling it for now                                                                      - <a href="src/expense_forecast/ScenarioDimension.py#L51">src/expense_forecast/ScenarioDimension.py:51</a>
TODO I will need some version of these eventually                                                                                               - <a href="src/expense_forecast/ScenarioSpace.py#L42">src/expense_forecast/ScenarioSpace.py:42</a>
TODO a methos to add exceptions- like, only keep these combinations of labels or drop this specific one                                         - <a href="src/expense_forecast/ScenarioSpace.py#L75">src/expense_forecast/ScenarioSpace.py:75</a>
todo this may more appropriate near some code for output or logging                                                                             - <a href="src/expense_forecast/SimulationStepper.py#L8">src/expense_forecast/SimulationStepper.py:8</a>
todo satisfice failed flag                                                                                                                      - <a href="src/expense_forecast/ef_cli.py#L87">src/expense_forecast/ef_cli.py:87</a>
todo not sure if this is correct                                                                                                                - <a href="src/expense_forecast/ef_cli.py#L122">src/expense_forecast/ef_cli.py:122</a>
todo satisfice failed flag                                                                                                                      - <a href="src/expense_forecast/ef_cli.py#L139">src/expense_forecast/ef_cli.py:139</a>
TODO there has to be a better way to validate date formats, but this works for now                                                              - <a href="src/expense_forecast/ef_cli.py#L377">src/expense_forecast/ef_cli.py:377</a>
todo modify forecast_database_details based on forecast table existence                                                                         - <a href="src/expense_forecast/ef_cli.py#L581">src/expense_forecast/ef_cli.py:581</a>
todo args.filename could be a path                                                                                                              - <a href="src/expense_forecast/ef_cli.py#L592">src/expense_forecast/ef_cli.py:592</a>
TODO these should be uncommented eventually                                                                                                     - <a href="src/expense_forecast/ef_cli.py#L656">src/expense_forecast/ef_cli.py:656</a>
todo this is not writing forecast_df and indeed some of the other data frames as intended                                                       - <a href="src/expense_forecast/ef_cli.py#L694">src/expense_forecast/ef_cli.py:694</a>
todo this would ovwrwrite our initial state!                                                                                                    - <a href="src/expense_forecast/ef_cli.py#L757">src/expense_forecast/ef_cli.py:757</a>
todo delete row from forecast stage                                                                                                             - <a href="src/expense_forecast/ef_cli.py#L818">src/expense_forecast/ef_cli.py:818</a>
todo also write Set JSON and report. i think &#x27;write child reports&#x27; could be a parameter                                                         - <a href="src/expense_forecast/ef_cli.py#L874">src/expense_forecast/ef_cli.py:874</a>
todo milestone tables                                                                                                                           - <a href="src/expense_forecast/ef_cli.py#L1098">src/expense_forecast/ef_cli.py:1098</a>
todo the logic in this block assumes the forecast is run, bc even if it did we don&#x27;t plan on using it                                           - <a href="src/expense_forecast/ef_cli.py#L1106">src/expense_forecast/ef_cli.py:1106</a>
todo account milestone set                                                                                                                      - <a href="src/expense_forecast/ef_cli.py#L1328">src/expense_forecast/ef_cli.py:1328</a>
todo memo milestone set                                                                                                                         - <a href="src/expense_forecast/ef_cli.py#L1329">src/expense_forecast/ef_cli.py:1329</a>
todo composite milestone set                                                                                                                    - <a href="src/expense_forecast/ef_cli.py#L1330">src/expense_forecast/ef_cli.py:1330</a>
todo insert into a forecastset table                                                                                                            - <a href="src/expense_forecast/ef_cli.py#L1332">src/expense_forecast/ef_cli.py:1332</a>
todo refactor https://github.com/hdickie/expense_forecast/issues/46                                                                             - <a href="src/expense_forecast/main.py#L339">src/expense_forecast/main.py:339</a>
todo refactor https://github.com/hdickie/expense_forecast/issues/46                                                                             - <a href="src/expense_forecast/main.py#L340">src/expense_forecast/main.py:340</a>
todo refactor https://github.com/hdickie/expense_forecast/issues/46                                                                             - <a href="src/expense_forecast/main.py#L351">src/expense_forecast/main.py:351</a>
TODO not sure                                                                                                                                   - <a href="src/expense_forecast/scratch.py#L307">src/expense_forecast/scratch.py:307</a>
TODO not sure                                                                                                                                   - <a href="src/expense_forecast/scratch.py#L316">src/expense_forecast/scratch.py:316</a>
TODO not sure                                                                                                                                   - <a href="src/expense_forecast/scratch.py#L325">src/expense_forecast/scratch.py:325</a>
TODO not sure                                                                                                                                   - <a href="src/expense_forecast/scratch.py#L334">src/expense_forecast/scratch.py:334</a>
TODO not sure                                                                                                                                   - <a href="src/expense_forecast/scratch.py#L343">src/expense_forecast/scratch.py:343</a>
TODO this could take kwargs                                                                                                                     - <a href="src/expense_forecast/scratch.py#L525">src/expense_forecast/scratch.py:525</a>
TODO maybe increase cost of gas ?                                                                                                               - <a href="src/expense_forecast/scratch.py#L536">src/expense_forecast/scratch.py:536</a>
TODO maybe increase cost of gas ?                                                                                                               - <a href="src/expense_forecast/scratch.py#L678">src/expense_forecast/scratch.py:678</a>
TODO                                                                                                                                            - <a href="src/expense_forecast/scratch.py#L679">src/expense_forecast/scratch.py:679</a>
TODO                                                                                                                                            - <a href="src/expense_forecast/scratch.py#L680">src/expense_forecast/scratch.py:680</a>
TODO                                                                                                                                            - <a href="src/expense_forecast/scratch.py#L682">src/expense_forecast/scratch.py:682</a>
TODO                                                                                                                                            - <a href="src/expense_forecast/scratch.py#L683">src/expense_forecast/scratch.py:683</a>
TODO                                                                                                                                            - <a href="src/expense_forecast/scratch.py#L684">src/expense_forecast/scratch.py:684</a>
TODO                                                                                                                                            - <a href="src/expense_forecast/scratch.py#L685">src/expense_forecast/scratch.py:685</a>
TODO                                                                                                                                            - <a href="src/expense_forecast/scratch.py#L693">src/expense_forecast/scratch.py:693</a>
TODO                                                                                                                                            - <a href="src/expense_forecast/scratch.py#L694">src/expense_forecast/scratch.py:694</a>
TODO                                                                                                                                            - <a href="src/expense_forecast/scratch.py#L695">src/expense_forecast/scratch.py:695</a>
TODO                                                                                                                                            - <a href="src/expense_forecast/scratch.py#L696">src/expense_forecast/scratch.py:696</a>
TODO                                                                                                                                            - <a href="src/expense_forecast/scratch.py#L697">src/expense_forecast/scratch.py:697</a>
TODO                                                                                                                                            - <a href="src/expense_forecast/scratch.py#L698">src/expense_forecast/scratch.py:698</a>
TODO                                                                                                                                            - <a href="src/expense_forecast/scratch.py#L735">src/expense_forecast/scratch.py:735</a>
TODO                                                                                                                                            - <a href="src/expense_forecast/scratch.py#L758">src/expense_forecast/scratch.py:758</a>
TODO this method is just for development, eventually runForecast will implement this                                                            - <a href="src/expense_forecast/scratch.py#L762">src/expense_forecast/scratch.py:762</a>
TODO in order to do these, I need to be able to stop mid way at a milestone and start a new forecsast                                           - <a href="src/expense_forecast/scratch.py#L790">src/expense_forecast/scratch.py:790</a>
TODO MS                                                                                                                                         - <a href="src/expense_forecast/scratch.py#L793">src/expense_forecast/scratch.py:793</a>
TODO ForecastStateSnapshot                                                                                                                      - <a href="src/expense_forecast/scratch.py#L796">src/expense_forecast/scratch.py:796</a>
TODO MilestoneTriggeredForecastTransition                                                                                                       - <a href="src/expense_forecast/scratch.py#L797">src/expense_forecast/scratch.py:797</a>
TODO list the classes                                                                                                                           - <a href="src/expense_forecast/scratch.py#L806">src/expense_forecast/scratch.py:806</a>
todo is this true?                                                                                                                              - <a href="src/expense_forecast/scratch10.py#L14">src/expense_forecast/scratch10.py:14</a>
todo implement                                                                                                                                  - <a href="test_results.txt#L349">test_results.txt:349</a>
todo idk if this is necessary                                                                                                                   - <a href="test_results.txt#L2041">test_results.txt:2041</a>
todo maybe this could be moved down? not sure                                                                                                   - <a href="test_results.txt#L2046">test_results.txt:2046</a>
todo not sure if this is necessary                                                                                                              - <a href="test_results.txt#L2049">test_results.txt:2049</a>
todo idk if this is necessary                                                                                                                   - <a href="test_results.txt#L2940">test_results.txt:2940</a>
todo maybe this could be moved down? not sure                                                                                                   - <a href="test_results.txt#L2945">test_results.txt:2945</a>
todo not sure if this is necessary                                                                                                              - <a href="test_results.txt#L2948">test_results.txt:2948</a>
todo idk if this is necessary                                                                                                                   - <a href="test_results.txt#L4049">test_results.txt:4049</a>
todo maybe this could be moved down? not sure                                                                                                   - <a href="test_results.txt#L4054">test_results.txt:4054</a>
todo not sure if this is necessary                                                                                                              - <a href="test_results.txt#L4057">test_results.txt:4057</a>
todo idk if this is necessary                                                                                                                   - <a href="test_results.txt#L4979">test_results.txt:4979</a>
todo maybe this could be moved down? not sure                                                                                                   - <a href="test_results.txt#L4984">test_results.txt:4984</a>
todo not sure if this is necessary                                                                                                              - <a href="test_results.txt#L4987">test_results.txt:4987</a>
todo idk if this is necessary                                                                                                                   - <a href="test_results.txt#L5701">test_results.txt:5701</a>
todo maybe this could be moved down? not sure                                                                                                   - <a href="test_results.txt#L5706">test_results.txt:5706</a>
todo not sure if this is necessary                                                                                                              - <a href="test_results.txt#L5709">test_results.txt:5709</a>
TODO old                                                                                                                                        - <a href="test_results.txt#L6351">test_results.txt:6351</a>
TODO was this supposed to go somewhere ?                                                                                                        - <a href="test_results.txt#L6421">test_results.txt:6421</a>
TODO log_in_color                                                                                                                               - <a href="tests/ExpenseForecast/unit/test_ExpenseForecast__unit_test.py#L416">tests/ExpenseForecast/unit/test_ExpenseForecast__unit_test.py:416</a>
todo use log methods                                                                                                                            - <a href="tests/ExpenseForecast/unit/test_ExpenseForecast__unit_test.py#L534">tests/ExpenseForecast/unit/test_ExpenseForecast__unit_test.py:534</a>
TODO an error here bc debug columns still coming through when they shouldn&#x27;t                                                                    - <a href="tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py#L279">tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py:279</a>
TODO an error here bc debug columns still coming through when they shouldn&#x27;t                                                                    - <a href="tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py#L450">tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py:450</a>
TODO manual review                                                                                                                              - <a href="tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py#L1097">tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py:1097</a>
TODO manual review                                                                                                                              - <a href="tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py#L1119">tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py:1119</a>
TODO manual review                                                                                                                              - <a href="tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py#L1141">tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py:1141</a>
TODO manual review                                                                                                                              - <a href="tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py#L1163">tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py:1163</a>
TODO manual review                                                                                                                              - <a href="tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py#L1185">tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py:1185</a>
TODO manual review                                                                                                                              - <a href="tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py#L1207">tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py:1207</a>
TODO manual review                                                                                                                              - <a href="tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py#L1229">tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py:1229</a>
TODO manual review                                                                                                                              - <a href="tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py#L1253">tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py:1253</a>
TODO manual review                                                                                                                              - <a href="tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py#L1277">tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py:1277</a>
TODO manual review                                                                                                                              - <a href="tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py#L1301">tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py:1301</a>
TODO manual review                                                                                                                              - <a href="tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py#L1325">tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py:1325</a>
TODO manual review                                                                                                                              - <a href="tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py#L1349">tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py:1349</a>
TODO manual review                                                                                                                              - <a href="tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py#L1373">tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py:1373</a>
TODO manual review                                                                                                                              - <a href="tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py#L1465">tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py:1465</a>
TODO manual review                                                                                                                              - <a href="tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py#L1493">tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py:1493</a>
TODO manual review                                                                                                                              - <a href="tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py#L1521">tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py:1521</a>
TODO manual review                                                                                                                              - <a href="tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py#L1549">tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py:1549</a>
TODO manual review                                                                                                                              - <a href="tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py#L1577">tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py:1577</a>
TODO manual review                                                                                                                              - <a href="tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py#L1605">tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py:1605</a>
TODO Savings / Investment Account                                                                                                               - <a href="tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py#L1678">tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py:1678</a>
TODO assert final values, and shape of final data frames                                                                                        - <a href="tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py#L1783">tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py:1783</a>
todo what should we do here?                                                                                                                    - <a href="tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py#L2146">tests/ForecastHandler/integration/test_ForecastHandler__integration_test.py:2146</a>
todo make this different from pervious test case                                                                                                - <a href="tests/ForecastSet/unit/test_ForecastSet__unit_test.py#L42">tests/ForecastSet/unit/test_ForecastSet__unit_test.py:42</a>
TODO this could be pared down to a generate-report-only test                                                                                    - <a href="tests/_e2e/test_E2E.py#L84">tests/_e2e/test_E2E.py:84</a>
TODO not sure                                                                                                                                   - <a href="tests/_e2e/test_E2E.py#L205">tests/_e2e/test_E2E.py:205</a>
TODO not sure                                                                                                                                   - <a href="tests/_e2e/test_E2E.py#L215">tests/_e2e/test_E2E.py:215</a>
TODO not sure                                                                                                                                   - <a href="tests/_e2e/test_E2E.py#L225">tests/_e2e/test_E2E.py:225</a>
TODO not sure                                                                                                                                   - <a href="tests/_e2e/test_E2E.py#L235">tests/_e2e/test_E2E.py:235</a>
TODO not sure                                                                                                                                   - <a href="tests/_e2e/test_E2E.py#L245">tests/_e2e/test_E2E.py:245</a>
todo should these be fixtures?                                                                                                                  - <a href="tests/account/unit/test_AccountSet__unit_test.py#L246">tests/account/unit/test_AccountSet__unit_test.py:246</a>
todo get rid of these or make them real                                                                                                         - <a href="tests/account/unit/test_AccountSet__unit_test.py#L1672">tests/account/unit/test_AccountSet__unit_test.py:1672</a>
TODO implement a test case to try and create multiple loans with the same name                                                                  - <a href="tests/account/unit/test_AccountSet__unit_test.py#L1718">tests/account/unit/test_AccountSet__unit_test.py:1718</a>
TODO implement test_MilestoneSet_AccountMilestone_summary_column                                                                                - <a href="tests/milestone/unit/test_AccountMilestone__unit_test.py#L33">tests/milestone/unit/test_AccountMilestone__unit_test.py:33</a>

TODO DEFER:
TODO DEFER implement required kwargs in createAccount for investment case                                                                       - <a href="src/expense_forecast/AccountSet.py#L187">src/expense_forecast/AccountSet.py:187</a>
TODO DEFER implement createAccount branch for investment case                                                                                   - <a href="src/expense_forecast/AccountSet.py#L248">src/expense_forecast/AccountSet.py:248</a>
TODO DEFER implement createInvestmentAccount                                                                                                    - <a href="src/expense_forecast/AccountSet.py#L364">src/expense_forecast/AccountSet.py:364</a>
TODO DEFER implement IO::__eq__                                                                                                                 - <a href="src/expense_forecast/ExpenseForecastInitialConditions.py#L227">src/expense_forecast/ExpenseForecastInitialConditions.py:227</a>
TODO DEFER implement IO::__ne__                                                                                                                 - <a href="src/expense_forecast/ExpenseForecastInitialConditions.py#L230">src/expense_forecast/ExpenseForecastInitialConditions.py:230</a>
TODO DEFER implement IO::__hash__ ; unclear on the purpose of this ?                                                                            - <a href="src/expense_forecast/ExpenseForecastInitialConditions.py#L233">src/expense_forecast/ExpenseForecastInitialConditions.py:233</a>
TODO DEFER implement IO::__str__                                                                                                                - <a href="src/expense_forecast/ExpenseForecastInitialConditions.py#L436">src/expense_forecast/ExpenseForecastInitialConditions.py:436</a>
TODO DEFER implement IO::__repr__                                                                                                               - <a href="src/expense_forecast/ExpenseForecastInitialConditions.py#L439">src/expense_forecast/ExpenseForecastInitialConditions.py:439</a>
TODO DEFER implement ExpenseForecastResult __ne__                                                                                               - <a href="src/expense_forecast/ExpenseForecastResult.py#L50">src/expense_forecast/ExpenseForecastResult.py:50</a>
TODO DEFER implement ExpenseForecastResult __hash__ ; unclear on the purpose of this- LLM-generated                                             - <a href="src/expense_forecast/ExpenseForecastResult.py#L53">src/expense_forecast/ExpenseForecastResult.py:53</a>
TODO DEFER implement R::__str__                                                                                                                 - <a href="src/expense_forecast/ExpenseForecastResult.py#L91">src/expense_forecast/ExpenseForecastResult.py:91</a>
TODO DEFER implement R::__repr__                                                                                                                - <a href="src/expense_forecast/ExpenseForecastResult.py#L94">src/expense_forecast/ExpenseForecastResult.py:94</a>

TODO OPTIMIZATION:
TODO OPTIMIZATION copy may not be needed here?                                                                                                  - <a href="src/expense_forecast/ForecastHandler.py#L188">src/expense_forecast/ForecastHandler.py:188</a>
</pre>
<!-- TODO:GENERATED:END -->

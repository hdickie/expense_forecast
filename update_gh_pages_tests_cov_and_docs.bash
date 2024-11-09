#!/bin/bash

# equivalent to running make script in the docs folder
sphinx-build -M html docs docs/_build

cp -R docs/_build/html/* pages/docs/
coverage run -m pytest --junitxml=all_test_results.xml
junit2html all_test_coverage.xml all_test_results.html
cp all_test_results.html pages/test_results/all_test_results.html
coverage html
cp -R htmlcov/* pages/coverage/
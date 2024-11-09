#!/bin/bash

# todo i need to get the args and directory structure right for this
# currently just running make html in docs/ in the terminal works 
#sphinx-build -M html sourcedir outputdir

cp -R docs/_build/html/* pages/docs/

# assume this was already run:
coverage run -m pytest --junitxml=all_test_results.xml
junit2html all_test_coverage.xml all_test_results.html
cp all_test_results.html pages/test_results/all_test_results.html

coverage html
cp -R htmlcov/* pages/coverage/
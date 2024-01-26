#!/usr/bin/env python
# Thanks to opie4624 from Github:  https://gist.github.com/opie4624/3896526

# import modules used here -- sys is a very standard one
import sys, argparse, logging
import ExpenseForecast

# Gather our code in a main() function
def main(args, loglevel):
    logging.basicConfig(format="%(levelname)s: %(message)s", level=loglevel)

    if args.output_directory is None:
        output_dir = './'
    else:
        output_dir = args.output_directory


    E = ExpenseForecast.initialize_from_json_file(args.input_path)[0]
    E.runForecast()
    E.appendSummaryLines()
    E.writeToJSONFile(output_dir)

    logging.info("Input: %s" % args.input_path)
    logging.info("Output directory: %s" % args.output_directory)


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Runs a Forecast or Forecast set and displays a progress bar.",
        epilog="As an alternative to the commandline, params can be placed in a file, one per line, and specified on the commandline like '%(prog)s @params.conf'.",
        fromfile_prefix_chars='@')
    parser.add_argument(
        "-i",
        "--input_path",
        help="File path of Forecast or ForecastSet JSON file to run",
        action="store")
    parser.add_argument(
        "-o",
        "--output_directory",
        help="Output directory for JSON and HTML documents to be output.",
        action="store")
    parser.add_argument(
        "-v",
        "--verbose",
        help="increase output verbosity",
        action="store_true")
    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.WARNING

    main(args, loglevel)
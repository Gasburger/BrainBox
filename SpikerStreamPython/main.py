"""Program that can stream in either audio input or SpikerBox input."""

# Standard modules
import argparse
import sys
from typing import List

# Internal modules
from input_stream import *
from plotter import *


def main(args: List = sys.argv[1:]):
    """Main entry point.

    Parameters
    ----------
    args : List
        unparsed command line arguments. Default value is sys.argv.
    """
    # Parse command line arguments
    parsed_args = _parse_args(args)

    # Create input stream
    input_stream = None
    if parsed_args.stream_type == "spikerbox":
        input_stream = SpikerStream(parsed_args.serial_port, chunk=parsed_args.chunk_size)
    elif parsed_args.stream_type == "audio":
        input_stream = AudioStream()

    # Initialise plotter
    plotter = None
    if parsed_args.plot_type == "matplotlib":
        plotter = PyPlotter(input_stream, input_stream.array_size)
    elif parsed_args.plot_type == "pyqtgraph":
        plotter = QtPlotter(input_stream, input_stream.array_size)

    # Start plotting
    plotter.start()


def _parse_args(args: List) -> argparse.Namespace:
    """Parses command line arguments.

    Parameters
    ----------
    args : List
        unparsed command line arguments

    Returns
    -------
    args : argparse.Namespace
        parsed command line arguments
    """

    parser = argparse.ArgumentParser(
        description="This CLI program is used to test out the SpikerStream interface."
    )

    parser.add_argument(
        "-p", "--p", "-plot", "--plot",
        choices=["matplotlib", "pyqtgraph"],
        default="matplotlib",
        help="The plotting library.",
        dest="plot_type"
    )

    parser.add_argument(
        "-i", "--i", "-input", "--input",
        choices=["spikerbox", "audio"],
        default="audio",
        help="The input stream.",
        dest="stream_type"
    )

    parser.add_argument(
        "-s", "--s", "-serialport", "--serialport",
        nargs="?",
        default="COM1",
        help="The serial port the SpikerBox is attached to.",
        dest="serial_port"
    )

    parser.add_argument(
        "-c", "--c", "-chunk", "--chunk",
        nargs="?",
        default=10000,
        help="The chunk size when using the SpikerBox stream. 20,000 = 1 second.",
        dest="chunk_size"
    )

    return parser.parse_args(args)


if __name__ == "__main__":
    main()

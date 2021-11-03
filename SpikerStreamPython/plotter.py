"""Plotting interfaces for the two input streams."""


# Standard modules
import sys
import time
from typing import Optional

# External modules
# Pyplot backend
import matplotlib.pyplot as plt
import numpy as np
from numpy.core.records import array

# PyQtGraph backend
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui

# Internal modules
from input_stream import InputStream  # For type hints


class Plotter:
    """Plotter interface."""

    def __init__(self, input_stream: InputStream):
        """Initialise interface with an input stream.

        Implement for each class using the interface.
        """
        pass

    def start(self) -> None:
        """Starts plotting the input stream.

        Implement for each class using the interface.
        """
        pass


class PyPlotter(Plotter):
    """Plotter that uses pyplot from matplotlib."""

    def __init__(self, input_stream: InputStream, array_size: Optional[int]):
        """Initialises an instance of PyPlotter given an input stream.

        Parameters
        ----------
        input_stream : InputStream
            input stream either an AudioStream or a SpikerStream.
        """
        self.input_stream = input_stream
        # Input buffer size
        chunk = self.input_stream.chunk

        # Create matplotlib figure and axes
        self.fig, (ax1) = plt.subplots(1, figsize=(15, 4))
        self.fig.canvas.mpl_connect("button_press_event", self.on_click)

        # Set array size
        if array_size is None:
            array_size = 2 * chunk

        # Create a line object with random data as a placeholder
        x = np.arange(0, array_size, 1)
        self.line, = ax1.plot(x, np.random.rand(array_size), "-", lw=2)

        # Format waveform axes
        ax1.set_title("Waveform")
        ax1.set_xlabel("samples")
        ax1.set_ylabel("volume")
        ax1.set_ylim(0, 255)
        ax1.set_xlim(0, array_size)
        plt.setp(
            ax1, yticks=[0, 128, 255],
            xticks=[0, chunk, array_size],
        )

        # Show axes
        fig_manager = plt.get_current_fig_manager()
        # Set window size
        fig_manager.window.setGeometry(5, 120, 1910, 1070)
        plt.show(block=False)

        # Pause flag
        self.pause = False

    def start(self) -> None:
        """Starts plotting the input stream."""
        # To track the FPS
        frame_count = 0
        start_time = time.time()

        while True and plt.fignum_exists(self.fig.number):
            if not self.pause:
                # Read from the input stream
                data = self.input_stream.update()
                # Update the line's data
                self.line.set_ydata(data)

                # Update figure canvas
                self.fig.canvas.draw()
                self.fig.canvas.flush_events()
                frame_count += 1
            else:
                break
        # Diagnostics: FPS
        framerate = frame_count / (time.time() - start_time)
        print("Average frame rate = {:.0f} FPS".format(framerate))

        # Stop the program
        self.stop()

    def stop(self) -> None:
        """Stops the program by closing the input stream."""
        self.input_stream.close()

    def on_click(self, _event) -> None:
        """Pause the stream to exit."""
        self.pause = True


class QtPlotter(Plotter):
    """Plotter that uses PyQtGraph."""

    def __init__(self, input_stream: InputStream, array_size: Optional[int]):
        """Initialises an instance of QtPlotter given an input stream.

        Parameters
        ----------
        input_stream : InputStream
            input stream either an AudioStream or a SpikerStream.
        """
        self.input_stream = input_stream
        # Input buffer size
        chunk = self.input_stream.chunk

        # PyQtGraph initialisation
        pg.setConfigOptions(antialias=True)
        self.app = QtGui.QApplication(sys.argv)
        self.win = pg.GraphicsWindow(title="Waveform viewer")
        self.win.setWindowTitle("Waveform viewer")
        self.win.setGeometry(5, 115, 1910, 1061)

        # Format x axis
        waveform_xlabels = [(0, "0"), (2048, "2048"), (4096, "4096")]
        waveform_xaxis = pg.AxisItem(orientation="bottom")
        waveform_xaxis.setTicks([waveform_xlabels])

        # Format y axis
        waveform_ylabels = [(0, "0"), (127, "128"), (255, "255")]
        waveform_yaxis = pg.AxisItem(orientation="left")
        waveform_yaxis.setTicks([waveform_ylabels])

        # Add waveform plot
        self.waveform = self.win.addPlot(
            title="WAVEFORM", row=1, col=1, axisItems={"bottom": waveform_xaxis, "left": waveform_yaxis},
        )

        if array_size is None:
            array_size = 2 * chunk

        # Initialise plot
        self.traces = self.waveform.plot(pen="c", width=3)
        self.waveform.setYRange(-3*550, 3*550, padding=0)
        self.waveform.setXRange(0, array_size, padding=0.005)

        self.wave_x = np.arange(0, array_size, 1)

    def start(self) -> None:
        """Starts plotting the input stream."""
        # Start the PyQtGraph application
        timer = QtCore.QTimer()
        # Connect the `update` method to the timer
        timer.timeout.connect(lambda: 0)
        timer.start(20)

        if (sys.flags.interactive != 1) or not hasattr(QtCore, "PYQT_VERSION"):
            QtGui.QApplication.instance().exec_()

    def update(self) -> None:
        """Reads the input stream."""
        temp = self.input_stream.update()
        self.traces.setData(self.wave_x, temp)

# Import necessary modules
import sys  # System-specific parameters and functions
from os import path  # Functions to manipulate file paths
import numpy as np  # Numerical operations library
import pandas as pd
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import *  # PyQt6 GUI components
from PyQt6.QtCore import *  # Core PyQt6 classes
from PyQt6.uic import loadUiType
import pyqtgraph as pg
from PyQt6.QtGui import QKeySequence, QShortcut
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from PyQt6.QtGui import QKeySequence
import pickle
from PyQt6.QtGui import QPixmap



# Load the UI file (returns class types for UI and base class)
FORM_CLASS, _ = loadUiType(path.join(path.dirname(__file__), "design.ui"))

class MainApp(QMainWindow, FORM_CLASS):
    # Initialization method
    def __init__(self, parent=None):
        super(MainApp, self).__init__(parent)
        QMainWindow.__init__(self)

        # Load and set up UI defined in mainwindow-2.ui
        self.setupUi(self)
        self.setWindowTitle("Multi-Port, Multi-Channel Signal Viewer")

        # Create PlotWidgets for graphs
        self.plot_widget1 = pg.PlotWidget()
        self.plot_widget2 = pg.PlotWidget()
        self.graph1Layout.addWidget(self.plot_widget1)
        self.graph2Layout.addWidget(self.plot_widget2)

        # Initialize PyQtGraph plots
        self.init_pyqtgraph1()
        self.init_pyqtgraph2()

        self.graph1HorizontalScroller.setEnabled(False)
        self.graph1HorizontalScroller.setValue(self.graph1HorizontalScroller.maximum())

        self.graph2HorizontalScroller.setEnabled(False)
        self.graph2HorizontalScroller.setValue(self.graph2HorizontalScroller.maximum())

        self.cineSpeedScoller.setValue(50)
        self.cineSpeedScoller_2.setValue(50)
        self.update_interval_ms = 200  # Interval for signal updates in milliseconds

        # For graph 1
        self.signal_data_graph1 = []
        self.is_playing_graph1 = False
        self.current_index_graph1 = 0
        self.play_state_graph1 = False
        self.zoom_factor_graph1 = 1.0
        self.playback_speed_graph1 = 1.0
        self.update_interval_graph1 = 300

        # For graph 2
        self.signal_data_graph2 = []
        self.is_playing_graph2 = False
        self.current_index_graph2 = 0
        self.play_state_graph2 = False
        self.zoom_factor_graph2 = 1.0
        self.playback_speed_graph2 = 1.0
        self.update_interval_graph2 = 300

        # Zooming
        self.zoom_in_presses = 0
        self.zoom_out_presses = 0
        self.zoom_in_presses2 = 0
        self.zoom_out_presses2 = 0
        self.previous_slider_value_scroller1 = 100
        self.previous_slider_value_scroller2 = 100
        self.right_limit_graph1 = 0
        self.right_limit_graph2 = 0

        # Initialize variables for selected channels and graph states
        self.lastSelectedComboBox = None  # Keeps track of the last selected combo box. Initialized to None.
        self.graph1Files = []  # List to store file paths for graph 1
        self.graph2Files = []  # List to store file paths for graph 2
        self.currentGraph = None  # Start with no default graph selected
        self.graph1ChannelNames = []  # List to store channel names for graph 1
        self.graph2ChannelNames = []  # List to store channel names for graph 2
        self.graph1ChannelMapping = {}  # Dictionary to store mapping for graph 1 (channel name to file path)
        self.graph2ChannelMapping = {}  # Dictionary to store mapping for graph 2 (channel name to file path)
        self.hidden_channels_graph1 = []  # List to store hidden channels for graph 1
        self.hidden_channels_graph2 = []  # List to store hidden channels for graph 2
        self.checkbox_states_graph1 = {}
        self.checkbox_states_graph2 = {}
        self.graph1Statistics = {}  # Container for graph 1 statistics
        self.graph2Statistics = {}  # Container for graph 2 statistics
        self.graph1_images = []  # Container for images of graph1
        self.graph2_images = []  # Container for images of graph2

        # Connect GUI elements to methods
        self.channelsComboBox.setCurrentIndex(-1)
        self.browseButton.clicked.connect(self.open_file)
        self.graph1Radio.toggled.connect(lambda: self.updateCurrentGraph(1))
        self.graph2Radio.toggled.connect(lambda: self.updateCurrentGraph(2))
        self.channelsComboBox.currentIndexChanged.connect(self.onChannelSelectionChanged)
        self.editChannelNameButton.clicked.connect(self.editChannelNameButtonClicked)
        self.play_pauseButton.clicked.connect(self.toggle_play_pause_signal_graph1)
        self.play_pauseButton_2.clicked.connect(self.toggle_play_pause_signal_graph2)
        self.rewindButton.clicked.connect(self.rewind_signal_graph1)
        self.rewindButton_2.clicked.connect(self.rewind_signal_graph2)
        self.zoomInButton.clicked.connect(self.zoom_in_signal_graph_1)
        self.zoomInButton_2.clicked.connect(self.zoom_in_signal_graph_2)
        self.zoomOutButton.clicked.connect(self.zoom_out_signal_graph1)
        self.zoomOutButton_2.clicked.connect(self.zoom_out_signal_graph2)
        self.selectChannelColorButton.clicked.connect(self.select_channel_color)
        self.graph1HorizontalScroller.valueChanged.connect(self.horizontal_scroll_graph1)
        self.graph2HorizontalScroller.valueChanged.connect(self.horizontal_scroll_graph2)
        self.hideChannelCheckBox.stateChanged.connect(self.hide_channel)
        self.cineSpeedScoller.valueChanged.connect(self.update_playback_speed_graph1)
        self.cineSpeedScoller_2.valueChanged.connect(self.update_playback_speed_graph2)
        self.pdfButton.clicked.connect(self.exportPDF)
        self.linkgraphsCheckbox.stateChanged.connect(self.link_graphs)
        self.channelsComboBox.currentIndexChanged.connect(self.update_legend_for_current_channel)
        self.snapShotButton.clicked.connect(self.generateSnapshots)
        # Connect the move functions to the respective buttons in your __init__ method
        # self.moveToGraph1Button.clicked.connect(self.moveSignalFromGraph)
        # self.moveToGraph2Button.clicked.connect(self.moveSignalFromGraph)
        self.moveToGraph1Button.clicked.connect(self.move_channel_to_other_graph)
        self.moveToGraph2Button.clicked.connect(self.move_channel_to_other_graph)



        # Define keyboard shortcuts for zooming in and out
        # zoom_in_shortcut = QShortcut(QKeySequence("+"), self)
        # zoom_out_shortcut = QShortcut(QKeySequence("-"), self)
        pause_resume_shortcut = QShortcut(QKeySequence(chr(32)), self)
        browse_shortcut = QShortcut(QKeySequence('B'), self)
        select_radio1 = QShortcut(QKeySequence('1'), self)
        select_radio2 = QShortcut(QKeySequence('2'), self)
        hide_shortcut = QShortcut(QKeySequence('h'), self)
        unhide_shortcut = QShortcut(QKeySequence("Ctrl+h"), self)
        rewind_shortcut = QShortcut(QKeySequence("r"), self)
        color_shortcut = QShortcut(QKeySequence("c"), self)
        increase_slider_shortcut = QShortcut(QKeySequence("right"), self)
        decrease_slider_shortcut = QShortcut(QKeySequence("left"), self)
        link_shortcut = QShortcut(QKeySequence("l"), self)
        unlink_shortcut = QShortcut(QKeySequence("Ctrl+l"), self)

        select_radio1.activated.connect(lambda:self.graph1Radio.setChecked(True))
        select_radio2.activated.connect(lambda:self.graph2Radio.setChecked(True))
        # zoom_in_shortcut.activated.connect(self.zoom_in_signal)
        # # zoom_out_shortcut.activated.connect(self.zoom_out_signal)
        # pause_resume_shortcut.activated.connect(self.toggle_play_pause_signal_graph1)
        # browse_shortcut.activated.connect(self.open_file)
        # hide_shortcut.activated.connect(lambda:self.hideChannelCheckBox.setChecked(True))
        # unhide_shortcut.activated.connect(lambda:self.hideChannelCheckBox.setChecked(False))
        # rewind_shortcut.activated.connect(self.rewind_signal)
        # color_shortcut.activated.connect(lambda:self.selectChannelColorButton.click())
        # increase_slider_shortcut.activated.connect(self.increase_slider_value)
        # decrease_slider_shortcut.activated.connect(self.decrease_slider_value)
        # link_shortcut.activated.connect(lambda:self.linkgraphsCheckbox.setChecked(True))
        # unlink_shortcut.activated.connect(lambda:self.linkgraphsCheckbox.setChecked(False))

        self.colors_graph1 = ['r', 'g', 'b','y','m','m','c']  # Define colors for graph 1 signals
        self.colors_graph2 = ['m', 'y', 'c','y','m','r','g']  # Define colors for graph 2 signals

        self.timer_graph1 = self.create_timer_graph1()
        self.timer_graph2 = self.create_timer_graph2()
        # self.timer = self.create_timer()

        self.legend_items_dict_graph1 = {}
        self.legend_items_dict_graph2 = {}

        # Automatically choose graph 1 to the first plot
        self.graph1Radio.setChecked(True)
        self.play_pauseButton.setEnabled(False)
        self.play_pauseButton_2.setEnabled(False)
        self.cineSpeedScoller.setEnabled(False)
        self.cineSpeedScoller_2.setEnabled(False)
        self.hideChannelCheckBox.setEnabled(False)
        self.moveToGraph1Button.setEnabled(False)
        self.moveToGraph2Button.setEnabled(False)

    def init_pyqtgraph1(self):
        self.plot_widget1.setBackground('k')  # Set the background color to black
        self.view_box1 = self.plot_widget1.getViewBox()
        self.view_box1.setLimits(xMin=0)  # Set the initial visible limits for graph 1
        self.view_box1.setMouseEnabled(x=False, y=True)  # Allow panning in the x-direction only
        self.view_box1.setRange(xRange=[0, 10], yRange=[0,1], padding=0.05)  # Set the initial range (visible window) for graph 1
        self.plot_widget1.plotItem.getViewBox().scaleBy((6, 1))
        self.legend1 = self.plot_widget1.addLegend()
        self.plot_widget1.plotItem.getViewBox().setLimits(yMin = -0.35 , yMax = 0.45)

    def init_pyqtgraph2(self):
        self.plot_widget2.setBackground('k')  # Set the background color to black
        self.view_box2 = self.plot_widget2.getViewBox()
        self.view_box2.setLimits(xMin=0)  # Set the initial visible limits for graph 2
        self.view_box2.setMouseEnabled(x=False, y=True)  # Allow panning in the x-direction only
        self.view_box2.setRange(xRange=[0, 10], yRange=[0,1], padding=0.05)  # Set the initial range (visible window) for graph 2
        self.plot_widget2.plotItem.getViewBox().scaleBy((6, 1))
        self.legend2 = self.plot_widget2.addLegend()
        self.plot_widget2.plotItem.getViewBox().setLimits(yMin = -0.15, yMax = 0.55)

    # def increase_slider_value(self):
    #     current_value = self.cineSpeedScoller.value()
    #     # Increase the slider value (adjust the step as needed)
    #     new_value = min(current_value + 1, self.cineSpeedScoller.maximum())
    #     self.cineSpeedScoller.setValue(new_value)
    #     # Update the playback speed based on the new slider value
    #     self.update_playback_speed(new_value)

    # def decrease_slider_value(self):
    #     current_value = self.cineSpeedScoller.value()
    #     # Decrease the slider value (adjust the step as needed)
    #     new_value = max(current_value - 1, self.cineSpeedScoller.minimum())
    #     self.cineSpeedScoller.setValue(new_value)
    #     # Update the playback speed based on the new slider value
    #     self.update_playback_speed(new_value)

    def open_file(self):
        if not (self.graph1Radio.isChecked() or self.graph2Radio.isChecked()):
            # Display an error message if neither graph 1 nor graph 2 radio button is checked
            QMessageBox.critical(self, "Error", "Please choose Graph 1 or Graph 2 before browsing a file.")
            return

        file_name, _= QFileDialog.getOpenFileName(self, "Open Signal File", "", "Signal Files (*.pkl);;All Files (*)")

        if file_name:
            if self.currentGraph == 1:
                self.graph1HorizontalScroller.setEnabled(True)
                with open(file_name, 'rb') as file:
                    file_data = pickle.load(file)
                self.graph1Files.append(file_name)
                new_channel_name = f"Channel {len(self.graph1Files) + 1}"
                self.play_pauseButton.setEnabled(True)
                self.cineSpeedScoller.setEnabled(True)
            elif self.currentGraph == 2:
                self.graph2HorizontalScroller.setEnabled(True)
                with open(file_name, 'rb') as file:
                    file_data = pickle.load(file)
                self.graph2Files.append(file_name)
                new_channel_name = f"Channel {len(self.graph2Files) + 1}"
                self.play_pauseButton_2.setEnabled(True)
                self.cineSpeedScoller_2.setEnabled(True)

            self.channelsComboBox.setCurrentIndex(self.channelsComboBox.findText(new_channel_name))  # Set the current index to the newly added channel
            self.load_signal_for_graph(file_data, self.graph1ChannelMapping if self.currentGraph == 1 else self.graph2ChannelMapping)
            self.updateChannelsComboBox()
            self.update_legend_for_current_channel()

            # Automatically play the signal
            self.is_playing_graph1 = True
            self.is_playing_graph2 = True
            self.play_pauseButton.setText("Pause")


    def load_signal_for_graph(self, signal_data, graph_files):
        new_channel_name = f"Channel {len(graph_files) + 1}"
        self.channelsComboBox.addItem(new_channel_name)

        if self.currentGraph == 1:
            self.signal_data_graph1.append(signal_data)
            self.timer_graph1.start(self.update_interval_ms)
            self.current_index_graph1 = 0
            self.update_play_pause_button_graph1(self.is_playing_graph1)
            self.graph1ChannelNames.append(new_channel_name)
            self.graph1ChannelMapping[new_channel_name] = signal_data
        elif self.currentGraph == 2:
            self.signal_data_graph2.append(signal_data)
            self.timer_graph2.start(self.update_interval_ms)
            self.current_index_graph2 = 0
            self.update_play_pause_button_graph2(self.is_playing_graph2)
            self.graph2ChannelNames.append(new_channel_name)
            self.graph2ChannelMapping[new_channel_name] = signal_data

        self.updateChannelMapping()

    def horizontal_scroll_graph1(self, value):
            view_box1 = self.plot_widget1.getViewBox()
            view_box2 = self.plot_widget2.getViewBox()

            current_view = view_box1.viewRange()[0]

            left_limit = 0
            right_limit = self.right_limit_graph1

            # Calculate the new x-axis range based on the scroll value
            current_x_range = current_view[1] - current_view[0]
            if(value > self.previous_slider_value_scroller1):
                new_x_end = current_view[1] + value
            else:
                new_x_end = current_view[1] - abs(value)

            if(new_x_end > right_limit):
                new_x_end = right_limit
                new_x_start = new_x_end - current_x_range
            else:
                new_x_start = new_x_end - current_x_range

            # Ensure the left limit is zero
            if (new_x_start < left_limit):
                new_x_start = left_limit
                new_x_end = new_x_start + current_x_range


            if self.linkgraphsCheckbox.isChecked():
                view_box1.setXRange(new_x_start, new_x_end, padding=0)
                view_box2.setXRange(new_x_start, new_x_end, padding=0)
            else:
                view_box1.setXRange(new_x_start, new_x_end, padding=0)

            self.previous_slider_value_scroller1 = value


    def horizontal_scroll_graph2(self, value):
        view_box = self.plot_widget2.getViewBox()
        current_view = view_box.viewRange()[0]

        left_limit = 0
        right_limit = self.right_limit_graph2

        current_x_range = current_view[1] - current_view[0]
        if(value > self.previous_slider_value_scroller2):
            new_x_end = current_view[1] + value
        else:
            new_x_end = current_view[1] - abs(value)

        if(new_x_end > right_limit):
            new_x_end = right_limit
            new_x_start = new_x_end - current_x_range
        else:
            new_x_start = new_x_end - current_x_range

        # Ensure the left limit is zero
        if (new_x_start < left_limit):
            new_x_start = left_limit
            new_x_end = new_x_start + current_x_range

        # Set the new x-axis range
        view_box.setXRange(new_x_start, new_x_end, padding=0)

        self.previous_slider_value_scroller2 = value



    def update_playback_speed_graph1(self, value):
        min_speed = 0.25
        max_speed = 2

        speed_multiplier = min_speed + (max_speed - min_speed) * (value / 100.0)
        if self.linkgraphsCheckbox.isChecked():
            # Synchronize both graphs' playback speed
            self.playback_speed_graph1 = speed_multiplier
            self.playback_speed_graph2 = speed_multiplier
            self.update_interval_graph1 = int(self.update_interval_ms / speed_multiplier)
            self.update_interval_graph2 = int(self.update_interval_ms / speed_multiplier)
            self.cineSpeedScoller.setValue(value)
        else:
            self.playback_speed_graph1 = speed_multiplier
            self.update_interval_graph1 = int(self.update_interval_ms / speed_multiplier)
                

    def update_playback_speed_graph2(self, value):
        min_speed = 0.25
        max_speed = 2

        speed_multiplier = min_speed + (max_speed - min_speed) * (value / 100.0)
        self.playback_speed_graph2 = speed_multiplier
        self.update_interval_graph2 = int(self.update_interval_ms / speed_multiplier)

    def link_graphs(self):
        if self.linkgraphsCheckbox.isChecked():
            self.browseButton.setEnabled(False)
            self.zoomInButton_2.setEnabled(False)
            self.zoomOutButton_2.setEnabled(False)
            self.play_pauseButton_2.setEnabled(False)
            self.rewindButton_2.setEnabled(False)
            self.cineSpeedScoller_2.setEnabled(False)
            self.graph2HorizontalScroller.setEnabled(False)
            self.play_pauseButton.setText("Pause")
            self.cineSpeedScoller.setValue(50)
            self.previous_slider_value_scroller1 = 100
            self.right_limit_graph1 = 0

            self.current_index_graph1 = 0
            self.plot_widget1.clear()
            self.timer_graph1.start(self.update_interval_ms)
            self.is_playing_graph1 = True
            self.playback_speed_graph1 = 1.0
            
            self.current_index_graph2 = 0
            self.plot_widget2.clear()
            self.timer_graph2.start(self.update_interval_ms)
            self.is_playing_graph2 = True
            self.playback_speed_graph2 = 1.0

        else:
            self.browseButton.setEnabled(True)
            self.zoomInButton_2.setEnabled(True)
            self.zoomOutButton_2.setEnabled(True)
            self.play_pauseButton_2.setEnabled(True)
            self.rewindButton_2.setEnabled(True)
            self.cineSpeedScoller_2.setEnabled(True)
            self.graph2HorizontalScroller.setEnabled(True)
            self.update_play_pause_button_graph1(self.is_playing_graph1)
            self.update_play_pause_button_graph2(self.is_playing_graph2)
            self.previous_slider_value_scroller1 = 100
            self.right_limit_graph1 = 0
            # self.cineSpeedLabel.setText("Graph #01 Cine Speed:")

    def plot_signal(self, plot_widget):
        if plot_widget == self.plot_widget1:
            signal_data_list = self.signal_data_graph1
            current_index = self.current_index_graph1
            zoom_factor = self.zoom_factor_graph1
            colors = self.colors_graph1
            hidden_channels = self.hidden_channels_graph1
        elif plot_widget == self.plot_widget2:
            signal_data_list = self.signal_data_graph2
            current_index = self.current_index_graph2
            zoom_factor = self.zoom_factor_graph2
            colors = self.colors_graph2
            hidden_channels = self.hidden_channels_graph2
        else:
            return  # Do nothing if no graph is selected

        if signal_data_list:
            min_value = float('inf')
            max_value = float('-inf')

            for i, signal_data in enumerate(signal_data_list):
                start = max(0, current_index - int(1000 * zoom_factor))
                end = min(len(signal_data), current_index + int(1000 * zoom_factor))
                data_to_plot_temp = signal_data[start:current_index + 1]

                if len(data_to_plot_temp) > 0:
                    # Skip hidden channels
                    if i in hidden_channels:
                        continue

                    min_value = min(min_value, np.min(data_to_plot_temp))
                    max_value = max(max_value, np.max(data_to_plot_temp))

                    plot_widget.plot(data_to_plot_temp, pen=pg.mkPen(colors[i]))

            if min_value != float('inf') and max_value != float('-inf'):
                plot_widget.setYRange(min_value, max_value)
            else:
                plot_widget.setYRange(0, 1)

        else:
            plot_widget.setYRange(0, 1)

        view_box = plot_widget.getViewBox()
        current_view = view_box.viewRange()[0]
        view_width = current_view[1] - current_view[0]
        new_view_x = [current_index - view_width * 0.5, current_index + view_width * 0.5]
        x_axis_offset = 31
        new_view_x[0] -= x_axis_offset
        new_view_x[1] -= x_axis_offset
        view_box.setXRange(new_view_x[0], new_view_x[1], padding=0)


    def create_timer_graph1(self):
        timer = QTimer()
        timer.timeout.connect(self.timerEvent1)
        return timer
    
    def create_timer_graph2(self):
        timer = QTimer()
        timer.timeout.connect(self.timerEvent2)
        return timer

    def timerEvent1(self):
            self.timer_graph1.setInterval(self.update_interval_graph1)
            if self.is_playing_graph1:
                self.plot_signal(self.plot_widget1)
                self.current_index_graph1 += 1


    def timerEvent2(self):
            self.timer_graph2.setInterval(self.update_interval_graph2)
            if self.is_playing_graph2:
                self.plot_signal(self.plot_widget2)
                self.current_index_graph2 += 1

    def zoom_in_signal_graph_1(self):
        if self.linkgraphsCheckbox.isChecked():
            # Simultaneously control both graphs with graph 1 button
            if self.zoom_in_presses >= 0 and self.zoom_in_presses < 5:
                self.plot_widget1.plotItem.getViewBox().scaleBy((0.91, 0.91))
                self.plot_widget2.plotItem.getViewBox().scaleBy((0.91, 0.91))
                self.zoom_in_presses += 1
                self.zoom_out_presses += 1
        else:
            if self.zoom_in_presses >= 0 and self.zoom_in_presses < 5:
                self.plot_widget1.plotItem.getViewBox().scaleBy((0.91, 0.91))
                self.zoom_in_presses += 1
                self.zoom_out_presses += 1

    def zoom_in_signal_graph_2(self):
        if(self.zoom_in_presses2 >= 0 and self.zoom_in_presses2 < 5):
                self.plot_widget2.plotItem.getViewBox().scaleBy((0.91, 0.91))
                self.zoom_in_presses2 += 1
                self.zoom_out_presses2 += 1

    def zoom_out_signal_graph1(self):
        if self.linkgraphsCheckbox.isChecked():
            # Simultaneously control both graphs
            if(self.zoom_out_presses > 0):
                self.plot_widget1.plotItem.getViewBox().scaleBy((1.1, 1.1))
                self.plot_widget2.plotItem.getViewBox().scaleBy((1.1, 1.1))
                self.zoom_in_presses -= 1
                self.zoom_out_presses -= 1
        else:
            if(self.zoom_out_presses > 0):
                self.plot_widget1.plotItem.getViewBox().scaleBy((1.1, 1.1))
                self.zoom_in_presses -= 1
                self.zoom_out_presses -= 1

    def zoom_out_signal_graph2(self):
        if(self.zoom_out_presses2 > 0):
                self.plot_widget2.plotItem.getViewBox().scaleBy((1.1, 1.1))
                self.zoom_in_presses2 -= 1
                self.zoom_out_presses2 -= 1

    def toggle_play_pause_signal_graph1(self):

        if self.linkgraphsCheckbox.isChecked():
            self.is_playing_graph1 = not self.is_playing_graph1
            self.is_playing_graph2 = not self.is_playing_graph2
            self.update_play_pause_button_graph1(self.is_playing_graph1)
            self.right_limit_graph1 = self.view_box1.viewRange()[0][1]
        else:
                self.is_playing_graph1 = not self.is_playing_graph1
                self.update_play_pause_button_graph1(self.is_playing_graph1)
                self.right_limit_graph1 = self.view_box1.viewRange()[0][1]

    def toggle_play_pause_signal_graph2(self):
        self.is_playing_graph2 = not self.is_playing_graph2
        self.update_play_pause_button_graph2(self.is_playing_graph2)
        self.right_limit_graph2 = self.view_box2.viewRange()[0][1]              

    def update_play_pause_button_graph1(self, is_playing):
        if is_playing:
            self.play_pauseButton.setText("Pause")
        else:
            self.play_pauseButton.setText("Resume")

    def update_play_pause_button_graph2(self, is_playing):
        if is_playing:
            self.play_pauseButton_2.setText("Pause")
        else:
            self.play_pauseButton_2.setText("Resume")

    def rewind_signal_graph1(self):
        if self.linkgraphsCheckbox.isChecked():
            # Simultaneously control both graphs
            self.plot_widget1.clear()
            self.plot_widget2.clear()
            self.current_index_graph1 = 0
            self.current_index_graph2 = 0
            self.plot_signal(self.plot_widget1)
            self.plot_signal(self.plot_widget2)
            self.is_playing_graph1 = True
            self.is_playing_graph2 = True
            self.play_pauseButton.setText("Pause")
        else:
            self.plot_widget1.clear()
            self.current_index_graph1 = 0
            self.plot_signal(self.plot_widget1)
            self.is_playing_graph1 = True
            self.play_pauseButton.setText("Pause")


    def rewind_signal_graph2(self):
            self.plot_widget2.clear()
            self.current_index_graph2 = 0
            self.plot_signal(self.plot_widget2)
            self.is_playing_graph2 = True
            self.play_pauseButton_2.setText("Pause")  
    

    def select_channel_color(self):
        # Get the current channel name
        current_channel_name = self.channelsComboBox.currentText()

        # Determine which graph is currently active
        if self.currentGraph == 1:
            colors = self.colors_graph1
            legend_items_dict = self.legend_items_dict_graph1
        elif self.currentGraph == 2:
            colors = self.colors_graph2
            legend_items_dict = self.legend_items_dict_graph2
        else:
            return

        selected_index = self.channelsComboBox.currentIndex()  # Get the index of the selected channel

        # Open a color dialog to let the user choose a new color
        new_color = QColorDialog.getColor()

        if new_color.isValid():  # Check if a valid color is chosen
            # Update the color in the list for the current graph
            colors[selected_index] = new_color

            # Update the color of the legend item directly
            legend_item = legend_items_dict.get(current_channel_name)
            if legend_item:
                pen = pg.mkPen(new_color)
                legend_item.setPen(pen)

        # Update the legend immediately after changing the channel color
        self.update_legend_for_current_channel()

    def update_channel_color(self, index, color, colors_list, plot_widget):
        # Update the color of the selected channel in the list
        if 0 <= index < len(colors_list):
            colors_list[index] = color.name()

        # Update the plot with the new color
        self.plot_signal(plot_widget)

    def hide_channel(self, state):
        selected_channel = self.channelsComboBox.currentText()

        if selected_channel:
            # Determine the current graph and the appropriate checkbox states dictionary
            if self.currentGraph == 1:
                checkbox_states = self.checkbox_states_graph1
                hidden_channels = self.hidden_channels_graph1
                channel_names = self.graph1ChannelNames
                plot_widget = self.plot_widget1
            elif self.currentGraph == 2:
                checkbox_states = self.checkbox_states_graph2
                hidden_channels = self.hidden_channels_graph2
                channel_names = self.graph2ChannelNames
                plot_widget = self.plot_widget2

            # Update the checkbox state in the dictionary
            checkbox_states[selected_channel] = state

            # Update the hidden channels list based on the checkbox state
            channel_index = channel_names.index(selected_channel)
            if state:
                hidden_channels.remove(channel_index)
            else:
                hidden_channels.append(channel_index)
                
            plot_widget.clear()

    def updateChannelsComboBox(self):
        self.channelsComboBox.clear()  # Clear the items in the channelsComboBox

        if self.currentGraph == 1:  # If the current graph is 1
            self.channelsComboBox.addItems(self.graph1ChannelNames)  # Add channel names for graph 1
        elif self.currentGraph == 2:  # If the current graph is 2
            self.channelsComboBox.addItems(self.graph2ChannelNames)  # Add channel names for graph 2


        self.channelsComboBox.currentIndexChanged.connect(self.update_legend_for_current_channel)

    def onChannelSelectionChanged(self, index):
        selected_channel = self.channelsComboBox.currentText()

        if selected_channel:
            # Get the current graph and the appropriate checkbox states dictionary
            if self.currentGraph == 1:
                self.hideChannelCheckBox.setEnabled(True)
                self.moveToGraph1Button.setEnabled(False)
                self.moveToGraph2Button.setEnabled(True)
                file_path = self.graph1ChannelMapping.get(selected_channel)
                checkbox_states = self.checkbox_states_graph1
            elif self.currentGraph == 2:
                self.hideChannelCheckBox.setEnabled(True)
                self.moveToGraph2Button.setEnabled(False)
                self.moveToGraph1Button.setEnabled(True)
                file_path = self.graph2ChannelMapping.get(selected_channel)
                checkbox_states = self.checkbox_states_graph2

            if file_path:
                # Update the checkbox state based on the dictionary or set to unchecked
                checkbox_state = checkbox_states.get(selected_channel, True)
                self.hideChannelCheckBox.blockSignals(True)  # Block signals temporarily
                self.hideChannelCheckBox.setChecked(checkbox_state)
                self.hideChannelCheckBox.blockSignals(False)  # Unblock signals

        else:
            self.hideChannelCheckBox.setEnabled(False)
            self.hideChannelCheckBox.setChecked(False)
            self.moveToGraph1Button.setEnabled(False)
            self.moveToGraph2Button.setEnabled(False)


    def move_channel_to_other_graph(self):
        # Get the selected channel
        selected_channel = self.channelsComboBox.currentText()

        # Determine the source and destination graphs based on the radio buttons
        source_graph = self.currentGraph
        destination_graph = 1 if source_graph == 2 else 2

        # Make sure the selected channel exists in the source graph
        source_channels = (
            self.graph1ChannelNames if source_graph == 1 else self.graph2ChannelNames
        )
        if selected_channel not in source_channels:
            return  # Channel doesn't exist in the source graph

        # Get the color of the channel
        channel_color = (
            self.colors_graph1[source_channels.index(selected_channel)]
            if source_graph == 1
            else self.colors_graph2[source_channels.index(selected_channel)]
        )

        # Get the signal data for the selected channel
        if source_graph == 1:
            source_data = self.signal_data_graph1
            destination_data = self.signal_data_graph2
            source_channels = self.graph1ChannelNames
            destination_channels = self.graph2ChannelNames
            source_widget = self.plot_widget1
        else:
            source_data = self.signal_data_graph2
            destination_data = self.signal_data_graph1
            source_channels = self.graph2ChannelNames
            destination_channels = self.graph1ChannelNames
            source_widget = self.plot_widget2

        channel_index = source_channels.index(selected_channel)
        channel_data = source_data.pop(channel_index)
        source_channels.pop(channel_index)

        # Append the signal data to the destination graph's data and update other data structures
        destination_data.append(channel_data)
        destination_channels.append(selected_channel)

        # Get the color of the channel in the destination graph
        destination_color = (
            self.colors_graph1[0]
            if destination_graph == 1
            else self.colors_graph2[0]
        )

        # Update the channel color in the destination graph
        if destination_graph == 1:
            self.colors_graph1.append(destination_color)
            destination_widget = self.plot_widget1
        else:
            self.colors_graph2.append(destination_color)
            destination_widget = self.plot_widget2

        # Update the channelsComboBox
        self.updateChannelsComboBox()

        # Add a new legend item for the moved channel in the destination graph's legend
        new_legend_item = pg.PlotDataItem(pen=pg.mkPen(destination_color), name=selected_channel)
        if destination_graph == 1:
            self.legend_items_dict_graph1[selected_channel] = new_legend_item
            self.legend1.addItem(new_legend_item, selected_channel)
            # Remove the legend item for the moved channel in the source graph's legend
            item = self.legend_items_dict_graph2.pop(selected_channel, None)
            if item:
                self.legend2.removeItem(item)
        else:
            self.legend_items_dict_graph2[selected_channel] = new_legend_item
            self.legend2.addItem(new_legend_item, selected_channel)
            # Remove the legend item for the moved channel in the source graph's legend
            item = self.legend_items_dict_graph1.pop(selected_channel, None)
            if item:
                self.legend1.removeItem(item)

        # Clear the source graph
        source_widget.clear()
        self.plot_signal(source_widget)

        # Call the load_signal_for_graph function to load the signal into the destination graph
        # self.load_signal_for_graph(channel_data, destination_channels)

        # Clear the destination graph to show the newly added signal
        destination_widget.clear()
        self.plot_signal(destination_widget)


        
    def updateChannelMapping(self):
        if self.currentGraph == 1:  # If the current graph is 1
            self.graph1ChannelMapping = {channel_name: file_path for channel_name, file_path in zip(self.graph1ChannelNames, self.graph1Files)}  # Update channel mapping for graph 1
        elif self.currentGraph == 2:  # If the current graph is 2
            self.graph2ChannelMapping = {channel_name: file_path for channel_name, file_path in zip(self.graph2ChannelNames, self.graph2Files)}  # Update channel mapping for graph 2

    def updateCurrentGraph(self, graph):
        if self.currentGraph == graph:
            return
        self.currentGraph = graph
        self.updateChannelsComboBox()

    def editChannelNameButtonClicked(self):
        new_channel_name = self.editChannelNameLineEdit.text().strip()  # Get the new channel name entered by the user

        if new_channel_name:  # If a new channel name is provided
            selected_index = self.channelsComboBox.currentIndex()  # Get the index of the selected channel

            if selected_index >= 0:  # If a channel is selected
                current_channel_name = self.channelsComboBox.currentText()  # Get the current channel name

                if self.currentGraph == 1:
                    # Update the channel name in the list for graph 1
                    self.graph1ChannelNames[selected_index] = new_channel_name
                    self.graph1ChannelMapping[new_channel_name] = self.graph1ChannelMapping.pop(current_channel_name, None)

                    # Update the displayed channel name in the channelsComboBox
                    self.channelsComboBox.setItemText(selected_index, new_channel_name)

                    # Update the legend item name directly
                    legend_item = self.legend_items_dict_graph1.get(current_channel_name)
                    if legend_item:
                        legend_item.opts['name'] = new_channel_name

                elif self.currentGraph == 2:
                    # Update the channel name in the list for graph 2
                    self.graph2ChannelNames[selected_index] = new_channel_name
                    self.graph2ChannelMapping[new_channel_name] = self.graph2ChannelMapping.pop(current_channel_name, None)

                    # Update the displayed channel name in the channelsComboBox
                    self.channelsComboBox.setItemText(selected_index, new_channel_name)

                    # Update the legend item name directly
                    legend_item = self.legend_items_dict_graph2.get(current_channel_name)
                    if legend_item:
                        legend_item.opts['name'] = new_channel_name

            # Clear the text in the editChannelNameLineEdit
            self.editChannelNameLineEdit.clear()

        # Update the legend immediately after editing
        self.update_legend_for_current_channel()



    def update_legend_for_current_channel(self):

        # Determine which graph is currently active
        if self.currentGraph == 1:
            legend = self.legend1
            colors = self.colors_graph1
            channel_names = self.graph1ChannelNames
            legend_items_dict = self.legend_items_dict_graph1
        elif self.currentGraph == 2:
            legend = self.legend2
            colors = self.colors_graph2
            channel_names = self.graph2ChannelNames
            legend_items_dict = self.legend_items_dict_graph2
        else:
            return

        # Clear existing items from the legend
        legend.clear()

        # Update the legend items dictionary
        legend_items_dict.clear()

        # Iterate over channel names and update the legend
        for i, channel_name in enumerate(channel_names):
            color = colors[i]
            pen = pg.mkPen(color)

            # Create a new item for each channel and add it to the legend
            item = pg.PlotDataItem(pen=pen, name=channel_name)
            legend.addItem(item, channel_name)

            # Update the legend items dictionary
            legend_items_dict[channel_name] = item

    def calculate_statistics(self, file_path):
        # Check if the file has a .pkl extension
        if not file_path.endswith('.pkl'):
            raise ValueError("Unsupported file format. Only .pkl files are supported.")

        # Load data from the pickle file
        with open(file_path, 'rb') as file:
            data = pickle.load(file)

        # Convert the data to a DataFrame if it's not already
        if not isinstance(data, pd.DataFrame):
            data = pd.DataFrame(data)

        # Calculate statistics for each column (signal)
        statistics = {}
        for column in data.columns:
            mean = data[column].mean()
            std_dev = data[column].std()
            duration = len(data)
            min_value = data[column].min()
            max_value = data[column].max()

            statistics[column] = {
                'Mean': mean,
                'Standard Deviation': std_dev,
                'Duration': duration,
                'Min Value': min_value,
                'Max Value': max_value
            }
        return statistics

    def generateStats(self):
        # Store the current selection
        temp_selection = 1 if self.graph1Radio.isChecked() else 2

        # Toggle to graph 1
        self.graph1Radio.setChecked(True)

        # Gather statistics for graph 1
        statistics_container1 = {}  # Create an empty container to hold statistics
        for index in range(self.channelsComboBox.count()):
            channel_name = self.channelsComboBox.itemText(index)
            file_path = self.graph1ChannelMapping.get(channel_name)

            if file_path:
                # Calculate statistics
                statistics1 = self.calculate_statistics(file_path)

                # Create a dictionary to hold information about the channel
                channel_info = {
                    'Name': channel_name,
                    'Graph': 1,
                    'Statistics': statistics1
                }

                # Add the channel info to the container
                statistics_container1[channel_name] = channel_info

        # Update graph 1 statistics
        self.graph1Statistics = statistics_container1

        # Toggle to graph 2
        self.graph2Radio.setChecked(True)

        # Gather statistics for graph 2
        statistics_container2 = {}  # Create an empty container to hold statistics
        for index in range(self.channelsComboBox.count()):
            channel_name = self.channelsComboBox.itemText(index)
            file_path = self.graph2ChannelMapping.get(channel_name)

            if file_path:
                # Calculate statistics
                statistics2 = self.calculate_statistics(file_path)

                # Create a dictionary to hold information about the channel
                channel_info = {
                    'Name': channel_name,
                    'Graph': 2,
                    'Statistics': statistics2
                }

                # Add the channel info to the container
                statistics_container2[channel_name] = channel_info

        # Update graph 2 statistics
        self.graph2Statistics = statistics_container2
        
        # print(f"Graph 1 Statistics: {self.graph1Statistics}")
        # print(f"Graph 2 Statistics: {self.graph2Statistics}")

        # Return to the original selection
        if temp_selection == 1:
            self.graph1Radio.setChecked(True)
        else:
            self.graph2Radio.setChecked(True)

    def generateSnapshots(self):
        # Store the current selection
        temp_selection = 1 if self.graph1Radio.isChecked() else 2

        # Get the snapshot of plot_widget1
        self.plot_widget1.repaint()
        pixmap = self.plot_widget1.grab()
        image1 = QPixmap.toImage(pixmap)
        image1_path = f'image1_{len(self.graph1_images) + 1}.png'  # Unique path for each snapshot
        image1.save(image1_path, 'PNG')
        self.graph1_images.append(image1_path)  

        # Get the snapshot of plot_widget2
        self.plot_widget2.repaint()
        pixmap = self.plot_widget2.grab()
        image2 = QPixmap.toImage(pixmap)
        image2_path = f'image2_{len(self.graph2_images) + 1}.png'  # Unique path for each snapshot
        image2.save(image2_path, 'PNG')
        self.graph2_images.append(image2_path)

        # Return to the original selection
        if temp_selection == 1:
            self.graph1Radio.setChecked(True)
        else:
            self.graph2Radio.setChecked(True)

        return self.graph1_images, self.graph2_images

    def generateTables(self,graph1Statistics, graph2Statistics):

        # Define the data for the tables
        data1 = [['Channel', 'Mean', 'Std Dev', 'Duration', 'Min Value', 'Max Value']]
        data2 = [['Channel', 'Mean', 'Std Dev', 'Duration', 'Min Value', 'Max Value']]

        for channel, stats in graph1Statistics.items():
            channel_stats = stats.get('Statistics', {}).get(0, {})  # Extract statistics for channel '0'
            data1.append([
                channel,
                f"{channel_stats['Mean']:.2f}",
                f"{channel_stats['Standard Deviation']:.2f}",
                channel_stats.get('Duration', ''),
                f"{channel_stats['Min Value']:.2f}",
                f"{channel_stats['Max Value']:.2f}"
            ])


        for channel, stats in graph2Statistics.items():
            channel_stats = stats.get('Statistics', {}).get(0, {})  # Extract statistics for channel '0'
            data2.append([
                channel,
                f"{channel_stats['Mean']:.2f}",
                f"{channel_stats['Standard Deviation']:.2f}",
                channel_stats.get('Duration', ''),
                f"{channel_stats['Min Value']:.2f}",
                f"{channel_stats['Max Value']:.2f}"
            ])


        # Create the tables and style them
        table1 = Table(data1)
        table1.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black)]))

        table2 = Table(data2)
        table2.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black)]))

        # print("Graph 1 Statistics:")
        # print(graph1Statistics)

        # print("Graph 2 Statistics:")
        # print(graph2Statistics)
        return table1,table2

    def generatePDF(self, graph1_images, table1, graph2_images, table2, file_name):
        doc = SimpleDocTemplate(file_name, pagesize=letter, leftMargin=inch, rightMargin=inch, topMargin=inch, bottomMargin=inch)
        elements = []

        # Add a title and logo
        title_style = getSampleStyleSheet()['Title']
        title = Paragraph("<b>ICU MultiVital Signal Monitor</b>", title_style)
        side_header_style = getSampleStyleSheet()['Normal'].clone('SideHeaderStyle')
        side_header_style.fontName = 'Helvetica-Bold'
        side_header_style.fontSize = 14
        side_header_style.alignment = 0
        bullet_point = '<bullet>&diams;</bullet>'


        # Add the title and logo to the PDF elements
        elements.append(title)

        # Add some space between the title and logo and the content below
        elements.extend([Spacer(0, 60)])

        h1_text = f'<b>{bullet_point}</b> <u>Graph #01 Signal-Display And Statistics</u>'
        h1 = Paragraph(h1_text, side_header_style)       
        h2_text = f'<b>{bullet_point}</b> <u>Graph #02 Signal-Display And Statistics</u>'
        h2 = Paragraph(h2_text, side_header_style)
        
        elements.append(h1)
        elements.extend([Spacer(0, 40)])
        
        for image_path in graph1_images:
            image = Image(image_path)
            image.drawWidth = 6*inch
            image.drawHeight = 4*inch
            elements.append(image)
            elements.extend([Spacer(0, 0.63*inch), table1])  
            elements.append(PageBreak())

        elements.append(h2)
        elements.extend([Spacer(0, 40)])

        # Iterate over graph2_images and add images to the PDF
        for image_path in graph2_images:
            image = Image(image_path)
            image.drawWidth = 6*inch
            image.drawHeight = 4*inch
            elements.append(image)
            elements.extend([Spacer(0, 0.63*inch), table2])  
            elements.append(PageBreak())

        
        doc.build(elements)
        QtWidgets.QMessageBox.information(
                self, 'Done', 'PDF has been created')
    
    def exportPDF(self):
        self.generateStats()     
        table1, table2 = self.generateTables(self.graph1Statistics, self.graph2Statistics)
        graph1_images, graph2_images = self.graph1_images, self.graph2_images
        file_name, _ = QFileDialog.getSaveFileName(self, "Save PDF File", "", "PDF Files (*.pdf);;All Files (*)")

        if file_name:
            self.generatePDF(graph1_images, table1, graph2_images, table2, file_name)



def main():
    app = QApplication(sys.argv)  # Create an application instance
    window = MainApp()  # Create an instance of the MainApp class
    window.show()  # Display the main window
    app.exec()  # Start the application event loop

if __name__ == "__main__":
    main()

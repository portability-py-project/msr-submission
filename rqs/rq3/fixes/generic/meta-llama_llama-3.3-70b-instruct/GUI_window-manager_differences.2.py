import os
import sys
import subprocess
import webbrowser
import platform

import toga
from toga.style import Pack
from toga.style.pack import RIGHT, CENTER, ROW, COLUMN
from toga.fonts import BOLD, SANS_SERIF

# Check for the existence of coverage and duvet
try:
    import coverage
    try:
        import duvet
    except ImportError:
        duvet = None
except ImportError:
    coverage = None
    duvet = None

from cricket.model import TestMethod, TestSuiteProblems
from cricket.executor import Executor
from cricket.dialogs import FailedTestDialog, TestLoadErrorDialog, IgnorableTestLoadErrorDialog


class Cricket(toga.App):
    def startup(self):
        '''
        -----------------------------------------------------
        | main button toolbar                               |
        -----------------------------------------------------
        |       < ma | in content area >                    |
        |            |                                      |
        |  left      |              right                   |
        |  control   |              details frame           |
        |  tree      |              / output viewer         |
        |  area      |                                      |
        -----------------------------------------------------
        |     status bar area                               |
        -----------------------------------------------------
        '''
        self.executor = None

        # Main window of the application with title and size
        if platform.system() == 'Windows':
            self.main_window = toga.MainWindow(title=self.name, size=(1024, 768))
        elif platform.system() == 'Darwin':
            self.main_window = toga.MainWindow(title=self.name, size=(800, 600))
        else:
            self.main_window = toga.MainWindow(title=self.name, size=(1024, 768))

        # Setup the menu and toolbar
        self._setup_commands()

        # Set up the main content for the window.
        self._setup_status_bar()
        self._setup_main_content()

        self._setup_init_values()

        # Now that we've laid out the grid, hide the error text
        # until we actually have an error/output to display
        # self.error_box.style.visibility = HIDDEN

        # Sets the content defined above to show on the main window
        self.main_window.content = self.content
        # Show the main window
        self.main_window.show()

        self._check_errors_status()

    # rest of your code remains the same
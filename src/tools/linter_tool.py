from json import loads, dumps

from chimerax.ui.gui import MainToolWindow
from chimerax.core.settings import Settings
from chimerax.core.tools import ToolInstance
from chimerax.core.commands import run

try:
    from Qt.QtCore import Qt
    from Qt.QtGui import QIcon
    from Qt.QtWidgets import (
        QPushButton,
        QComboBox,
        QTableWidget,
        QTableWidgetItem,
        QFormLayout,
        QHBoxLayout,
        QWidget,
        QLabel,
        QStyle,
        QHeaderView,
        QFileDialog,
    )
except (ModuleNotFoundError, ImportError):
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QIcon
    from PyQt5.QtWidgets import (
        QPushButton,
        QComboBox,
        QTableWidget,
        QTableWidgetItem,
        QFormLayout,
        QHBoxLayout,
        QWidget,
        QLabel,
        QStyle,
        QHeaderView,
        QFileDialog,
    )


class _LinterSettings(Settings):
    AUTO_SAVE = {
        "files": "[]",
        "linter": "flake8",
    }


class Linter(ToolInstance):
    """
    tool to run python linters on files
    the UI has a list of files, an option to choose
    the linter, and a button to run the linter
    results are printed to the log
    """

    def __init__(self, session, name):
        super().__init__(session, name)
        
        self.tool_window = MainToolWindow(self)
        self.settings = _LinterSettings(self.session, name)
        
        self._build_ui()
    
    def _build_ui(self):
        layout = QFormLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["file", "remove"])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.cellClicked.connect(self.table_clicked)
        layout.addRow(self.table)

        self.linters = QComboBox()
        self.linters.addItems([
            "pyflakes", "flake8", "mypy", "pydocstyle",
            "pylint", 
        ])
        ndx = self.linters.findText(self.settings.linter, Qt.MatchExactly)
        self.linters.setCurrentIndex(ndx)
        layout.addRow(self.linters)
        
        lint = QPushButton("run linter")
        lint.clicked.connect(self.run_linter)
        layout.addRow(lint)

        self.add_files(loads(self.settings.files))

        self.tool_window.ui_area.setLayout(layout)

        self.tool_window.manage(None)
    
    def table_clicked(self, row, column):
        """
        if the last row is clicked, open a file browser and add
        the files to the list
        otherwise, if the 2nd column is clicked (the trash can),
        remove that row
        """
        if row == self.table.rowCount() - 1 or self.table.rowCount() == 1:
            filenames = QFileDialog.getOpenFileNames(
                filter="Python Files (*.py)"
            )
            if filenames[0]:
                self.table.setRowCount(self.table.rowCount() - 1)
                self.add_files(filenames[0])
        elif column == 1:
            self.table.removeRow(row)

    def add_files(self, filenames):
        """add filenames (list(str)) to the table"""
        for f in filenames:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            file_item = QTableWidgetItem()
            file_item.setData(Qt.DisplayRole, f)
            self.table.setItem(row, 0, file_item)
            
            widget_that_lets_me_horizontally_align_an_icon = QWidget()
            widget_layout = QHBoxLayout(widget_that_lets_me_horizontally_align_an_icon)
            section_remove = QLabel()
            dim = int(1.5 * section_remove.fontMetrics().boundingRect("Z").height())
            section_remove.setPixmap(
                QIcon(
                    section_remove.style().standardIcon(QStyle.SP_DialogDiscardButton)
                ).pixmap(dim, dim)
            )
            widget_layout.addWidget(section_remove, 0, Qt.AlignHCenter)
            widget_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 1, widget_that_lets_me_horizontally_align_an_icon)

        self.add_last_row()

    def add_last_row(self):
        """add the "add files" button to the bottom of the table"""
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        add_row = QTableWidgetItem()
        add_row.setData(Qt.DisplayRole, "add files")
        self.table.setItem(row, 0, add_row)

    def run_linter(self):
        """execute linter"""
        previous_files = []
        linter = self.linters.currentText()
        for row in range(0, self.table.rowCount() - 1):
            fname = self.table.item(row, 0).text()
            previous_files.append(fname)

            run(self.session, "linter \"%s\" linter %s" % (fname, linter))

        self.settings.files = dumps(previous_files)
        self.settings.linter = linter

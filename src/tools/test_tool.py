try:
    from PySide2.QtCore import QRegularExpression, Qt
    from PySide2.QtGui import QFontDatabase
    from PySide2.QtWidgets import (
        QVBoxLayout,
        QHBoxLayout,
        QTableWidget,
        QTableWidgetItem,
        QPushButton,
        QLineEdit,
        QStyle,
        QSizePolicy,
        QWidget,
        QTextBrowser,
    )
except (ModuleNotFoundError, ImportError):
    from PyQt5.QtCore import QRegularExpression, Qt
    from PyQt5.QtGui import QFontDatabase
    from PyQt5.QtWidgets import (
        QVBoxLayout,
        QHBoxLayout,
        QTableWidget,
        QTableWidgetItem,
        QPushButton,
        QLineEdit,
        QStyle,
        QSizePolicy,
        QWidget,
        QTextBrowser,
    )

from chimerax.core.settings import Settings
from chimerax.core.tools import ToolInstance
from chimerax.ui.gui import MainToolWindow, ChildToolWindow


def get_button(button_type):
    button = QPushButton()
    button.setFlat(True)
    if button_type == "success":
        button.setIcon(button.style().standardIcon(QStyle.SP_DialogApplyButton))
    elif button_type == "fail":
        button.setIcon(button.style().standardIcon(QStyle.SP_MessageBoxCritical))
    elif button_type == "error":
        button.setIcon(button.style().standardIcon(QStyle.SP_MessageBoxWarning))
    elif button_type == "skip" or button_type == "expected fail":
        button.setIcon(button.style().standardIcon(QStyle.SP_MessageBoxInformation))
    elif button_type == "unexpected success":
        button.setIcon(button.style().standardIcon(QStyle.SP_MessageBoxQuestion))

    return button


class TestRunner(ToolInstance):
    def __init__(self, session, name):
        super().__init__(session, name)
        self.tool_window = MainToolWindow(self)
        
        self._build_ui()
    
    def _build_ui(self):
        """
        ui should have:
            * table with a list of available tests and show results after they are done
            * way to filter tests
            * button to run tests
        """
        layout = QVBoxLayout()
        
        # table to list test classes and the results
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["test", "result"])
        self.table.horizontalHeader().setSectionResizeMode(0, self.table.horizontalHeader().Interactive)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(1, self.table.horizontalHeader().Stretch)
        self.table.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.table.setSelectionBehavior(self.table.SelectRows)
        layout.insertWidget(0, self.table, 1)
        
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("filter test names")
        self.filter.setClearButtonEnabled(True)
        self.filter.textChanged.connect(self.apply_filter)
        layout.insertWidget(1, self.filter, 0)
        
        self.run_button = QPushButton("run tests")
        self.run_button.clicked.connect(self.run_tests)
        self.run_button.setToolTip(
            "if no tests are selected on the table, run all tests\n" +
            "otherwise, run selected tests"
        )
        layout.insertWidget(2, self.run_button)
        
        self.fill_table()
        self.table.resizeColumnToContents(0)
        
        self.tool_window.ui_area.setLayout(layout)

        self.tool_window.manage(None)

    def apply_filter(self, text=None):
        """filter table to only show tests matching text"""
        if text is None:
            text = self.filter.text()

        if text:
            text = text.replace("(", "\(")
            text = text.replace(")", "\)")
            m = QRegularExpression(text)
            m.setPatternOptions(QRegularExpression.CaseInsensitiveOption)
            if m.isValid():
                m.optimize()
                filter = lambda row_num: m.match(self.table.item(row_num, 0).text()).hasMatch()
            else:
                return

        else:
            filter = lambda row: True
            
        for i in range(0, self.table.rowCount()):
            self.table.setRowHidden(i, not filter(i))
    
    def fill_table(self):
        """adds test names to the table"""
        mgr = self.session.test_manager
        
        for name in mgr.tests.keys():
            row = self.table.rowCount()
            self.table.insertRow(row)
            test_name = QTableWidgetItem()
            test_name.setData(Qt.DisplayRole, name)
            self.table.setItem(row, 0, test_name)
    
    def run_tests(self):
        """run the tests selected on the table and show the results"""
        from TestManager.commands.test import test
        
        test_list = []
        
        use_selected = True
        for row in self.table.selectionModel().selectedRows():
            if self.table.isRowHidden(row.row()):
                continue
            
            test_name = self.table.item(row.row(), 0).text()
            test_list.append(test_name)
        
        if not test_list:
            use_selected = False
            for i in range(0, self.table.rowCount()):
                if self.table.isRowHidden(i):
                    continue
                
                test_name = self.table.item(i, 0).text()
                test_list.append(test_name)

            if not test_list:
                test_list = ["all"]
        
        results = test(self.session, test_list)
        
        cell_widgets = []
        
        for name in results:
            widget = QWidget()
            widget_layout = QHBoxLayout(widget)
            widget_layout.setContentsMargins(0, 0, 0, 0)
            
            success_button = get_button("success")
            fail_button = get_button("fail")
            skip_button = get_button("skip")
            error_button = get_button("error")
            expected_fail_button = get_button("expected fail")
            unexpected_success_button = get_button("unexpected success")
            
            success_count = 0
            fail_count = 0
            error_count = 0
            unexpected_success_count = 0
            expected_fail_count = 0
            skip_count = 0
            
            success_tooltip = "Successes:\n"
            fail_tooltip = "Failed tests:\n"
            error_tooltip = "Errors during test:\n"
            unexpected_success_tooltip = "Unexpected successes:\n"
            expected_fail_tooltip = "Expected fails:\n"
            skip_tooltip = "Skipped tests:\n"

            for case in results[name]:
                result, msg = results[name][case]
                if result == "success":
                    success_count += 1
                    success_tooltip += "%s.%s: %s\n" % (case.__class__.__qualname__, case._testMethodName, msg)
                
                elif result == "fail":
                    fail_count += 1
                    fail_tooltip += "%s.%s failed: %s\n" % (case.__class__.__qualname__, case._testMethodName, msg)
                
                elif result == "error":
                    error_count += 1
                    error_tooltip += "error during %s.%s: %s\n" % (case.__class__.__qualname__, case._testMethodName, msg)

                elif result == "expected_failure":
                    expected_fail_count += 1
                    expected_fail_tooltip += "intended failure during %s.%s: %s\n" % (case.__class__.__qualname__, case._testMethodName, msg)

                elif result == "skip":
                    skip_count += 1
                    skip_tooltip += "%s.%s\n" % (case.__class__.__qualname__, case._testMethodName)

                elif result == "unexpected_success":
                    unexpected_success_count += 1
                    unexpected_success_tooltip += "%s.%s should not have worked, but did\n" % (case.__class__.__qualname__, case._testMethodName)
            
            success_tooltip = success_tooltip.strip()
            fail_tooltip = fail_tooltip.strip()
            error_tooltip = error_tooltip.strip()
            expected_fail_tooltip = expected_fail_tooltip.strip()
            skip_tooltip = skip_tooltip.strip()
            unexpected_success_tooltip = unexpected_success_tooltip.strip()
            
            icon_count = 0
            if success_count:
                success_button.setText("%i" % success_count)
                success_button.setToolTip(success_tooltip)
                success_button.clicked.connect(
                    lambda *args, t_name=name, res=success_tooltip: self.tool_window.create_child_window(
                        "successes for %s" % t_name,
                        text=res,
                        window_class=ResultsWindow,
                    )
                )
                widget_layout.insertWidget(icon_count, success_button, 1)
                icon_count += 1
            
            if fail_count:
                fail_button.setText("%i" % fail_count)
                fail_button.setToolTip(fail_tooltip)
                fail_button.clicked.connect(
                    lambda *args, res=fail_tooltip: self.tool_window.create_child_window(
                        "failures for %s" % name,
                        text=res,
                        window_class=ResultsWindow,
                    )
                )
                widget_layout.insertWidget(icon_count, fail_button, 1)
                icon_count += 1
            
            if error_count:
                error_button.setText("%i" % error_count)
                error_button.setToolTip(error_tooltip)
                error_button.clicked.connect(
                    lambda *args, res=error_tooltip: self.tool_window.create_child_window(
                        "errors for %s" % name,
                        text=res,
                        window_class=ResultsWindow,
                    )
                )
                widget_layout.insertWidget(icon_count, error_button, 1)
                icon_count += 1
            
            if unexpected_success_count:
                unexpected_success_button.setText("%i" % unexpected_success_count)
                unexpected_success_button.setToolTip(unexpected_success_tooltip)
                unexpected_success_button.clicked.connect(
                    lambda *args, res=unexpected_success_tooltip: self.tool_window.create_child_window(
                        "unexpected successes for %s" % name,
                        text=res,
                        window_class=ResultsWindow,
                    )
                )
                widget_layout.insertWidget(icon_count, unexpected_success_button, 1)
                icon_count += 1
            
            if expected_fail_count:
                expected_fail_button.setText("%i" % expected_fail_count)
                expected_fail_button.setToolTip(expected_fail_tooltip)
                expected_fail_button.clicked.connect(
                    lambda *args, res=expected_fail_tooltip: self.tool_window.create_child_window(
                        "expected failures for %s" % name,
                        text=res,
                        window_class=ResultsWindow,
                    )
                )
                widget_layout.insertWidget(icon_count, expected_fail_button, 1)
                icon_count += 1
            
            if skip_count:
                skip_button.setText("%i" % skip_count)
                skip_button.setToolTip(skip_tooltip)
                skip_button.clicked.connect(
                    lambda *args, res=skip_tooltip: self.tool_window.create_child_window(
                        "skipped tests for %s" % name,
                        text=res,
                        window_class=ResultsWindow,
                    )
                )
                widget_layout.insertWidget(icon_count, skip_button, 1)
                
            cell_widgets.append(widget)    
        
        widget_count = 0
        if use_selected:
            for row in self.table.selectionModel().selectedRows():
                if self.table.isRowHidden(row.row()):
                    continue
                
                self.table.setCellWidget(row.row(), 1, cell_widgets[widget_count])
                self.table.resizeRowToContents(row.row())
                widget_count += 1

        else:
            for i in range(0, self.table.rowCount()):
                if self.table.isRowHidden(i):
                    continue
                
                self.table.setCellWidget(i, 1, cell_widgets[widget_count])
                # self.table.resizeRowToContents(i)
                widget_count += 1


class ResultsWindow(ChildToolWindow):
    def __init__(self, tool_instance, title, text="", **kwargs):
        super().__init__(tool_instance, title, statusbar=False, **kwargs)
        
        self._build_ui()
        
        self.results.setText(text)

    def _build_ui(self):
        layout = QVBoxLayout()
        
        self.results = QTextBrowser()
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.results.setFont(font)
        layout.insertWidget(0, self.results, 1)
        
        self.ui_area.setLayout(layout)
        
        self.manage(None)
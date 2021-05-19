import time

from unittest import TestCase

from chimerax.core.toolshed import BundleAPI


class TestWithSession(TestCase):
    """test case with a session attribute"""
    count = 0
    "number of tests - set during the running of tests"
    total_time = 0
    "time taken to run all tests - set during the running of tests"
    last_class = None
    "class of the previous test - set during the running of tests"
    last_result = None
    "previous result - set during the running of tests"
    _errors = 0
    _fails = 0
    session = None
    "ChimeraX Session - set after TestManager bundle has initialized"
    _prev_msg = ""
    _prev_test = ""
    close_between_tests = True
    "run the close command during setUp/tearDown"
    close_between_classes = True
    "run the close command during setUpClass/tearDownClass"

    @classmethod
    def addTests(cls, suite):
        """discover test methods of cls and add them to suite"""
        test_names = [
            key for key in cls.__dict__.keys() if key.startswith("test_")
        ]
        
        found_tests = []
        for test in test_names:
            if callable(getattr(cls, test)):
                test_cls = cls(test)
                suite.addTest(test_cls)
                found_tests.append(test_cls)

        if not found_tests:
            test_cls = cls()
            suite.addTest(test_cls)
            found_tests.append(test_cls)
        
        return found_tests

    @classmethod
    def setUpClass(cls):
        """runs the close command if cls.close_between_classes"""
        if cls.close_between_classes:
            from chimerax.core.commands import run
            run(cls.session, "close")

    @classmethod
    def tearDownClass(cls):
        """
        runs the close command if cls.close_between_classes
        also prints info from the tests that were run from this class
        """
        if cls.close_between_classes:
            from chimerax.core.commands import run
            run(cls.session, "close")
        errors = len(cls.last_result.errors)
        fails = len(cls.last_result.failures)
        ok_msg = "{} ok"
        if TestWithSession._errors != errors:
            TestWithSession._errors = errors
            ok_msg = "{} ERROR"
        elif TestWithSession._fails != fails:
            TestWithSession._fails = fails
            ok_msg = "{} FAIL"
        else:
            ok_msg = "{} ok"

        TestWithSession._prev_msg += ok_msg.format(TestWithSession._prev_test)
        TestWithSession._prev_test = ""

        cls.session.logger.info(
            "<pre>{}</pre>".format(TestWithSession._prev_msg),
            is_html=True,
            add_newline=False,
        )

        cls.session.logger.info(
            "<pre>Ran {} tests in {:.3f}s</pre>".format(
                TestWithSession.count,
                TestWithSession.total_time,
            ),
            is_html=True,
        )
        cls.session.logger.info("-" * 70)
        TestWithSession.total_time = 0
        TestWithSession.count = 0
        TestWithSession._prev_msg = ""
        TestWithSession._prev_test = ""
        TestWithSession.last_class = None
        TestWithSession.last_result = None

    def setUp(self):
        """
        runs the close command if self.close_between_tests
        also does some accounting for info to print to log about this test
        """
        if self.close_between_tests:
            from chimerax.core.commands import run
            run(TestWithSession.session, "close")
        errors = len(self._outcome.result.errors)
        fails = len(self._outcome.result.failures)
        ok_msg = "{} ok"
        if TestWithSession._errors != errors:
            TestWithSession._errors = errors
            ok_msg = "{} ERROR"
        elif TestWithSession._fails != fails:
            TestWithSession._fails = fails
            ok_msg = "{} FAIL"
        elif self.id().split(".")[1] == self.last_class:
            ok_msg = "{} ok"
        if TestWithSession._prev_test:
            TestWithSession._prev_msg += ok_msg.format(TestWithSession._prev_test)
        self.start_time = time.time()

    def tearDown(self):
        """
        runs the close command if self.close_between_tests
        also does some accounting for info to print to log about this test
        """
        t = time.time() - self.start_time
        TestWithSession.total_time += t

        name = self.id().split(".")[-2:]
        if not TestWithSession.last_class or TestWithSession.last_class != name[0]:
            TestWithSession.last_class = name[0]
            TestWithSession.count = 0
            TestWithSession._prev_msg = "\n{}:".format(name[0])

        name = name[1]
        TestWithSession.count += 1
        TestWithSession._prev_test = "\n    {:3.0f}: {:<30s} {: 3.3f}s  ".format(
            TestWithSession.count, name, t
        )

        TestWithSession.last_result = self._outcome.result
        if self.close_between_tests:
            from chimerax.core.commands import run
            run(TestWithSession.session, "close")

    @classmethod
    def open_tool(cls, name, tool_cls=None, log=True):
        """
        opens a tool with the specified name and returns the instance of that tool
        returns False if the tool does not open
        tool_cls: ToolInstance subclass corresponding to the name of the tool
             this is used if the tool's name isn't the same as the specified name
        log: log the command used to open the tool
        """
        from chimerax.core.commands import run
        run(cls.session, "ui tool show \"%s\"" % name, log=log)
        
        opened_tool = False
        for tool in cls.session.tools.list():
            if tool_cls is not None:
                if isinstance(tool, tool_cls):
                    opened_tool = tool
                    break
            else:
                if tool.tool_name == name:
                    opened_tool = tool
                    break
        
        return opened_tool


class _TESTMANAGER_API(BundleAPI):

    api_version = 1
    
    @staticmethod
    def initialize(session, bundle_info):
        TestWithSession.session = session
    
    @staticmethod
    def register_command(bundle_info, command_info, logger):
        if command_info.name == "test":
            from .commands.test import register_test_command
            register_test_command(logger)
        if command_info.name == "linter":
            from .commands.linter import register_linter_command
            register_linter_command(logger)

    @staticmethod
    def init_manager(session, bundle_info, name, **kwargs):
        """
        initialize test manager
        """
        if name == "test_manager":
            from .manager import TestManager
            session.test_manager = TestManager(session, name)
            return session.test_manager
    
    @staticmethod
    def start_tool(session, bundle_info, tool_info):
        if tool_info.name == "Run Tests":
            from .tools.test_tool import TestRunner
            return TestRunner(session, tool_info.name)
        if tool_info.name == "Linter":
            from .tools.linter_tool import Linter
            return Linter(session, tool_info.name)

bundle_api = _TESTMANAGER_API()

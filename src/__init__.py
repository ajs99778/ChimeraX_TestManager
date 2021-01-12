import time

from unittest import TestCase

from chimerax.core.toolshed import BundleAPI


class TestWithSession(TestCase):
    count = 0
    total_time = 0
    last_class = None
    last_result = None
    _errors = 0
    _fails = 0
    session = None
    _prev_msg = ""
    _prev_test = ""
    close_between_tests = True
    close_between_classes = True

    @classmethod
    def addTests(cls, suite):
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
        if cls.close_between_classes:
            from chimerax.core.commands import run
            run(cls.session, "close")

    @classmethod
    def tearDownClass(cls):
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
    
    @staticmethod
    def run_provider(session, name, mgr, **kw):
        if mgr == session.test_manager:
            if name == "substitute_command":
                from .tests.substitute_command import SubstituteCmdTest
                return SubstituteCmdTest
            
            elif name == "normal_modes":
                from .tests.normal_modes import NormalModesToolTest
                return NormalModesToolTest
    
bundle_api = _TESTMANAGER_API()

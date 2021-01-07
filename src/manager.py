from inspect import signature

from warnings import warn

from chimerax.core.toolshed import ProviderManager

from TestManager import TestWithSession

class TestManager(ProviderManager):
    def __init__(self, session, name):
        self._session = session
        self.tests = {}
        args = []
        params = signature(super().__init__).parameters
        if any("name" in param for param in params):
            args.append(name)
        super().__init__(*args)

    def add_provider(self, bundle_info, name):
        self.tests[name] = bundle_info

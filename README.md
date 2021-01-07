# TestManager
Manager for test cases (à la `unittest`) for ChimeraX bundles.
Creating test cases can allow bundle developers to quickly test the functionality of their bundle and whether their bundle remains functioning after code is edited or ChimeraX updates.
Test cases can be created by subclassing the `TestWithSession` class of this bundle. 
For convenience, this subclass of `unittest.TestCase` has a session attribute, which can be used to execute commands or start tools in the same way a user would.
Tests can be implemented either as methods of a `TestWithSession` subclass with names that begin with "`test_`" or by implementing the `runTest` method, as is standard with `unittest.TestCase`.
A structure validation function is also included, which can be used to compare two `chimerax.atomic.AtomicStructure`s based on their elements, bonding, and RMSD between the two structures.
As an example:
```python
from chimerax.core.commands import run

from TestManager import TestWithSession
from TestManager.validation import validate_atomic_structures as validate


class AngleCmdTest(TestWithSession):
    """tests associated with the `angle` command"""
    
    def test_change_angle(self):
        """test setting the angle of a simple structure"
        # open a water molecule
        run(self.session, "open /home/CoolUser/my_bundle/tests/structures/water_molecule.mol2")
        # set the H-O-H angle to 104.5 degrees
        run(self.session, "angle @H1 @O1 @H2 104.5")
        
        # grab the water model
        # before and after every test, all open models are closed
        # therefore, our water molecule should be the first and only open model
        mdl = self.session.models.list()[0]
        
        # open a reference structure, which has an H-O-H angle of 104.5 and
        # the same bonding pattern as the previous water molecule
        run(self.session, "open /home/CoolUser/my_bundle/tests/structures/water_angle_ref.mol2")
        # grab this reference structure
        ref_mdl = self.session.models.list()[1]
        
        # the test will fail if the two water molecules are dissimilar
        # the "thresh" keyword specifies the tolerance on the RMSD
        # see the documentation associated with this method for more details
        self.assertTrue(validate(mdl, ref_mdl, thresh="tight"))
```

To add this test, include a provider for the `test_manager` in your bundle_info.xml file. 
Whether developers choose to add their test cases to their main bundle, or create a separate bundle specifically for tests is up to them.
```xml
<Providers manager="test_manager">
    <Provider name="angle_command"/>
</Providers>
```

The `run_provider` method of the bundle containing this test should return their `TestWithSession` subclass.
Multiple providers can be added to the manager.

```python
class _TestBundle(BundleAPI):
    
    @staticmethod
    def run_provider(session, name, mgr, **kw):
        if mgr is session.test_manager:
            if name == "angle_command":
                from .tests.angle_command import AngleCmdTest
                return AngleCmdTest
```

There are two simple ways to run tests. One is using the `test` command, for which a list of provider names can be specified to only run certain tests.
When run without arguments, the `test` command will run all tests.
Running `help test` will list the available tests in the log.
The "Run Tests" tool, found in the "Utilities" section, can also be used to run your tests. 
The tool lists all providers, and the providers can be selected to only run test methods of those providers.
After tests are run, results can be viewed in the tool.
For both the `test` command the the tool, results are printed to the log.

The test manager currently works with ChimeraX 1.1 and the ChimeraX 1.2 daily build as of 6th January, 2021.

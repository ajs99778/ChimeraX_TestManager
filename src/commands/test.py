from chimerax.core.commands import CmdDesc, DynamicEnum, ListOf, register

def get_test_names(session):
    names = ["all"]
    for name in session.test_manager.tests:
        names.append(name)
    
    return names

def register_test_command(logger):
    desc = CmdDesc(
        optional=[(
            "test_names",
            ListOf(
                DynamicEnum(
                    lambda session=logger.session: get_test_names(session)
                )
            )
        )],
        synopsis="test the specifed component or 'all'",
    )
    
    register("test", desc, test)

def test(session, test_names=["all"]):
    from unittest import TestSuite, TextTestRunner
    
    suite = TestSuite()
    runner = TextTestRunner()    
    
    if any(name == "all" for name in test_names):
        names = get_test_names(session)[1:]
    else:
        names = test_names
    
    cls_by_name = {}
    for name in names:
        case = session.test_manager.tests[name].run_provider(session, name, session.test_manager)
        cls_by_name[name] = case.addTests(suite)
    
    results = runner.run(suite)

    results_by_name = {}
    for name, test_classes in cls_by_name.items():
        results_by_name[name] = {}
        for test_class in test_classes:
            added_test = False
            for fail, exception in results.failures:
                if test_class is fail:
                    results_by_name[name][test_class] = ("fail", exception)
                    added_test = True
                    break
            
            for error, exception in results.errors:
                if test_class is error:
                    results_by_name[name][test_class] = ("error", exception)
                    added_test = True
                    break
    
            for fail, exception in results.expectedFailures:
                if test_class is fail:
                    results_by_name[name][test_class] = ("expected_failure", exception)
                    added_test = True
                    break
                
            for success in results.unexpectedSuccesses:
                if test_class is success:
                    results_by_name[name][test_class] = ("unexpected_success", "I didn't expect to get this far...")
                    added_test = True
                    break
                
            for skip, reason in results.skipped:
                if test_class is skip:
                    results_by_name[name][test_class] = ("skip", reason)
                    added_test = True
                    break
            
            if not added_test:
                results_by_name[name][test_class] = ("success", "success!")
        
    return results_by_name
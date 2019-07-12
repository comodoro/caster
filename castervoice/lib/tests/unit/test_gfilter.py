import unittest

from dragonfly import Choice
from castervoice.lib import settings
from castervoice.lib.dfplus.merge.mergerule import MergeRule
from castervoice.lib.dfplus.merge.mergepair import MergeInf, MergePair
from castervoice.lib.dfplus.merge import gfilter
from castervoice.lib.tests.mocks import MockAction

test_action = MockAction()

class TestMergeRule(MergeRule):
    mapping = {
        "my hovercraft is full of <something>": test_action,
        "my place bouncy bouncy": test_action,
    }

    extras = [
        Choice("something", {
            "eels": True,
            "dung": 0,
            "spam": "spam",
        }),
    ]

    defaults = {
        "something": "eels",
    }

original_rule = TestMergeRule()


class TestGlobalFilter(unittest.TestCase):

    test_rule = None
    filter_defs_path = settings.SETTINGS["paths"]["SIMPLIFIED_FILTER_RULES_PATH"]

    @classmethod
    def tearDownClass(cls):
        settings.SETTINGS["paths"]["SIMPLIFIED_FILTER_RULES_PATH"] = cls.filter_defs_path
        reload(gfilter)

    def setUp(self):
        self.test_rule = original_rule.copy()
        del self.test_rule.mapping_actual()["display available commands"]
        self.test_merge_pair = MergePair(MergeInf.BOOT, MergeInf.GLOBAL,
                self.test_rule, None, False)

    def tearDown(self):
        pass

    def test_replace_spec_words(self):
        gfilter.DEFS = gfilter.GlobalFilterDefs('<<<SPEC>>>\nmy -> your'.splitlines())
        self.assertListEqual(self.test_rule.mapping_actual().keys(), original_rule.mapping_actual().keys())
        gfilter.run_on(self.test_rule)
        mapping = {
            "your hovercraft is full of <something>": MockAction(),
            "your place bouncy bouncy": MockAction()
        }
        del self.test_rule.mapping_actual()["display available commands"]
        self.assertListEqual(self.test_rule.mapping_actual().keys(), mapping.keys())

    def test_replace_extra_words(self):
        gfilter.DEFS = gfilter.GlobalFilterDefs('<<<EXTRA>>>\neels -> ducks'.splitlines())
        self.assertNotIn('ducks', self.test_rule.extras_actual()['something']._choices.keys())
        self.assertIn('eels', self.test_rule.extras_actual()['something']._choices.keys())
        gfilter.run_on(self.test_rule)
        self.assertIn('ducks', self.test_rule.extras_actual()['something']._choices.keys())
        self.assertNotIn('eels', self.test_rule.extras_actual()['something']._choices.keys())

    def test_replace_notspec_words(self):
        gfilter.DEFS = gfilter.GlobalFilterDefs('<<<NOT_SPECS>>>\neels -> ducks'.splitlines())
        self.assertNotIn('ducks', self.test_rule.extras_actual()['something']._choices.keys())
        self.assertIn('eels', self.test_rule.extras_actual()['something']._choices.keys())
        self.assertNotIn('ducks', self.test_rule.defaults_actual().values())
        self.assertIn('eels', self.test_rule.defaults_actual()['something'].values())
        gfilter.run_on(self.test_rule)
        self.assertIn('ducks', self.test_rule.extras_actual()['something']._choices.keys())
        self.assertNotIn('eels', self.test_rule.extras_actual()['something']._choices.keys())

    def test_do_not_replace_spec_substrings(self):
        gfilter.DEFS = gfilter.GlobalFilterDefs('<<<SPEC>>>\ncraft -> board'.splitlines())
        self.assertListEqual(self.test_rule.mapping_actual().keys(), original_rule.mapping_actual().keys())
        gfilter.run_on(self.test_rule)
        del self.test_rule.mapping_actual()["display available commands"]
        # Mapping should be unchanged
        self.assertListEqual(self.test_rule.mapping_actual().keys(), original_rule.mapping_actual().keys())

if __name__ == '__main__':
    unittest.main()

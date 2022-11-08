import unittest
import MemoRule

class TestMemoRuleMethods(unittest.TestCase):

    def test_MemoRule_Constructor(self):

        self.assertEqual('<class \'MemoRule.MemoRule\'>',str( type( MemoRule.MemoRule() ) ) )

        # bc duck-typing, we dont check data types, but just make sure that the fields are usable the way we want


        pass

    def test_str(self):
        self.assertIsNotNone(str(MemoRule.MemoRule()))

    def test_repr(self):
        self.assertIsNotNone(repr(MemoRule.MemoRule()))
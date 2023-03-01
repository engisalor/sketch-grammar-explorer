import unittest

from sgex.call.query import simple_query


def clean(string):
    return string.replace(" ", "")


class TestSimpleQueryInternal(unittest.TestCase):
    """Checks internal coherency of simple_query syntax."""

    def test_one_word(self):
        ref = 'q[lc="1" | lemma_lc="1"]'
        query = simple_query("1")
        self.assertEqual(clean(query), clean(ref))

    def test_two_word(self):
        ref = 'q[lc="1A" | lemma_lc="1A"][lc="1B" | lemma_lc="1B"]'
        query = simple_query("1A 1B")
        self.assertEqual(clean(query), clean(ref))

    def test_pipe(self):
        ref = 'q[lc="1" | lemma_lc="1"]|[lc="2" | lemma_lc="2"]'
        query = simple_query("1 | 2")
        self.assertEqual(clean(query), clean(ref))

    def test_single_hyphen(self):
        ref = 'q[lc="1A-1B" | lemma_lc="1A-1B"]'
        query = simple_query("1A-1B", False)
        self.assertEqual(clean(query), clean(ref))

    def test_single_hyphen_atomic(self):
        ref = 'q( [lc="1A-1B" | lemma_lc="1A-1B"] | [lc="1A" | lemma_lc="1A"] [lc="-" | lemma_lc="-"] [lc="1B" | lemma_lc="1B"] )'  # noqa: E501
        query = simple_query("1A-1B", True)
        self.assertEqual(clean(query), clean(ref))

    def test_double_hyphen(self):
        ref = 'q( [lc="1A1B" | lemma_lc="1A1B"] | [lc="1A" | lemma_lc="1A"] [lc="1B" | lemma_lc="1B"] | [lc="1A-1B" | lemma_lc="1A-1B"] )'  # noqa: E501
        query = simple_query("1A--1B", False)
        self.assertEqual(clean(query), clean(ref))

    def test_double_hypen_atomic(self):
        ref = 'q( [lc="1A1B" | lemma_lc="1A1B"] | [lc="1A" | lemma_lc="1A"] [lc="1B" | lemma_lc="1B"] | [lc="1A-1B" | lemma_lc="1A-1B"] | [lc="1A" | lemma_lc="1A"] [lc="-" | lemma_lc="-"] [lc="1B" | lemma_lc="1B"] )'  # noqa: E501
        query = simple_query("1A--1B", True)
        self.assertEqual(clean(query), clean(ref))

    def test_double_hyphen_pipe_atomic(self):
        ref = 'q( [lc="1A1B" | lemma_lc="1A1B"] | [lc="1A" | lemma_lc="1A"] [lc="1B" | lemma_lc="1B"] | [lc="1A-1B" | lemma_lc="1A-1B"] | [lc="1A" | lemma_lc="1A"] [lc="-" | lemma_lc="-"] [lc="1B" | lemma_lc="1B"] )[lc="1C" | lemma_lc="1C"]|[lc="2" | lemma_lc="2"]'  # noqa: E501
        query = simple_query("1A--1B 1C | 2")
        self.assertEqual(clean(query), clean(ref))

    def test_qmark(self):
        ref = 'q[lc="1A." | lemma_lc="1A."]'
        query = simple_query("1A?")
        self.assertEqual(clean(query), clean(ref))

    def test_asterisk_in_word(self):
        ref = 'q[lc="1A.*" | lemma_lc="1A.*"]'
        query = simple_query("1A*")
        self.assertEqual(clean(query), clean(ref))

    def test_asterisk_whole_word(self):
        ref = 'q[lc="1" | lemma_lc="1"][lc=".*" | lemma_lc=".*"][lc="3" | lemma_lc="3"]'
        query = simple_query("1 * 3")
        self.assertEqual(clean(query), clean(ref))


class TestSimpleQuerySkE(unittest.TestCase):
    """Checks coherency of simple_query syntax with CQL manually retrieved from SkE.

    Notes:
        - SkE `simple` queries appear to break when combining `--` and `|` in one query
            (ignoring `test_double_hyphen_pipe_atomic` in this class).
    """

    def test_one_word(self):
        ref = 'q[lc="gender" | lemma_lc="gender"]'
        query = simple_query("gender", False)
        self.assertEqual(clean(query), clean(ref))

    def test_two_word(self):
        ref = 'q[lc="gender" | lemma_lc="gender"][lc="based" | lemma_lc="based"]'
        query = simple_query("gender based", False)
        self.assertEqual(clean(query), clean(ref))

    def test_pipe(self):
        ref = 'q[lc="united" | lemma_lc="united"][lc="nations" | lemma_lc="nations"] | [lc="UN" | lemma_lc="UN"]'  # noqa: E501
        query = simple_query("united nations | UN", False)
        self.assertEqual(clean(query), clean(ref))

    def test_single_hyphen(self):
        ref = 'q[lc="gender-based" | lemma_lc="gender-based"]'
        query = simple_query("gender-based", False)
        self.assertEqual(clean(query), clean(ref))

    def test_double_hyphen(self):
        ref = 'q( [lc="genderbased" | lemma_lc="genderbased"] | [lc="gender" | lemma_lc="gender"] [lc="based" | lemma_lc="based"] | [lc="gender-based" | lemma_lc="gender-based"] )'  # noqa: E501
        query = simple_query("gender--based", False)
        self.assertEqual(clean(query), clean(ref))

    def test_qmark(self):
        ref = 'q[lc="gender." | lemma_lc="gender."]'
        query = simple_query("gender?", False)
        self.assertEqual(clean(query), clean(ref))

    def test_asterisk_in_word(self):
        ref = 'q[lc="gender.*" | lemma_lc="gender.*"]'
        query = simple_query("gender*", False)
        self.assertEqual(clean(query), clean(ref))

    def test_asterisk_whole_word(self):
        ref = 'q[lc="gender" | lemma_lc="gender"][lc=".*" | lemma_lc=".*"][lc="violence" | lemma_lc="violence"]'  # noqa: E501
        query = simple_query("gender * violence", False)
        self.assertEqual(clean(query), clean(ref))


if __name__ == "__main__":
    unittest.main()

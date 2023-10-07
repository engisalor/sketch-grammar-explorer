import unittest

from sgex import query


def clean(string):
    return string.replace(" ", "")


class TestSimpleQueryInternal(unittest.TestCase):
    """Checks internal coherency of simple_query syntax."""

    def test_one_word(self):
        ref = '[lc="1" | lemma_lc="1"]'
        q = query.simple_query("1")
        self.assertEqual(clean(q), clean(ref))

    def test_two_word(self):
        ref = '[lc="1A" | lemma_lc="1A"][lc="1B" | lemma_lc="1B"]'
        q = query.simple_query("1A 1B")
        self.assertEqual(clean(q), clean(ref))

    def test_pipe(self):
        ref = '[lc="1" | lemma_lc="1"]|[lc="2" | lemma_lc="2"]'
        q = query.simple_query("1 | 2")
        self.assertEqual(clean(q), clean(ref))

    def test_single_hyphen(self):
        ref = '[lc="1A-1B" | lemma_lc="1A-1B"]'
        q = query.simple_query("1A-1B", False)
        self.assertEqual(clean(q), clean(ref))

    def test_single_hyphen_atomic(self):
        ref = '( [lc="1A-1B" | lemma_lc="1A-1B"] | [lc="1A" | lemma_lc="1A"] [lc="-" | lemma_lc="-"] [lc="1B" | lemma_lc="1B"] )'  # noqa: E501
        q = query.simple_query("1A-1B", True)
        self.assertEqual(clean(q), clean(ref))

    def test_double_hyphen(self):
        ref = '( [lc="1A1B" | lemma_lc="1A1B"] | [lc="1A" | lemma_lc="1A"] [lc="1B" | lemma_lc="1B"] | [lc="1A-1B" | lemma_lc="1A-1B"] )'  # noqa: E501
        q = query.simple_query("1A--1B", False)
        self.assertEqual(clean(q), clean(ref))

    def test_double_hypen_atomic(self):
        ref = '( [lc="1A1B" | lemma_lc="1A1B"] | [lc="1A" | lemma_lc="1A"] [lc="1B" | lemma_lc="1B"] | [lc="1A-1B" | lemma_lc="1A-1B"] | [lc="1A" | lemma_lc="1A"] [lc="-" | lemma_lc="-"] [lc="1B" | lemma_lc="1B"] )'  # noqa: E501
        q = query.simple_query("1A--1B", True)
        self.assertEqual(clean(q), clean(ref))

    def test_double_hyphen_pipe_atomic(self):
        ref = '( [lc="1A1B" | lemma_lc="1A1B"] | [lc="1A" | lemma_lc="1A"] [lc="1B" | lemma_lc="1B"] | [lc="1A-1B" | lemma_lc="1A-1B"] | [lc="1A" | lemma_lc="1A"] [lc="-" | lemma_lc="-"] [lc="1B" | lemma_lc="1B"] )[lc="1C" | lemma_lc="1C"]|[lc="2" | lemma_lc="2"]'  # noqa: E501
        q = query.simple_query("1A--1B 1C | 2")
        self.assertEqual(clean(q), clean(ref))

    def test_qmark(self):
        ref = '[lc="1A." | lemma_lc="1A."]'
        q = query.simple_query("1A?")
        self.assertEqual(clean(q), clean(ref))

    def test_asterisk_in_word(self):
        ref = '[lc="1A.*" | lemma_lc="1A.*"]'
        q = query.simple_query("1A*")
        self.assertEqual(clean(q), clean(ref))

    def test_asterisk_whole_word(self):
        ref = '[lc="1" | lemma_lc="1"][lc=".*" | lemma_lc=".*"][lc="3" | lemma_lc="3"]'
        q = query.simple_query("1 * 3")
        self.assertEqual(clean(q), clean(ref))

    def test_simple_query_escape(self):
        refs = {
            '"': r'[lc="\\"" | lemma_lc="\\""]',
            "$": r'[lc="\$" | lemma_lc="\$"]',
            "(": r'[lc="\(" | lemma_lc="\("]',
            ")": r'[lc="\)" | lemma_lc="\)"]',
            "+": r'[lc="\+" | lemma_lc="\+"]',
            "[": r'[lc="\[" | lemma_lc="\["]',
            "]": r'[lc="\]" | lemma_lc="\]"]',
            "^": r'[lc="\^" | lemma_lc="\^"]',
            "{": r'[lc="\{" | lemma_lc="\{"]',
            "}": r'[lc="\}" | lemma_lc="\}"]',
            "\\": r'[lc="\\\\" | lemma_lc="\\\\"]',
        }
        for k in refs.keys():
            q = query.simple_query(k)
            self.assertEqual(clean(q), clean(refs[k]))


class TestSimpleQuerySkE(unittest.TestCase):
    """Checks coherency of simple_query syntax with CQL manually retrieved from SkE.

    Notes:
        - SkE `simple` queries appear to break when combining `--` and `|` in one query
            (ignoring `test_double_hyphen_pipe_atomic` in this class).
    """

    def test_one_word(self):
        ref = '[lc="gender" | lemma_lc="gender"]'
        q = query.simple_query("gender", False)
        self.assertEqual(clean(q), clean(ref))

    def test_two_word(self):
        ref = '[lc="gender" | lemma_lc="gender"][lc="based" | lemma_lc="based"]'
        q = query.simple_query("gender based", False)
        self.assertEqual(clean(q), clean(ref))

    def test_pipe(self):
        ref = '[lc="united" | lemma_lc="united"][lc="nations" | lemma_lc="nations"] | [lc="UN" | lemma_lc="UN"]'  # noqa: E501
        q = query.simple_query("united nations | UN", False)
        self.assertEqual(clean(q), clean(ref))

    def test_single_hyphen(self):
        ref = '[lc="gender-based" | lemma_lc="gender-based"]'
        q = query.simple_query("gender-based", False)
        self.assertEqual(clean(q), clean(ref))

    def test_double_hyphen(self):
        ref = '( [lc="genderbased" | lemma_lc="genderbased"] | [lc="gender" | lemma_lc="gender"] [lc="based" | lemma_lc="based"] | [lc="gender-based" | lemma_lc="gender-based"] )'  # noqa: E501
        q = query.simple_query("gender--based", False)
        self.assertEqual(clean(q), clean(ref))

    def test_qmark(self):
        ref = '[lc="gender." | lemma_lc="gender."]'
        q = query.simple_query("gender?", False)
        self.assertEqual(clean(q), clean(ref))

    def test_asterisk_in_word(self):
        ref = '[lc="gender.*" | lemma_lc="gender.*"]'
        q = query.simple_query("gender*", False)
        self.assertEqual(clean(q), clean(ref))

    def test_asterisk_whole_word(self):
        ref = '[lc="gender" | lemma_lc="gender"][lc=".*" | lemma_lc=".*"][lc="violence" | lemma_lc="violence"]'  # noqa: E501
        q = query.simple_query("gender * violence", False)
        self.assertEqual(clean(q), clean(ref))


class TestFuzzyQuery(unittest.TestCase):
    """Tests FuzzyQuery and related functions."""

    def test_fuzzy_query(self):
        f1 = "Before yesterday, it was fine, don't you think?"
        f2 = "Here's some cheese, meat, bread, apples, and pie."
        f3 = "We saw 1,000.99% more visitors at www.example.com yesterday"
        f4 = "I think there’s not (much) to do... anymore."
        f5 = " Here , take this. "
        f6 = "Well (then) - we, e.g., should (I think) take the aero-plane today."

        r1 = '"Before" "yesterday" []{,1} "it" "was" "fine" []{,3} "you" "think"'
        r2 = '"some" "cheese" []{,1} "meat" []{,1} "bread" []{,1} "apples" []{,1} "and" "pie"'  # noqa: E501
        r3 = '"We" "saw" []{,6} "more" "visitors" "at" []{,2} "yesterday"'
        r4 = '"I" "think" []{,2} "not" []{,1} "much" []{,1} "to" "do" []{,3} "anymore"'
        r5 = '"Here" []{,1} "take" "this"'
        r6 = '"Well" []{,1} "then" []{,2} "we" []{,6} "should" []{,1} "I" "think" []{,1} "take" "the" []{,3} "today"'  # noqa: E501

        self.assertEqual(query.fuzzy_query(f1), r1)
        self.assertEqual(query.fuzzy_query(f2), r2)
        self.assertEqual(query.fuzzy_query(f3), r3)
        self.assertEqual(query.fuzzy_query(f4), r4)
        self.assertEqual(query.fuzzy_query(f5), r5)
        self.assertEqual(query.fuzzy_query(f6), r6)


class TestCleanQuery(unittest.TestCase):
    def test_clean_query(self):
        q = "‘’‛‹›"
        ref = "'''''"
        self.assertEqual(query._clean_query(q), ref)
        q = "ʺ˝ˮ˵˶̋«»“”‟"
        ref = '"""""""""""'
        self.assertEqual(query._clean_query(q), ref)
        q = "abc\t\n\u00A0d"
        ref = "abc   d"
        self.assertEqual(query._clean_query(q), ref)
        q = " hello "
        ref = "hello"
        self.assertEqual(query._clean_query(q), ref)


if __name__ == "__main__":
    unittest.main()

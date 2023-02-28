import unittest

from sgex.call import job
from sgex.config import default


class TestJob(unittest.TestCase):
    def test_ttype_analysis(self):
        j = job.TTypeAnalysis("susanne", "noske", default)
        j.run()
        self.assertEqual(len(j.df), 81)

    def test_simple_freqs_query(self):
        j = job.SimpleFreqsQuery("sun*", "susanne", "noske", default)
        j.run()
        self.assertEqual(len(j.df), 39)


if __name__ == "__main__":
    unittest.main()

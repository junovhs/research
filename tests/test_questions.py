from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import questions


class QuestionTests(unittest.TestCase):
    def test_error_feed_is_not_zero_prior_literature(self):
        valid=b'<feed xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/"><opensearch:totalResults>0</opensearch:totalResults></feed>'
        self.assertEqual(questions.parse_feed(valid),0)
        with self.assertRaises(ValueError):
            questions.parse_feed(b'<feed><error>service unavailable</error></feed>')
        error=b'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/"><opensearch:totalResults>1</opensearch:totalResults><entry><id>http://arxiv.org/api/errors#incorrect_id_format</id></entry></feed>'
        with self.assertRaisesRegex(ValueError,'error feed'):
            questions.parse_feed(error)

    def test_unknown_availability_does_not_outrank_measured_zero(self):
        zero=dict(id='b',coherence=2,literature={'count':0})
        unknown=dict(id='a',coherence=2,literature={'count':None})
        self.assertLess(questions.selection_key(zero),questions.selection_key(unknown))

    def test_twenty_reproducible_executable_combinations(self):
        items=questions.proposals()
        self.assertEqual(items,questions.proposals())
        self.assertEqual(len(items),20)
        self.assertEqual(sum(q['baseline'] for q in items),4)
        self.assertEqual(len({frozenset((q['x'],q['y'])) for q in items}),20)
        self.assertTrue(all(q['x'] in questions.TERMS and q['y'] in questions.TERMS for q in items))


if __name__=='__main__':
    unittest.main()

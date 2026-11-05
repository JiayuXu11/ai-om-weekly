"""Integrity guards for editorial artifacts; no network required."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from render_dashboard import render


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'examples/report.json').read_text(encoding='utf-8'))

    def test_full_report_and_visible_likes(self):
        output = render(self.data)
        self.assertIn('data-dimension="ideas"', output)
        self.assertEqual(output.count('class="likes-badge"'), 5)
        self.assertEqual(output.count('class="sources"'), 32)

    def test_missing_om_cannot_be_full(self):
        self.data['sections'][3]['items'].pop()
        with self.assertRaises(ValueError):
            render(self.data)

    def test_ideas_cannot_cite_missing_event(self):
        self.data['sections'][4]['items'][0]['evidence_ids'] = ['invented']
        with self.assertRaises(ValueError):
            render(self.data)

    def test_unsafe_source_rejected(self):
        self.data['sections'][0]['items'][0]['sources'][0]['url'] = 'javascript:alert(1)'
        with self.assertRaises(ValueError):
            render(self.data)

    def test_like_order_rejected(self):
        self.data['sections'][2]['items'][1]['metrics']['likes'] = 999999
        with self.assertRaises(ValueError):
            render(self.data)

    def test_outside_window_rejected(self):
        self.data['sections'][3]['items'][0]['event_date'] = '2020-01-01'
        with self.assertRaises(ValueError):
            render(self.data)

    def test_no_ideas_is_valid(self):
        self.data['sections'][4]['items'] = []
        self.assertIn('data-dimension="ideas"', render(self.data))

    def test_untrusted_text_escaped(self):
        self.data['sections'][0]['items'][0]['title'] = '<script>bad()</script>'
        output = render(self.data)
        self.assertIn('&lt;script&gt;bad()', output)
        self.assertNotIn('<script>bad()', output)


if __name__ == '__main__':
    unittest.main()

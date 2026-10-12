import contextlib
import copy
import io
import json
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'argus'
spec = spec_from_file_location('render_report', SKILL / 'scripts/render_report.py')
module = module_from_spec(spec)
spec.loader.exec_module(module)


def load(name):
    return json.loads((SKILL / 'examples' / name).read_text(encoding='utf-8'))


def live_report():
    data = load('example-output.json')
    data['research_mode'] = 'live'
    data['accessed_on'] = '2026-10-12'
    data['evidence'] = [{'claim': 'Pricing page lists three plans', 'status': 'verified', 'confidence': 'high',
                         'source_url': 'https://example.com/pricing', 'accessed_on': '2026-10-12'}]
    for channel in data['channels']:
        channel['basis'] = 'evidence'
    return data


class ScoreTests(unittest.TestCase):
    def test_bounds(self):
        self.assertEqual(module.score({key: 5 for key in module.WEIGHTS}), 100)
        self.assertEqual(module.score({key: 1 for key in module.WEIGHTS}), 20)

    def test_weights_sum_to_twenty(self):
        self.assertEqual(sum(module.WEIGHTS.values()), 20)

    def test_matches_documented_formula(self):
        values = {'icp_fit': 4, 'intent': 3, 'reachability': 4, 'speed': 4, 'cost': 5, 'effort': 3, 'risk': 3}
        formula = round(20 * (.25 * 4 + .20 * 3 + .15 * 4 + .15 * 4 + .10 * 5 + .10 * 3 + .05 * 3))
        self.assertEqual(module.score(values), formula)

    def test_rejects_bad_values(self):
        base = {key: 3 for key in module.WEIGHTS}
        for bad in (6, 0, 3.5, True, '3', None):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                module.score({**base, 'intent': bad})

    def test_rejects_missing_or_extra_keys(self):
        base = {key: 3 for key in module.WEIGHTS}
        with self.assertRaises(ValueError):
            module.score({k: v for k, v in base.items() if k != 'risk'})
        with self.assertRaises(ValueError):
            module.score({**base, 'vibes': 5})


class ExampleTests(unittest.TestCase):
    def test_examples_render_without_warnings(self):
        for name in ('example-output.json', 'example-output.tr.json'):
            with self.subTest(name=name):
                data = load(name)
                module.validate(data)
                self.assertEqual(module.lint(data), [])
                self.assertIn('# Argus —', module.render(data))

    def test_shipped_reports_are_in_sync(self):
        for source, target in (('example-output.json', 'example-report.md'), ('example-output.tr.json', 'example-report.tr.md')):
            with self.subTest(target=target):
                expected = module.render(load(source))
                actual = (SKILL / 'examples' / target).read_text(encoding='utf-8')
                self.assertEqual(actual, expected, 'Regenerate with `make examples`')

    def test_template_renders(self):
        self.assertIn('# Argus — Your product', module.render(copy.deepcopy(module.TEMPLATE)))


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.data = load('example-output.json')

    def test_hypothesis_only_rejects_evidence(self):
        self.data['evidence'] = [{'claim': 'oops'}]
        with self.assertRaises(ValueError):
            module.render(self.data)

    def test_bad_mode(self):
        self.data['research_mode'] = 'vibes'
        with self.assertRaises(ValueError):
            module.render(self.data)

    def test_missing_product_name(self):
        del self.data['product_name']
        with self.assertRaises(ValueError):
            module.validate(self.data)

    def test_not_an_object(self):
        with self.assertRaises(ValueError):
            module.validate([])

    def test_all_problems_reported_together(self):
        self.data['research_mode'] = 'vibes'
        self.data['channels'][0]['scores']['intent'] = 9
        with self.assertRaises(ValueError) as ctx:
            module.validate(self.data)
        message = str(ctx.exception)
        self.assertIn('research_mode', message)
        self.assertIn('channels[1]', message)

    def test_live_verified_needs_url_and_date(self):
        data = live_report()
        del data['evidence'][0]['source_url']
        with self.assertRaises(ValueError):
            module.validate(data)
        data = live_report()
        del data['evidence'][0]['accessed_on']
        with self.assertRaises(ValueError):
            module.validate(data)

    def test_live_rejects_non_http_urls(self):
        for bad in ('javascript:alert(1)', 'ftp://x.com/a', 'https://x.com/a b', 'not a url', 'https://x.com/<a>'):
            data = live_report()
            data['evidence'][0]['source_url'] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                module.validate(data)

    def test_rejects_bad_dates(self):
        for bad in ('2026-13-01', '20261012', '12/10/2026', 'today'):
            data = live_report()
            data['accessed_on'] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                module.validate(data)

    def test_inference_needs_no_url(self):
        data = live_report()
        data['evidence'].append({'claim': 'Likely seasonal', 'status': 'inference', 'confidence': 'low'})
        module.validate(data)

    def test_live_report_valid(self):
        data = live_report()
        module.validate(data)
        self.assertEqual(module.lint(data), [])
        self.assertIn('<https://example.com/pricing>', module.render(data))

    def test_wrong_types(self):
        for key, value in (('channels', 'nope'), ('weeks', {}), ('risks', 'a'), ('copy', []), ('snapshot', 'x')):
            data = load('example-output.json')
            data[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                module.validate(data)


class LintTests(unittest.TestCase):
    def setUp(self):
        self.data = load('example-output.json')

    def warnings(self):
        return ' | '.join(module.lint(self.data))

    def test_clean(self):
        self.assertEqual(module.lint(self.data), [])

    def test_no_48h_experiment(self):
        for e in self.data['experiments']:
            e['within_48h'] = False
        self.assertIn('within_48h', self.warnings())

    def test_experiment_count(self):
        self.data['experiments'].pop()
        self.assertIn('Expected 5 experiments', self.warnings())

    def test_missing_gate_and_kill_criteria(self):
        del self.data['weeks'][0]['gate']
        del self.data['kill_criteria']
        self.assertIn('Week 1 has no stop/go gate', self.warnings())
        self.assertIn('kill criteria', self.warnings())

    def test_missing_disconfirming(self):
        del self.data['disconfirming']
        self.assertIn('disconfirming', self.warnings())

    def test_typo_field_is_flagged(self):
        self.data['experiments'][0]['decision_gates'] = 'x'
        self.assertIn('decision_gates', self.warnings())

    def test_live_without_evidence(self):
        self.data['research_mode'] = 'live'
        self.assertIn('evidence ledger is empty', self.warnings())

    def test_live_assumption_top_channel(self):
        data = live_report()
        data['channels'][0]['basis'] = 'assumption'
        self.assertIn('assumptions', ' | '.join(module.lint(data)))

    def test_too_few_promotable_channels(self):
        for channel in self.data['channels'][:3]:
            channel['promotion_allowed'] = False
        self.assertIn('Fewer than 2', self.warnings())


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.data = load('example-output.json')

    def test_roles_skip_prohibited_channels(self):
        result = module.render(self.data)
        lines = {line.split('|')[1].strip(): line for line in result.splitlines() if line.startswith('| ') and '/' not in line[:4]}
        self.assertIn('Participate only', lines['Subreddit that bans tool promotion'])
        self.assertIn('Validate now', lines['Founder communities (participation-first)'])
        self.assertIn('Validate now', lines['Content on collecting feedback'])
        self.assertIn('After checkpoint', lines['Launch directories'])

    def test_ranked_descending_and_stable(self):
        ranked = module._ranked(self.data)
        points = [p for p, _ in ranked]
        self.assertEqual(points, sorted(points, reverse=True))
        tied = copy.deepcopy(self.data)
        tied['channels'] = [{'name': n, 'scores': {k: 3 for k in module.WEIGHTS}} for n in ('B', 'A', 'C')]
        self.assertEqual([c['name'] for _, c in module._ranked(tied)], ['B', 'A', 'C'])

    def test_language_override(self):
        self.assertIn('## Karar', module.render(self.data, 'tr'))
        self.assertIn('## Verdict', module.render(self.data, 'en'))
        with self.assertRaises(ValueError):
            module.render(self.data, 'xx')

    def test_hypothesis_banner(self):
        self.assertIn('Nothing in this report is verified', module.render(self.data))
        self.assertNotIn('Nothing in this report is verified', module.render(live_report()))

    def test_untrusted_text_cannot_break_structure(self):
        self.data['channels'][0]['name'] = 'evil | name\n## injected'
        self.data['summary'] = '<script>alert(1)</script>\n# Fake heading'
        self.data['copy']['launch_post'] = 'line one\n# heading\n<img src=x>'
        result = module.render(self.data)
        self.assertNotIn('\n## injected', result)
        self.assertNotIn('\n# Fake heading', result)
        self.assertNotIn('<script>', result)
        self.assertNotIn('<img', result)
        self.assertIn('evil \\| name ## injected', result)
        self.assertIn('> # heading', result)

    def test_budget_formatting(self):
        self.data['experiments'][0]['budget_usd'] = 25.5
        self.assertIn('Budget ceiling: $25.5', module.render(self.data))


class CliTests(unittest.TestCase):
    def run_cli(self, *args, stdin=None):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            if stdin is not None:
                import sys
                original = sys.stdin
                sys.stdin = io.StringIO(stdin)
            try:
                code = module.main(list(args))
            except SystemExit as exc:
                code = exc.code
            finally:
                if stdin is not None:
                    sys.stdin = original
        return code, out.getvalue(), err.getvalue()

    def example(self):
        return str(SKILL / 'examples/example-output.json')

    def test_render_to_stdout(self):
        code, out, _ = self.run_cli(self.example())
        self.assertEqual(code, 0)
        self.assertIn('# Argus — FormNest', out)

    def test_check(self):
        code, out, _ = self.run_cli(self.example(), '--check')
        self.assertEqual((code, out.strip()), (0, 'OK'))

    def test_template_round_trips(self):
        code, out, _ = self.run_cli('--template')
        self.assertEqual(code, 0)
        code, out, _ = self.run_cli('-', stdin=out)
        self.assertEqual(code, 0)
        self.assertIn('# Argus — Your product', out)

    def test_strict_fails_on_warnings(self):
        code, _, err = self.run_cli(str(SKILL / 'examples/example-output.json'), '--strict', '--check')
        self.assertEqual(code, 0)
        data = load('example-output.json')
        data['kill_criteria'] = []
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'f.json'
            path.write_text(json.dumps(data), encoding='utf-8')
            code, _, err = self.run_cli(str(path), '--strict')
            self.assertEqual(code, 1)
            self.assertIn('kill criteria', err)

    def test_errors_exit_one(self):
        code, _, err = self.run_cli('-', stdin='{not json')
        self.assertEqual(code, 1)
        self.assertIn('Error', err)
        code, _, err = self.run_cli('/no/such/file.json')
        self.assertEqual(code, 1)

    def test_output_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'out.md'
            code, out, _ = self.run_cli(self.example(), '-o', str(target), '--lang', 'tr')
            self.assertEqual(code, 0)
            self.assertIn('## Karar', target.read_text(encoding='utf-8'))

    def test_input_required(self):
        code, _, _ = self.run_cli()
        self.assertEqual(code, 2)


class SkillMetadataTests(unittest.TestCase):
    def test_frontmatter_name_matches_folder(self):
        text = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
        front = text.split('---')[1]
        self.assertIn(f'name: {SKILL.name}', front)
        description = next(l for l in front.splitlines() if l.startswith('description:'))
        self.assertLessEqual(len(description) - len('description: '), 1024)

    def test_referenced_files_exist(self):
        text = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
        for line in text.splitlines():
            if line.startswith('- `') and '`:' in line:
                rel = line.split('`')[1]
                self.assertTrue((SKILL / rel).exists(), rel)


if __name__ == '__main__':
    unittest.main()

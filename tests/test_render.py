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
    data['product_url'] = 'https://example.com'
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

    def test_live_assumption_top_channel_is_a_note_not_a_warning(self):
        data = live_report()
        data['channels'][0]['basis'] = 'assumption'
        self.assertIn('assumptions', ' | '.join(module.notes(data)))
        self.assertNotIn('assumptions', ' | '.join(module.lint(data)))

    def test_too_few_fast_channels(self):
        for channel in self.data['channels']:
            channel['scores']['speed'] = 2
        self.assertIn('within weeks', ' | '.join(module.notes(self.data)))
        self.assertNotIn('within weeks', self.warnings())

    def test_too_few_promotable_channels(self):
        for channel in self.data['channels'][:3]:
            channel['promotion_allowed'] = False
        self.assertIn('Fewer than 2', ' | '.join(module.notes(self.data)))


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.data = load('example-output.json')

    def test_roles(self):
        result = module.render(self.data)
        lines = {line.split('|')[1].strip(): line for line in result.splitlines() if line.startswith('| ') and '/' not in line[:4]}
        self.assertIn('Participate only', lines['Subreddit that bans tool promotion'])
        self.assertIn('Validate now', lines['Direct conversations with founders you know'])
        self.assertIn('Validate now', lines['Founder communities (participation-first)'])
        self.assertIn('After checkpoint', lines['Launch directories'])
        self.assertIn('Background (slow payoff)', lines['Content on collecting feedback'])

    def test_slow_channel_never_takes_a_validation_slot(self):
        channels = [{'name': n, 'scores': {**{k: 3 for k in module.WEIGHTS}, 'speed': sp, 'icp_fit': ic}}
                    for n, sp, ic in (('Slow but top', 1, 5), ('Fast A', 4, 4), ('Fast B', 3, 3), ('Fast C', 3, 2))]
        roles = module._roles(module._ranked({'channels': channels}))
        by_name = {c['name']: roles[id(c)] for c in channels}
        self.assertEqual(by_name, {'Slow but top': 'slow', 'Fast A': 'validate', 'Fast B': 'validate', 'Fast C': 'checkpoint'})

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

    def test_free_text_budget_wins_and_supports_any_currency(self):
        self.data['experiments'][0]['budget_usd'] = 25.5
        self.data['experiments'][0]['budget'] = '500 TL'
        self.assertIn('Budget ceiling: 500 TL', module.render(self.data))
        self.assertIn('500 TL', module.render_html(self.data))
        self.data['experiments'][0]['budget'] = ' '
        with self.assertRaises(ValueError):
            module.validate(self.data)

    def test_assumption_tag_only_in_live_mode(self):
        self.assertNotIn('[assumption]', module.render(self.data))
        self.assertIn('Every score here rests on assumptions', module.render(self.data))
        live = live_report()
        live['channels'][0]['basis'] = 'assumption'
        self.assertIn('[assumption]', module.render(live))
        self.assertNotIn('Every score here rests on assumptions', module.render(live))


class ResearchGateTests(unittest.TestCase):
    def test_live_report_requires_the_url_the_user_gave(self):
        data = live_report()
        del data['product_url']
        for render in (module.render, module.render_html):
            with self.subTest(render=render.__name__), self.assertRaises(ValueError) as ctx:
                render(data)
            self.assertIn('requires product_url', str(ctx.exception))

    def test_live_with_url_is_fine(self):
        module.validate(live_report())

    def test_hypothesis_only_needs_no_url(self):
        data = load('example-output.json')
        self.assertNotIn('product_url', data)
        module.validate(data)

    def test_bad_urls_rejected(self):
        for bad in ('example.com', 'javascript:alert(1)', 'ftp://example.com', '', None, 'https://x.com/<b>'):
            data = live_report()
            data['product_url'] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                module.validate(data)

    def test_url_is_shown_and_escaped(self):
        data = live_report()
        data['product_url'] = 'https://example.com/?q="x'
        self.assertIn('<https://example.com/?q="x>', module.render(data))
        page = module.render_html(data)
        self.assertIn('&quot;x', page)
        self.assertNotIn('href="https://example.com/?q="x', page)
        self.assertIn('Ürün URL', module.render(data, 'tr'))

    def test_cli_rejects_live_without_url(self):
        import tempfile
        data = live_report()
        del data['product_url']
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'f.json'
            path.write_text(json.dumps(data), encoding='utf-8')
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = module.main([str(path), '--check'])
        self.assertEqual(code, 1)
        self.assertIn('no research', err.getvalue())

    def test_skill_states_the_gate(self):
        text = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
        self.assertIn('Never research unless the user gave you a URL', text)
        self.assertIn('product_url', text)


class ExtraFieldsTests(unittest.TestCase):
    def setUp(self):
        self.data = load('example-output.json')

    def test_unknown_promotion_cannot_take_a_sprint_slot(self):
        self.data['channels'][0]['promotion_allowed'] = 'unknown'
        roles = module._roles(module._ranked(self.data))
        by_name = {c['name']: roles[id(c)] for c in self.data['channels']}
        self.assertEqual(by_name['Subreddit that bans tool promotion'], 'participate')
        self.assertEqual(by_name[self.data['channels'][0]['name']], 'verify')
        self.assertIn('Read the rules first', module.render(self.data))
        self.assertIn('badge verify', module.render_html(self.data))
        self.assertFalse(any('unknown for' in n for n in module.notes(self.data)), 'offline: unknown is expected')
        live = live_report()
        live['channels'][0]['promotion_allowed'] = 'unknown'
        self.assertTrue(any('unknown for' in n for n in module.notes(live)))
        self.assertFalse(any('unknown' in w or 'within weeks' in w for w in module.lint(live)), 'notes must not block --strict')

    def test_promotion_allowed_rejects_other_values(self):
        for bad in ('maybe', 1, None):
            self.data['channels'][0]['promotion_allowed'] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                module.validate(self.data)

    def test_new_sections_render_in_both_formats(self):
        md, page = module.render(self.data), module.render_html(self.data)
        for needle in ('Fixes on your own pages', 'Assumptions', 'What was not checked', 'Budget plan', 'no rate cards were verified'):
            self.assertIn(needle, md)
            self.assertIn(needle, page)
        self.assertIn('id="audit"', page)
        self.assertIn('id="budget"', page)

    def test_outreach_draft_renders_escaped(self):
        self.data['copy']['outreach_draft'] = 'Hi <b>Sam</b>\nquick question'
        md, page = module.render(self.data), module.render_html(self.data)
        self.assertIn('Outreach draft (one to one)', md)
        self.assertIn('> Hi &lt;b&gt;Sam', md)
        self.assertIn('Hi &lt;b&gt;Sam&lt;/b&gt;', page)
        self.assertIn('Birebir mesaj taslağı', module.render(self.data, 'tr'))

    def test_section_lists_must_be_strings(self):
        for key in ('assumptions', 'limits', 'budget_plan', 'audit_findings'):
            data = load('example-output.json')
            data[key] = [1]
            with self.subTest(key=key), self.assertRaises(ValueError):
                module.validate(data)

    def test_source_type_and_note(self):
        data = live_report()
        data['evidence'][0]['source_type'] = 'secondary'
        data['evidence'][0]['note'] = 'contradicts the pricing page'
        md, page = module.render(data), module.render_html(data)
        self.assertIn('(secondary)', md)
        self.assertIn('contradicts the pricing page', md)
        self.assertIn('contradicts the pricing page', page)
        data['evidence'][0]['source_type'] = 'rumor'
        with self.assertRaises(ValueError):
            module.validate(data)

    def test_two_channels_are_enough(self):
        self.data['channels'] = self.data['channels'][1:3]
        self.assertFalse(any('Expected 2-8' in w for w in module.lint(self.data)))
        self.data['channels'] = self.data['channels'][:1]
        self.assertTrue(any('Expected 2-8' in w for w in module.lint(self.data)))


class HtmlTests(unittest.TestCase):
    def setUp(self):
        self.data = load('example-output.json')

    def test_renders_all_sections(self):
        result = module.render_html(self.data)
        self.assertTrue(result.startswith('<!doctype html>'))
        for anchor in ('verdict', 'snapshot', 'icps', 'evidence', 'against', 'channels', 'sprint', 'copy', 'experiments', 'risks'):
            self.assertIn(f'id="{anchor}"', result)
        self.assertIn('Founder communities (participation-first)', result)
        self.assertIn('badge validate', result)
        self.assertIn('badge participate', result)

    def test_is_self_contained(self):
        result = module.render_html(live_report())
        self.assertNotIn('<script', result)
        self.assertNotIn('<link', result)
        self.assertNotIn('@import', result)
        self.assertNotIn('src="http', result)
        self.assertIn("default-src 'none'", result)
        # The only outbound references are the product URL and the evidence link, both nofollow.
        self.assertEqual(result.count('href="http'), 2)
        self.assertEqual(result.count('rel="noopener noreferrer nofollow"'), 2)

    def test_untrusted_text_is_escaped(self):
        self.data['product_name'] = '<img src=x onerror=alert(1)>'
        self.data['summary'] = '"><script>alert(1)</script>'
        self.data['channels'][0]['name'] = '<b>x</b>'
        self.data['copy']['launch_post'] = '<iframe src=//evil></iframe>\n# heading'
        self.data['weeks'][0]['actions'] = ['<svg onload=alert(1)>']
        result = module.render_html(self.data)
        for needle in ('<img src=x', '<script>alert', '<b>x</b>', '<iframe', '<svg onload'):
            self.assertNotIn(needle, result)
        self.assertIn('&lt;script&gt;', result)

    def test_url_attribute_cannot_break_out(self):
        data = live_report()
        data['evidence'][0]['source_url'] = 'https://example.com/?q="onmouseover=alert(1)'
        result = module.render_html(data)
        self.assertNotIn('"onmouseover', result)
        self.assertIn('&quot;onmouseover', result)

    def test_language_and_banner(self):
        self.assertIn('<html lang="tr">', module.render_html(self.data, 'tr'))
        self.assertIn('Karar', module.render_html(self.data, 'tr'))
        self.assertIn('class="banner"', module.render_html(self.data))
        self.assertNotIn('class="banner"', module.render_html(live_report()))
        with self.assertRaises(ValueError):
            module.render_html(self.data, 'xx')

    def test_validates_first(self):
        self.data['research_mode'] = 'vibes'
        with self.assertRaises(ValueError):
            module.render_html(self.data)

    def test_score_bar_width_matches_score(self):
        top = module._ranked(self.data)[0][0]
        self.assertIn(f'width:{top}%', module.render_html(self.data))

    def test_shipped_html_in_sync(self):
        for source, target in (('example-output.json', 'example-report.html'), ('example-output.tr.json', 'example-report.tr.html')):
            with self.subTest(target=target):
                actual = (SKILL / 'examples' / target).read_text(encoding='utf-8')
                self.assertEqual(actual, module.render_html(load(source)), 'Regenerate with `make examples`')


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

    def test_notes_print_but_do_not_fail_strict(self):
        import tempfile
        data = live_report()
        data['channels'][0]['basis'] = 'assumption'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'f.json'
            path.write_text(json.dumps(data), encoding='utf-8')
            code, out, err = self.run_cli(str(path), '--check', '--strict')
        self.assertEqual((code, out.strip()), (0, 'OK'))
        self.assertIn('note:', err)

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

    def test_html_by_extension_and_flag(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'out.html'
            code, _, _ = self.run_cli(self.example(), '-o', str(target))
            self.assertEqual(code, 0)
            self.assertTrue(target.read_text(encoding='utf-8').startswith('<!doctype html>'))
            md = Path(tmp) / 'out.md'
            self.run_cli(self.example(), '-o', str(md))
            self.assertTrue(md.read_text(encoding='utf-8').startswith('# Argus'))
        code, out, _ = self.run_cli(self.example(), '--html')
        self.assertTrue(out.startswith('<!doctype html>'))

    def test_streams_are_switched_to_utf8(self):
        # Reports contain "—", "⚠" and "⏱"; a legacy Windows console would otherwise raise UnicodeEncodeError.
        class Stream(io.StringIO):
            def reconfigure(self, **kwargs):
                self.kwargs = kwargs
        out, err = Stream(), Stream()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(module.main(['--template']), 0)
        self.assertEqual(out.kwargs['encoding'], 'utf-8')
        self.assertEqual(err.kwargs['encoding'], 'utf-8')

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

    def test_frontmatter_is_portable(self):
        # claude.ai uploads and the Skills API reject frontmatter keys outside the Agent Skills spec.
        text = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
        self.assertTrue(text.startswith('---\n'), 'frontmatter must start on line 1')
        front = text.split('---')[1]
        keys = {line.split(':')[0] for line in front.splitlines() if line and not line.startswith(' ')}
        self.assertLessEqual(keys, {'name', 'description', 'license', 'compatibility', 'metadata', 'allowed-tools'})
        self.assertLessEqual(len(front.split('compatibility:')[1].split('\n')[0]), 500)

    def test_howto_covers_every_platform(self):
        for name in ('HOWTO.md', 'HOWTO.tr.md'):
            text = (ROOT / name).read_text(encoding='utf-8')
            for platform in ('OpenCode', 'Claude Code', 'Codex', 'Hermes', 'ChatGPT', 'Claude.ai'):
                self.assertIn(f'## {platform}', text.replace('## OpenAI Codex', '## Codex'), (name, platform))

    def test_referenced_files_exist(self):
        text = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
        for line in text.splitlines():
            if line.startswith('- `') and '`:' in line:
                rel = line.split('`')[1]
                self.assertTrue((SKILL / rel).exists(), rel)

    def test_documented_description_length_is_current(self):
        import re
        front = (SKILL / 'SKILL.md').read_text(encoding='utf-8').split('---')[1]
        line = next(l for l in front.splitlines() if l.startswith('description:'))
        actual = len(line) - len('description: ')
        for name in ('HOWTO.md', 'HOWTO.tr.md', 'argus/references/platforms.md'):
            text = (ROOT / name).read_text(encoding='utf-8')
            stated = re.findall(r"description(?: is about|'ı yaklaşık) (\d{3})\b", text)
            self.assertTrue(stated, f'{name} should state the description length')
            for number in stated:
                self.assertLessEqual(abs(int(number) - actual), 10, f'{name}: says {number}, actual {actual}')

    def test_body_stays_within_the_recommended_size(self):
        # The Agent Skills spec recommends under 500 lines and about 5000 tokens for the body.
        body = (SKILL / 'SKILL.md').read_text(encoding='utf-8').split('---', 2)[2]
        self.assertLess(len(body.splitlines()), 500)
        self.assertLess(len(body.split()), 3000)


class TextFieldTests(unittest.TestCase):
    """A list or object in a free-text field would print as a Python repr in the report."""

    def setUp(self):
        self.data = load('example-output.json')

    def test_lists_and_objects_are_rejected_everywhere_a_string_is_expected(self):
        places = {
            'snapshot.problem': lambda d: d['snapshot'],
            'icps[1].alternatives': lambda d: d['icps'][0],
            'channels[1].rationale': lambda d: d['channels'][0],
            'weeks[1].gate': lambda d: d['weeks'][0],
            'copy.launch_post': lambda d: d['copy'],
            'experiments[1].kpi': lambda d: d['experiments'][0],
        }
        for label, holder in places.items():
            for bad in (['a', 'b'], {'k': 1}, 7):
                data = copy.deepcopy(self.data)
                holder(data)[label.split('.')[-1]] = bad
                with self.subTest(label=label, bad=bad), self.assertRaises(ValueError) as ctx:
                    module.validate(data)
                self.assertIn(f'{label} must be a string', str(ctx.exception))

    def test_null_means_absent(self):
        self.data['weeks'][0]['signal'] = None
        self.data['copy']['outreach_draft'] = None
        module.validate(self.data)
        out = module.render(self.data)
        self.assertNotIn(': None', out)
        self.assertNotIn('> None', out)

    def test_every_text_field_in_the_template_and_examples_is_a_string(self):
        for data in (load('example-output.json'), load('example-output.tr.json'), copy.deepcopy(module.TEMPLATE)):
            module.validate(data)

    def test_hypothesis_only_error_says_what_to_do(self):
        self.data['evidence'] = [{'claim': 'x'}]
        with self.assertRaises(ValueError) as ctx:
            module.validate(self.data)
        self.assertIn('assumptions', str(ctx.exception))


class WeakFitNoteTests(unittest.TestCase):
    def setUp(self):
        self.data = load('example-output.json')

    def test_shipped_examples_raise_no_notes(self):
        for name in ('example-output.json', 'example-output.tr.json'):
            self.assertEqual(module.notes(load(name)), [], name)

    def test_weak_audience_in_a_validation_slot_is_a_note_not_a_warning(self):
        channel = self.data['channels'][0]
        channel['scores']['icp_fit'] = 2
        notes = ' | '.join(module.notes(self.data))
        self.assertIn(f'"{channel["name"]}"', notes)
        self.assertIn('icp_fit is 2', notes)
        self.assertNotIn('icp_fit', ' | '.join(module.lint(self.data)))

    def test_weak_audience_outside_the_validation_slots_is_not_flagged(self):
        for channel in self.data['channels']:
            if channel['scores']['speed'] <= 2 or channel.get('promotion_allowed') is False:
                channel['scores']['icp_fit'] = 1
        self.assertEqual(module.notes(self.data), [])


class EvalsTests(unittest.TestCase):
    def setUp(self):
        self.evals = json.loads((ROOT / 'evals/evals.json').read_text(encoding='utf-8'))['evals']

    def test_every_scenario_is_complete_and_unique(self):
        ids = [e['id'] for e in self.evals]
        self.assertEqual(len(ids), len(set(ids)))
        for e in self.evals:
            self.assertTrue(e['prompt'].strip() and len(e['expectations']) >= 4, e['id'])

    def test_readme_counts_the_scenarios(self):
        words = {5: 'five', 6: 'six', 7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten', 11: 'eleven', 12: 'twelve'}
        readme = (ROOT / 'evals/README.md').read_text(encoding='utf-8')
        self.assertIn(f'holds {words[len(self.evals)]} scenarios', readme)


class SiteJsonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec_b = spec_from_file_location('build_site_json', ROOT / 'site/build_site_json.py')
        cls.builder = module_from_spec(spec_b)
        spec_b.loader.exec_module(cls.builder)
        cls.full = json.loads((ROOT / 'site/argus.json').read_text(encoding='utf-8'))
        cls.lite = json.loads((ROOT / 'site/argus.lite.json').read_text(encoding='utf-8'))

    def test_committed_files_are_current(self):
        data = self.builder.build()
        self.assertEqual((ROOT / 'site/argus.json').read_text(encoding='utf-8'), self.builder.dump(data), 'Run `make site`')
        self.assertEqual((ROOT / 'site/argus.lite.json').read_text(encoding='utf-8'), self.builder.dump(self.builder.lite(data)), 'Run `make site`')

    def test_version_matches_the_skill(self):
        text = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
        self.assertIn(f'version: "{self.full["version"]}"', text)
        released = [c['version'] for c in self.full['changelog'] if c['version'] != 'Unreleased']
        self.assertEqual(released[0], self.full['version'])

    def test_file_hashes_and_coverage(self):
        import hashlib
        on_disk = {p.relative_to(SKILL).as_posix() for p in SKILL.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        listed = {f['path'].removeprefix('argus/') for f in self.full['files']}
        self.assertEqual(on_disk, listed)
        for f in self.full['files']:
            self.assertEqual(hashlib.sha256(f['content'].encode('utf-8')).hexdigest(), f['sha256'], f['path'])
            self.assertEqual(len(f['content'].encode('utf-8')), f['bytes'])

    def test_every_text_is_bilingual(self):
        problems = []

        def walk(node, path=''):
            if isinstance(node, dict):
                if set(node) == {'en', 'tr'}:
                    problems.extend(f'{path}.{k}' for k in ('en', 'tr') if not str(node[k]).strip())
                else:
                    for key, value in node.items():
                        if key not in ('files', 'system_prompt', 'changelog'):
                            walk(value, f'{path}/{key}')
            elif isinstance(node, list):
                for i, value in enumerate(node):
                    walk(value, f'{path}[{i}]')
        walk(self.full)
        self.assertEqual(problems, [])

    def test_platforms_match_the_howto(self):
        howto = (ROOT / 'HOWTO.md').read_text(encoding='utf-8')
        for platform in self.full['platforms']:
            self.assertIn(platform['vendor_docs'], howto, platform['id'])
            self.assertTrue(platform['install']['steps'] and platform['first_prompt']['en'].strip())

    def test_nothing_private_leaks(self):
        raw = (ROOT / 'site/argus.json').read_text(encoding='utf-8')
        for needle in ('/Users/', 'ardakaanozcan', 'api_key', 'sk-'):
            self.assertNotIn(needle, raw)

    def test_lite_is_small_and_has_no_contents(self):
        self.assertTrue(all('content' not in f for f in self.lite['files']))
        self.assertNotIn('text', self.lite['system_prompt'])
        self.assertLess((ROOT / 'site/argus.lite.json').stat().st_size, 60 * 1024)
        self.assertEqual([f['path'] for f in self.lite['files']], [f['path'] for f in self.full['files']])

    def test_system_prompt_carries_the_research_gate(self):
        self.assertIn('Never research unless the user gave you a URL', self.full['system_prompt']['text'])
        self.assertNotIn('name: argus', self.full['system_prompt']['text'][:200], 'frontmatter must be stripped')


if __name__ == '__main__':
    unittest.main()

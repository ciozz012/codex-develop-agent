import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills' / 'develop-agent' / 'scripts' / 'read_handoff.py'
EXAMPLE = ROOT / 'examples' / 'employee-assistant' / 'docs' / 'agent' / 'plan.md'
MARKER = '**给新会话的接续指令**'


class ReadHandoffTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.plan = Path(directory.name) / '项目 计划.md'

    def read_handoff(self, path):
        before = path.read_bytes() if path.exists() else None
        result = subprocess.run(
            [sys.executable, '-X', 'utf8', str(SCRIPT), str(path)],
            cwd=self.plan.parent, capture_output=True, encoding='utf-8',
        )
        if before is None:
            self.assertFalse(path.exists())
        else:
            self.assertEqual(path.read_bytes(), before)
        return result

    def assert_instruction(self, path, expected):
        result = self.read_handoff(path)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), expected.splitlines())

    def assert_rejected(self, path):
        result = self.read_handoff(path)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertTrue(result.stderr.strip())

    def test_employee_assistant_example(self):
        lines = EXAMPLE.read_text(encoding='utf-8').splitlines()
        expected, = [line[2:] for line in lines if line.startswith('> 使用 `$develop-agent`')]
        self.assert_instruction(EXAMPLE, expected)

    def test_heading_with_bom_crlf_and_multiline_instruction(self):
        self.plan.write_bytes((
            '## 给新会话的接续指令\r\n\r\n'
            '> 先读取 `docs/agent/plan.md`。\r\n> 再核对两组样例。\r\n'
        ).encode('utf-8-sig'))
        self.assert_instruction(self.plan, '先读取 `docs/agent/plan.md`。\n再核对两组样例。')

    def test_fenced_examples_do_not_compete_with_the_real_instruction(self):
        for fence in ('```', '~~~'):
            with self.subTest(fence=fence):
                self.plan.write_text(
                    f'{fence}markdown\n{MARKER}\n> 示例。\n{fence}\n\n'
                    f'{MARKER}\n\n> 接续当前功能。\n', encoding='utf-8',
                )
                self.assert_instruction(self.plan, '接续当前功能。')

    def test_missing_or_ambiguous_instruction_is_rejected(self):
        cases = {
            'no marker': '> 这是一段普通引用。\n',
            'empty section': f'{MARKER}\n\n## 其他事项\n> 无关。\n',
            'two markers': f'{MARKER}\n> 第一项。\n\n{MARKER}\n> 第二项。\n',
            'two quote blocks': f'{MARKER}\n\n> 第一项。\n\n> 第二项。\n',
            'partial instruction': f'{MARKER}\n> 只设计功能一。\n实现留到下次。\n',
            'commented instruction': f'<!-- 已归档\n{MARKER}\n> 旧指令。\n-->\n',
        }
        for name, content in cases.items():
            with self.subTest(name=name):
                self.plan.write_text(content, encoding='utf-8')
                self.assert_rejected(self.plan)

    def test_missing_file_is_rejected(self):
        self.assert_rejected(self.plan)


if __name__ == '__main__':
    unittest.main()

"""Print the explicitly marked next instruction from a UTF-8 Markdown plan."""

import argparse
import re
import sys
from pathlib import Path


TITLE = '给新会话的接续指令'
MARKER = re.compile(
    rf' {{0,3}}(?:\*\*{TITLE}\*\*|#{{1,6}}[ \t]+{TITLE}(?:[ \t]+#+)?)[ \t]*'
)
FENCE = re.compile(r' {0,3}(`{3,}|~{3,})(.*)')
QUOTE = re.compile(r' {0,3}> ?(.*)')


def find_marker(lines):
    marker = None
    fence = ''
    in_comment = False
    for index, line in enumerate(lines):
        boundary = FENCE.fullmatch(line)
        if fence:
            if boundary and boundary[1].startswith(fence) and not boundary[2].strip():
                fence = ''
            continue
        if in_comment or line.lstrip().startswith('<!--'):
            in_comment = '-->' not in line
            continue
        if boundary:
            delimiter, info = boundary.groups()
            if delimiter[0] == '~' or '`' not in info:
                fence = delimiter
                continue
        if MARKER.fullmatch(line):
            if marker is not None:
                raise ValueError('计划中有多处接续指令标记，请核对当前项。')
            marker = index
    if marker is None:
        raise ValueError('未找到「给新会话的接续指令」标记，请查看计划中的当前项。')
    return marker


def read_handoff(plan):
    lines = plan.read_text(encoding='utf-8-sig').splitlines()
    index = find_marker(lines) + 1
    while index < len(lines) and not lines[index].strip():
        index += 1
    instruction = []
    while index < len(lines):
        match = QUOTE.fullmatch(lines[index])
        if not match:
            break
        instruction.append(match.group(1))
        index += 1
    text = '\n'.join(instruction).strip()
    if not text:
        raise ValueError('接续标记下缺少指令，请用一段以 > 开头的引用写明下一步。')
    if index < len(lines) and lines[index].strip():
        raise ValueError('接续指令的续行需带 >，下一段与指令之间请留空行。')
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index < len(lines) and QUOTE.fullmatch(lines[index]):
        raise ValueError('接续标记下有多段引用，请核对哪一段是当前指令。')
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path, help='项目里的 Markdown 计划路径')
    args = parser.parse_args()
    try:
        instruction = read_handoff(args.plan)
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        return 1
    if not sys.stdout.isatty():
        sys.stdout.reconfigure(encoding='utf-8')
    print(instruction)
    return 0


if __name__ == '__main__':
    sys.exit(main())

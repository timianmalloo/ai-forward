"""Current INSTALL instructions, excluding declared historical data."""
import re

_HISTORY = re.compile(
    r'(?m)^<details>\n<summary>Detailed deltas through revision \d+ — preserved history</summary>'
    r'\n\n```yaml\nchanges:\n'
    r'(?P<records>(?:(?!```|</?details>|</?summary>)[^\n]*\n)*)'
    r'```\n\n</details>\n?'
)


def current_install_body(text):
    body = text.split('\n---\n', 1)[-1] if text.startswith('---\n') else text

    def historical_data(match):
        entries = [line for line in match.group('records').splitlines()
                   if line.strip() and not line.lstrip().startswith('#')]
        # Account for every data line; never span a fence/container boundary.
        if entries and all(line.startswith('  - {') and line.rstrip().endswith('}')
                           for line in entries):
            return ''
        return match.group(0)

    return _HISTORY.sub(historical_data, body)

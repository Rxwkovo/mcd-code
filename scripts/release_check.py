#!/usr/bin/env python3
"""Check the actual submission files; never create orders or inject fake data."""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import re
import os
import struct
import subprocess
import sys
import urllib.request
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.package_source import source_files

DECLARATION_URL = 'https://raw.githubusercontent.com/M-China/mcd-developer-innovation-challenge/main/CONTEST_DECLARATION.md'
DECLARATION_SHA256 = 'cd28101bcb29cc8fb24b372fe91ce6b42c4a1487a54e01f7ade0c8c6a84241b7'


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--official', action='store_true', help='联网逐字节比对官方声明')
    parser.add_argument('--report', type=Path, help='保存不含凭据或业务响应的检查报告')
    args = parser.parse_args()
    checks, failures = {}, []

    def check(name, action):
        try:
            result = action()
            if result is False:
                raise ValueError('check failed')
            checks[name] = {'passed': True}
        except Exception as exc:
            checks[name] = {'passed': False, 'error_type': type(exc).__name__}
            failures.append(name)

    def required():
        for name in ['README.md','CONTEST_DECLARATION.md','MCP_INTEGRATION.md',
                     'mcp-config.example.json','SKILL.md','mcd.py','mcdcode/cli.py']:
            if not (ROOT/name).is_file():
                raise ValueError('required file missing')
    check('required_files', required)
    check('declaration_hash', lambda: hashlib.sha256((ROOT/'CONTEST_DECLARATION.md').read_bytes()).hexdigest() == DECLARATION_SHA256)
    if args.official:
        def official():
            with urllib.request.urlopen(DECLARATION_URL, timeout=20) as response:
                data = response.read(128*1024)
            return data == (ROOT/'CONTEST_DECLARATION.md').read_bytes()
        check('official_declaration_bytes', official)

    files = list(source_files(ROOT))
    relative = [path.relative_to(ROOT).as_posix() for path in files]
    def python_sources():
        for path in files:
            if path.suffix == '.py':
                tree = ast.parse(path.read_text(encoding='utf-8-sig'), filename=path.name)
                for node in ast.walk(tree):
                    names = ([alias.name for alias in node.names] if isinstance(node, ast.Import) else
                             [node.module] if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module else [])
                    for name in names:
                        if name.split('.')[0] not in sys.stdlib_module_names | {'mcdcode','scripts'}:
                            raise ValueError('non-stdlib runtime import')
    check('python_syntax_and_stdlib_imports', python_sources)

    def config():
        value = json.loads((ROOT/'mcp-config.example.json').read_text(encoding='utf-8'))
        entry = value['mcpServers']['mcd-mcp']
        return (entry['url'] == 'https://mcp.mcd.cn' and entry['type'] == 'streamablehttp'
                and entry['headers']['Authorization'] == 'Bearer ${MCD_TOKEN}')
    check('connector_environment_placeholder', config)

    def boundaries():
        for name in relative:
            if any(part in {'.local','outputs','tests','.git','__pycache__'} for part in Path(name).parts):
                raise ValueError('private or development content included')
        return not (ROOT/'tests').exists() and not (ROOT/'mcdcode/demo.py').exists()
    check('public_package_boundaries', boundaries)

    def secrets():
        token = os.environ.get('MCD_TOKEN','').encode('utf-8')
        for path in files:
            data = path.read_bytes()
            if token and token in data:
                raise ValueError('active token in public file')
            if path.suffix in {'.md','.json','.py'}:
                text = data.decode('utf-8-sig')
                if re.search(r'https://m\.mcd\.cn/mcp/scanToPay\?orderId=\d+',text):
                    raise ValueError('private order payment link')
                if re.search(r'"(?:orderId|payId)"\s*:\s*"\d{15,}"',text):
                    raise ValueError('private order identifier')
    check('public_file_sensitive_values', secrets)

    def links():
        for name in ['README.md','SKILL.md','MCP_INTEGRATION.md']:
            path = ROOT/name
            for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
                if '://' in target or target.startswith('#'):
                    continue
                target = target.split('#')[0]
                if target and not (path.parent/target).exists():
                    raise ValueError('broken relative documentation link')
    check('entry_document_links', links)

    def media():
        from mcdcode.ui import _read_animation
        animation = _read_animation(ROOT/'assets/laugh.json')
        if not animation.video or animation.frame_count != 144:
            raise ValueError('missing real video frames')
        characters = list((ROOT/'assets/characters').glob('*.png'))
        if len(characters) != 11:
            raise ValueError('missing characters')
        for path in characters:
            data = path.read_bytes()
            if not data.startswith(b'\x89PNG\r\n\x1a\n') or struct.unpack('>II',data[16:24]) != (512,512):
                raise ValueError('unexpected character asset')
        data = (ROOT/'assets/card-example.png').read_bytes()
        if struct.unpack('>II',data[16:24]) != (1080,1440):
            raise ValueError('unexpected card preview size')
        with wave.open(str(ROOT/'assets/laugh.wav'),'rb') as wav:
            if abs(wav.getnframes()/wav.getframerate()-6) > .01:
                raise ValueError('unexpected laugh duration')
        return (ROOT/'assets/nawa.gif').read_bytes().startswith((b'GIF87a',b'GIF89a'))
    check('shipped_media', media)

    def cli_help():
        result = subprocess.run([sys.executable,str(ROOT/'mcd.py'),'--json','--command','/help'],
                                cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=15)
        value = json.loads(result.stdout)
        return result.returncode == 0 and value['ok'] and value['mode'] == 'live' and '\x1b' not in result.stdout
    check('real_cli_help_entry', cli_help)

    def cli_preferences():
        result = subprocess.run([sys.executable,str(ROOT/'mcd.py'),'--json','--command','/偏好'],
                                cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=15)
        value = json.loads(result.stdout)
        memory = value['data']['preferences']
        return (result.returncode == 0 and value['ok'] and not value['confirmation_required']
                and memory['schema_version'] == 1 and isinstance(memory['enabled'],bool)
                and isinstance(memory['notes'],list) and isinstance(memory['order_choices'],list))
    check('real_cli_preferences_entry', cli_preferences)

    def opening_banner():
        import io
        from mcdcode.ui import banner, display_width
        value = banner(stream=io.StringIO())
        return '奶蛙记得你的口味' in value and max(map(display_width,value.splitlines())) <= 80
    check('opening_banner_width', opening_banner)

    result = {'checked_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
              'passed': not failures,'checks':checks,'public_file_count':len(files),
              'active_token_value_scanned': bool(os.environ.get('MCD_TOKEN')),
              'mcp_writes_executed':0,
              'note':'交付文件和实际程序入口检查；不等于全部业务或报名资格审核通过。'}
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

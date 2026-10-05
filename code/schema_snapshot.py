"""Validate native saved tools/list responses without changing their schemas.

This is an offline preparation utility, not a server crawler. It never invokes
tools. Missing revision/license provenance prevents a snapshot from being ready.
"""
import _root  # noqa: F401
import argparse
import copy
import json
import re
from pathlib import Path
from jsonschema import validators
import evidence


def validate(blob, provenance):
    for key in ('source_url', 'commit', 'license', 'task'):
        if not isinstance(provenance.get(key), str) or not provenance[key].strip():
            raise ValueError(f'missing native-schema provenance: {key}')
    if provenance['task'] not in ('orders', 'email', 'calendar', 'files'):
        raise ValueError('unsupported task stratum')
    if not re.fullmatch(r'[0-9a-f]{40}', provenance['commit']):
        raise ValueError('source commit must be a full 40-character Git revision, not a branch/tag')
    tools = blob.get('tools', blob.get('result', {}).get('tools'))
    if not isinstance(tools, list) or not tools:
        raise ValueError('expected a nonempty native tools/list result')
    names = set()
    for tool in tools:
        name = tool.get('name')
        if not isinstance(name, str) or not name or name in names:
            raise ValueError('tool names must be present and unique')
        names.add(name)
        schema = tool.get('inputSchema')
        if not isinstance(schema, dict):
            raise ValueError(f'{name}: missing inputSchema')
        validators.validator_for(schema).check_schema(schema)
    return {'schema_version': 1, 'provenance': copy.deepcopy(provenance),
            'native_tools_list': copy.deepcopy(blob)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('--provenance', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    result = validate(json.loads(Path(args.input).read_text()),
                      json.loads(Path(args.provenance).read_text()))
    result['source_sha256'] = evidence.digest(args.input)
    with open(args.out, 'x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')

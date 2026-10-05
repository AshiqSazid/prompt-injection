"""Export the minimal historical MCPTox listing subset used by prevalence.

Local artifact generation only. Review upstream licensing before redistribution.
Does not download, execute servers, or include benchmark attack responses.
"""
import _root  # noqa: F401
import json
from pathlib import Path
import evidence
import harvest_benign_fields as harvest


def main():
    source = Path('.cache/mcptox_response_all.json')
    blob = json.loads(source.read_text())
    output = Path('data/source_snapshots/mcptox_listings.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    subset = {'servers': {name: {'clean_system_promot': entry.get('clean_system_promot')}
                          for name, entry in blob['servers'].items()}}
    output.write_text(json.dumps(subset, indent=2, ensure_ascii=False) + '\n')
    provenance = {'source_url': harvest.MCPTOX_URL, 'source_sha256': evidence.digest(source),
                  'snapshot_sha256': evidence.digest(output),
                  'transformation': 'Keep server keys and clean_system_promot only; no attack responses.',
                  'license_status': 'Upstream redistribution/license review required before release; no license inferred.',
                  'source_commit': None, 'source_commit_status': 'Historical cache did not record a revision.'}
    output.with_name('provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(f'exported {len(subset["servers"])} historical listings -> {output}')


if __name__ == '__main__':
    main()

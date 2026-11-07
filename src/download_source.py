"""Download a NEW full City export and its metadata, without replacing the frozen input.

Example: python src/download_source.py --destination data/raw/refresh_2026-11-08
The live dataset can change; a new snapshot will not necessarily reproduce v1 results.
"""
import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


def download(url, target):
    request = Request(url, headers={'User-Agent':'Austin311Portfolio/1.0'})
    with urlopen(request, timeout=180) as response, target.open('wb') as stream:
        shutil.copyfileobj(response,stream)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination',required=True)
    args = parser.parse_args()
    folder = Path(args.destination)
    folder.mkdir(parents=True,exist_ok=False)
    start = datetime.now(timezone.utc).isoformat()
    download('https://data.austintexas.gov/api/views/38mr-dwji.json',folder/'city_metadata.json')
    # Full export avoids the default row limit of the Socrata resource endpoint.
    download('https://data.austintexas.gov/api/views/38mr-dwji/rows.csv?accessType=DOWNLOAD',folder/'source_snapshot.csv')
    with (folder/'source_snapshot.csv').open('rb') as stream:
        digest = hashlib.file_digest(stream,'sha256').hexdigest()
    manifest = {'started_utc':start,'completed_utc':datetime.now(timezone.utc).isoformat(),
                'source_sha256':digest,'export_scope':'All published rows; pipeline selects calendar 2025',
                'note':'CSV and metadata are separate live requests, not an atomic portal transaction.'}
    (folder/'download_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(folder.resolve())


if __name__=='__main__':
    main()

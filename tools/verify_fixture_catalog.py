"""Validate the fixture using the authoritative reader from the CAT-CONS delivery."""
import subprocess
import sys
import tempfile
from pathlib import Path

SOURCE = 'd63f0465263f072d3965e813a60bb806eb51872e'


def verify(root):
    with tempfile.TemporaryDirectory(prefix='fixture-catalog-') as temporary:
        reader = Path(temporary)
        def git(*args):
            subprocess.run(['git', '-C', str(reader), *args], check=True)
        git('init', '-q')
        git('remote', 'add', 'origin', 'https://github.com/venomenon328/picross.git')
        git('config', 'remote.origin.promisor', 'true')
        git('config', 'remote.origin.partialclonefilter', 'blob:none')
        git('fetch', '--quiet', '--no-tags', '--depth=1', '--filter=blob:none', 'origin', SOURCE)
        git('checkout', '-q', 'FETCH_HEAD', '--', 'tools')
        # Use isolated mode so no fixture module or environment path shadows the pinned reader.
        subprocess.run([sys.executable, '-I', '-c', """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from tools.production_workspace.sources import GitSource
from tools.puzzle_production import puzzle_catalog
source = GitSource(Path(sys.argv[2]))
read = lambda name, limit, missing=False: source.read(sys.argv[3], name, limit, missing=missing)
ids = source.puzzle_ids(sys.argv[3])
cats, registry = puzzle_catalog.index(read, ids)
for row in registry['entries']:
    puzzle_catalog.delivery(read, row['id'], cats, row)
print('Verified synthetic records, runtime projection and original asset hashes:', len(ids))
""", str(reader), str(root.resolve()), subprocess.check_output(
            ['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()], check=True)

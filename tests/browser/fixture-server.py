"""Serve disposable journal records through the production center HTTP stack."""
import argparse
import json
from pathlib import Path
import sys
import threading

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'dashboard'), str(ROOT / 'scripts/core')]
from center_store import CenterStore
from center_catalog import CenterCatalog
from center_runtime import CenterRuntime
from center_server import CenterServer
from test_center_runtime import FakeAdapter

parser = argparse.ArgumentParser()
parser.add_argument('--repo', type=Path, required=True)
args = parser.parse_args()
store = CenterStore(args.repo / '.browser-center')
catalog = CenterCatalog(store)
candidate = catalog.probe({'root': str(args.repo)})
item = catalog.commit({'candidateId': candidate['candidateId'], 'candidateHash': candidate['candidateHash'],
                       'idempotencyKey': candidate['candidateId']})['items'][0]
runtime = CenterRuntime(store, catalog, ROOT, {'platform': 'posix'}, adapter=FakeAdapter())
with store.transaction() as tx:
    preferences = tx.get('preferences', 'main')
    preferences.update(language='zh-CN', productLanguage='zh-CN')
    tx.put('preferences', 'main', preferences)

def no_preparation(*_args):
    raise AssertionError('Journal tests must not prepare or dispatch model work')

runtime._worker = no_preparation
server = CenterServer(('127.0.0.1', 0), store, catalog, runtime, ROOT)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
try:
    print(json.dumps({'url': f'http://127.0.0.1:{server.server_address[1]}', **item}), flush=True)
    sys.stdin.read()
finally:
    server.shutdown()
    server.server_close()
    thread.join(5)
    store.close()

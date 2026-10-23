"""Verify live dashboards, active alert rules and PromQL without saving secrets."""
import base64
import json
import os
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read_json(url, auth=None):
    request = urllib.request.Request(url)
    if auth:
        request.add_header('Authorization', 'Basic ' + auth)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def main():
    os.environ['KUBECONFIG'] = str(ROOT / '.local/kubeconfig')
    secret = json.loads(subprocess.check_output([
        'kubectl', '--context', 'kind-mecaniqa', '-n', 'mecaniqa',
        'get', 'secret', 'grafana-admin', '-o', 'json',
    ]))['data']
    credentials = b':'.join(base64.b64decode(secret[key])
                            for key in ('username', 'password'))
    auth = base64.b64encode(credentials).decode()
    paths = {
        'health': 'api/health',
        'datasource': 'api/datasources/uid/mecaniqa-prometheus/health',
        'dashboards': 'api/search?tag=oat2',
        'rules': 'api/v1/provisioning/alert-rules',
    }
    results = {name: read_json('http://localhost:3000/' + path, auth)
               for name, path in paths.items()}
    if results['health']['database'] != 'ok' or results['datasource']['status'] != 'OK':
        raise RuntimeError('Grafana or datasource unhealthy')
    if len(results['dashboards']) != 4:
        raise RuntimeError('Expected exactly four OAT2 dashboards')
    rules = results['rules']
    if len(rules) != 4 or any(rule['isPaused'] for rule in rules):
        raise RuntimeError('Expected exactly four active rules')
    for rule in rules:
        params = urllib.parse.urlencode({'query': rule['data'][0]['model']['expr']})
        query = read_json('http://localhost:9090/api/v1/query?' + params)
        if query['status'] != 'success' or not query['data']['result']:
            raise RuntimeError(f"Rule query has no samples: {rule['uid']}")
        results[rule['uid']] = query
    output = ROOT / 'docs/evidencias/2026-10-21-estresse/configuracao-validada.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print('PASS: Grafana, datasource, four dashboards, four active rules and four live queries')


if __name__ == '__main__':
    main()

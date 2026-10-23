"""Controlled local fault injection, live evidence and automatic recovery.

Run with .local/venv/Scripts/python.exe scripts/stress-test.py.
Requires localhost Grafana :3000, Prometheus :9090 and the local Kind cluster.
Playwright + installed Edge are workstation-only dependencies.
"""
import base64
import json
import os
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ['KUBECONFIG'] = str(ROOT / '.local/kubeconfig')
OUT = ROOT / 'docs/evidencias/2026-10-21-estresse'


def kubectl(*args):
    return subprocess.check_output(
        ['kubectl', '--context', 'kind-mecaniqa', '-n', 'mecaniqa', *args],
        text=True, encoding='utf-8', stderr=subprocess.STDOUT, timeout=45)


def get(url, auth=None):
    request = urllib.request.Request(url)
    if auth:
        request.add_header('Authorization', 'Basic ' + auth)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def main():
    from playwright.sync_api import sync_playwright
    OUT.mkdir(parents=True, exist_ok=True)
    original = json.loads(kubectl('get', 'deployment', 'simulator', '-o', 'json'))
    original_env = original['spec']['template']['spec']['containers'][0]['env']
    secret = json.loads(kubectl('get', 'secret', 'grafana-admin', '-o', 'json'))['data']
    user, password = [base64.b64decode(secret[key]).decode() for key in ('username', 'password')]
    auth = base64.b64encode(f'{user}:{password}'.encode()).decode()
    # Verify both APIs before changing the workload.
    get('http://localhost:3000/api/health', auth)
    get('http://localhost:9090/api/v1/targets')
    samples = []
    started = datetime.now(timezone.utc).isoformat()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 1100})
        login = context.request.post('http://localhost:3000/login', data={'user': user, 'password': password})
        if login.status != 200:
            raise RuntimeError('Grafana login failed')
        page = context.new_page()

        def capture(label):
            page.goto('http://localhost:3000/alerting/list', wait_until='domcontentloaded')
            page.get_by_role('heading', name='Alert rules', exact=True).wait_for(timeout=60000)
            page.get_by_role('radio', name='List', exact=True).check()
            folder = page.get_by_text('MecaniQA OAT 2', exact=True)
            folder.wait_for(timeout=60000)
            cpu_rule = page.get_by_text('CPU acima de 80 por cento do limite', exact=True).first
            if not cpu_rule.is_visible():
                folder.click()
            cpu_rule.wait_for(timeout=60000)
            page.screenshot(path=str(OUT / f'{label}-alarmes.png'), full_page=True)
            for name in ('cpu', 'memoria', 'erro', 'sucesso'):
                page.goto(f'http://localhost:3000/d/mecaniqa-{name}?from=now-30m&to=now&kiosk', wait_until='domcontentloaded')
                page.locator('canvas').first.wait_for(timeout=60000)
                page.wait_for_function("!document.body.innerText.includes('Loading')")
                page.screenshot(path=str(OUT / f'{label}-{name}.png'), full_page=True)

        def snapshot(phase):
            rules = get('http://localhost:3000/api/prometheus/grafana/api/v1/rules', auth)
            alerts = [r for group in rules['data']['groups'] for r in group['rules']
                      if r.get('type') == 'alerting']
            hpa = json.loads(kubectl('get', 'hpa', 'simulator', '-o', 'json'))
            deploy = json.loads(kubectl('get', 'deploy', 'simulator', '-o', 'json'))
            sample = {'time': datetime.now(timezone.utc).isoformat(), 'phase': phase,
                      'hpa': hpa['status'], 'deployment': deploy['status'], 'rules': alerts,
                      'targets': get('http://localhost:9090/api/v1/targets')['data']['activeTargets']}
            samples.append(sample)
            (OUT / 'amostras.json').write_text(json.dumps(samples, ensure_ascii=False, indent=2), encoding='utf-8')
            (OUT / 'recursos.txt').write_text(kubectl('get', 'hpa,pods,deploy') + '\n' + kubectl('get', 'events', '--sort-by=.lastTimestamp'), encoding='utf-8')
            print(phase, sample['hpa'].get('currentReplicas'), [(a['name'], a['state']) for a in alerts], flush=True)
            return sample, alerts

        result = {'started': started, 'stress_passed': False, 'recovery_passed': False}
        try:
            snapshot('baseline')
            kubectl('set', 'env', 'deployment/simulator', 'PEAK_MODE=off',
                    'READINGS_PER_SECOND=100', 'STRESS_CPU_MS=10',
                    'STRESS_MEMORY_MIB=80', 'STRESS_ERROR_RATIO=0.2')
            # The rollout must finish before measuring the stable set of replicas.
            kubectl('rollout', 'status', 'deployment/simulator', '--timeout=40s')
            deadline = time.monotonic() + 600
            while time.monotonic() < deadline:
                sample, alerts = snapshot('stress')
                firing = len(alerts) == 4 and all(a['state'] == 'firing' for a in alerts)
                if firing and sample['hpa'].get('currentReplicas', 0) > 1:
                    result['stress_passed'] = True
                    (OUT / 'simulator-stress.log').write_text(kubectl('logs', '-l', 'app=simulator', '--prefix', '--tail=30'), encoding='utf-8')
                    (OUT / 'grafana-alarmes.log').write_text(kubectl('logs', 'deployment/grafana', '--since=15m'), encoding='utf-8')
                    capture('estresse')
                    break
                time.sleep(15)
            if not result['stress_passed']:
                capture('incompleto')
                raise RuntimeError('Stress acceptance criteria not met within 600 seconds')
        finally:
            patch = ROOT / '.local/restore-simulator.json'
            patch.write_text(json.dumps([{'op': 'replace', 'path': '/spec/template/spec/containers/0/env', 'value': original_env}]), encoding='utf-8')
            kubectl('patch', 'deployment', 'simulator', '--type=json', '--patch-file', str(patch))
            deadline = time.monotonic() + 720
            try:
                while time.monotonic() < deadline:
                    sample, alerts = snapshot('recovery')
                    if (sample['hpa'].get('currentReplicas') == 1
                            and sample['deployment'].get('readyReplicas') == 1
                            and len(alerts) == 4 and all(a['state'] == 'inactive' for a in alerts)):
                        result['recovery_passed'] = True
                        capture('recuperacao')
                        break
                    time.sleep(15)
            finally:
                result['finished'] = datetime.now(timezone.utc).isoformat()
                (OUT / 'resultado.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
                browser.close()
        if not all(result[key] for key in ('stress_passed', 'recovery_passed')):
            raise RuntimeError('Incomplete acceptance criteria; inspect saved evidence')
        print('PASS: four firing alerts, scale-out and recovery to one replica', flush=True)


if __name__ == '__main__':
    main()

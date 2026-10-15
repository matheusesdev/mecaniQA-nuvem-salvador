"""Capture the deployed Grafana dashboards using an installed Microsoft Edge.

Optional workstation dependency: pip install playwright (outside the simulator).
Requires the Grafana port-forward on localhost:3000 and the local Kind cluster.
"""

import base64
import json
import os
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    root = Path(__file__).resolve().parent.parent
    environment = dict(os.environ, KUBECONFIG=str(root / '.local/kubeconfig'))
    secret = json.loads(subprocess.check_output(
        ['kubectl', '--context', 'kind-mecaniqa', '-n', 'mecaniqa',
         'get', 'secret', 'grafana-admin', '-o', 'json'],
        env=environment,
    ))['data']
    credentials = {
        'user': base64.b64decode(secret['username']).decode(),
        'password': base64.b64decode(secret['password']).decode(),
    }
    output = root / 'docs/evidencias/2026-10-14'
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='msedge', headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 1000})
        response = context.request.post('http://localhost:3000/login', data=credentials)
        if response.status != 200:
            raise RuntimeError('Grafana login failed')
        page = context.new_page()
        for definition in sorted((root / 'grafana/dashboards').glob('*.json')):
            dashboard = json.loads(definition.read_text(encoding='utf-8'))
            page.goto(f"http://localhost:3000/d/{dashboard['uid']}?from=now-15m&to=now&kiosk",
                      wait_until='domcontentloaded')
            page.locator('canvas').first.wait_for(timeout=60000)
            page.wait_for_timeout(5000)
            body = page.locator('body').inner_text()
            if 'No data' in body or 'Panel plugin not found' in body:
                raise RuntimeError(f"Dashboard failed to render data: {dashboard['uid']}")
            page.screenshot(path=str(output / f'{definition.stem}.png'), full_page=True)
            print(f"Captured {dashboard['uid']}")
        browser.close()


if __name__ == '__main__':
    main()

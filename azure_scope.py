#!/usr/bin/env python3
"""Produce *candidate* Azure penetration-testing scope from explicitly selected groups.

Read-only Azure CLI inventory. Nothing in this tool sends traffic to discovered assets.
Inventory alone does not constitute proof of ownership or authorization.
"""
import argparse
import ipaddress
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

COMMANDS = {
    'public-ip': ['network', 'public-ip', 'list'],
    'webapp': ['webapp', 'list'],
    'functionapp': ['functionapp', 'list'],
    'sql': ['sql', 'server', 'list'],
    'container': ['container', 'list'],
    'storage': ['storage', 'account', 'list'],
}


def safe_hostname(host):
    """Reject arbitrary URLs, wildcards and malformed names; no DNS queries."""
    if not isinstance(host, str):
        return None
    host = host.strip().rstrip('.').lower()
    if not host or len(host) > 253 or '*' in host or '/' in host or ':' in host:
        return None
    if not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+', host):
        return None
    return host


def public_ip(value):
    try:
        address = ipaddress.ip_address(str(value))
        return str(address) if address.is_global else None
    except ValueError:
        return None


def enabled(resource):
    return str(resource.get('publicNetworkAccess', 'Enabled')).lower() != 'disabled'


def inventory(service, resources, subscription, group):
    """Convert Azure CLI JSON to candidates; resource IDs enable human review."""
    found = []
    for item in resources:
        if not isinstance(item, dict):
            continue
        name, rid = str(item.get('name', '')), str(item.get('id', ''))

        def add(kind, value, note):
            if not value:
                return
            found.append({'subscription': subscription, 'resource_group': group,
                          'service': service, 'resource_name': name, 'resource_id': rid,
                          'type': kind, 'target': value, 'review': note})

        if service == 'public-ip':
            ip = public_ip(item.get('ipAddress'))
            if ip and item.get('ipConfiguration'):
                add('ip', ip, 'Public IP associated with an Azure resource; verify frontend, ownership and permission')
            # NAT gateway egress addresses and unattached IPs are not inbound scan candidates.
            dns = safe_hostname((item.get('dnsSettings') or {}).get('fqdn'))
            if dns and item.get('ipConfiguration'):
                add('hostname', dns, 'Public IP DNS name; validate ingress and assignment')
        elif service in ('webapp', 'functionapp') and enabled(item):
            # outboundIpAddresses are the application's *egress* identities, not inbound targets.
            add('hostname', safe_hostname(item.get('defaultHostName')),
                'Default app hostname; check authentication, restrictions and approved scope')
            for host in item.get('enabledHostNames') or []:
                # Exclude internal SCM endpoints and avoid assuming custom domains authorized.
                if '.scm.' not in str(host).lower():
                    add('hostname', safe_hostname(host),
                        'Additional hostname; ownership and permission must be verified separately')
        elif service == 'sql' and enabled(item):
            add('hostname', safe_hostname(item.get('fullyQualifiedDomainName')),
                'SQL FQDN; public reachability and firewall rules require manual verification')
        elif service == 'container':
            addr = item.get('ipAddress') or {}
            if str(addr.get('type', '')).lower() == 'public':
                add('ip', public_ip(addr.get('ip')),
                    'Container public IP; verify deployment ownership and authorization')
                add('hostname', safe_hostname(addr.get('fqdn')),
                    'Container FQDN; verify public exposure')
        elif service == 'storage' and enabled(item):
            endpoint = (item.get('primaryEndpoints') or {}).get('blob')
            if endpoint:
                parsed = urlsplit(endpoint)
                if parsed.scheme == 'https':
                    add('hostname', safe_hostname(parsed.hostname),
                        'Blob endpoint; network ACLs and authorization require verification')
    return found


def az_inventory(service, subscription, resource_group):
    cmd = ['az', *COMMANDS[service], '--subscription', subscription,
           '--resource-group', resource_group, '--output', 'json']
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=90)
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"Azure CLI inventory failed for {service}/{resource_group}: {exc}") from exc
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid Azure CLI JSON for {service}/{resource_group}") from exc
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected Azure CLI payload for {service}/{resource_group}")
    return data


def collect(subscription, groups, services=tuple(COMMANDS)):
    rows = []
    for group in groups:
        for service in services:
            rows.extend(inventory(service, az_inventory(service, subscription, group), subscription, group))
    by_key = {}
    for row in rows:
        key = (row['subscription'], row['resource_group'], row['type'], row['target'], row['resource_id'])
        by_key[key] = row
    return sorted(by_key.values(), key=lambda r: (r['resource_group'], r['type'], r['target'], r['service']))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--subscription', required=True, help='Explicit Azure subscription ID')
    parser.add_argument('--resource-group', action='append', required=True,
                        help='Authorized resource group (repeat to add more)')
    parser.add_argument('--service', choices=list(COMMANDS), action='append',
                        help='Optional service filter (repeatable)')
    parser.add_argument('--output', type=Path, default=Path('scope-candidates.json'))
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error(f'Output already exists: {args.output} (choose a new filename)')
    try:
        rows = collect(args.subscription, list(dict.fromkeys(args.resource_group)),
                       tuple(dict.fromkeys(args.service)) if args.service else tuple(COMMANDS))
    except RuntimeError as exc:
        parser.exit(1, f'{exc}\nNo output saved; inventory may be incomplete.\n')
    data = {'notice': 'Candidate inventory only. NOT authorization or a ready-to-scan target list.',
            'subscription': args.subscription, 'resource_groups': list(dict.fromkeys(args.resource_group)),
            'candidates': rows}
    args.output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Collected {len(rows)} candidates for manual scope review in {args.output}')


if __name__ == '__main__':
    main()

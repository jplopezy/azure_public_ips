import unittest
from unittest.mock import patch
from azure_scope import inventory, collect, safe_hostname, public_ip


class ScopeTests(unittest.TestCase):
    def test_public_ip_must_be_associated_and_globally_routable(self):
        sample = [
            {'name': 'ingress', 'id': '/r/a', 'ipAddress': '20.1.2.3', 'ipConfiguration': {'id': '/nic/1'}},
            {'name': 'unassigned', 'id': '/r/b', 'ipAddress': '20.1.2.4'},
            {'name': 'egress', 'id': '/r/c', 'ipAddress': '20.1.2.5', 'natGateway': {'id': '/nat/1'}},
            {'name': 'private', 'id': '/r/d', 'ipAddress': '10.0.0.1', 'ipConfiguration': {'id': '/nic/2'}},
        ]
        rows = inventory('public-ip', sample, 'sub', 'rg')
        self.assertEqual([r['target'] for r in rows], ['20.1.2.3'])

    def test_webapp_excludes_egress_and_disabled(self):
        rows = inventory('webapp', [
            {'name': 'app', 'id': '/a', 'defaultHostName': 'app.azurewebsites.net',
             'outboundIpAddresses': '20.2.2.2',
             'enabledHostNames': ['app.azurewebsites.net', 'app.scm.azurewebsites.net']},
            {'name': 'off', 'id': '/b', 'defaultHostName': 'off.azurewebsites.net',
             'publicNetworkAccess': 'Disabled'}
        ], 'sub', 'rg')
        self.assertEqual({r['target'] for r in rows}, {'app.azurewebsites.net'})

    def test_sql_fqdn_not_double_suffix(self):
        rows = inventory('sql', [{'name':'sql', 'id':'/sql',
                                   'fullyQualifiedDomainName':'foo.database.windows.net'}], 's', 'g')
        self.assertEqual(rows[0]['target'], 'foo.database.windows.net')

    def test_container_private_filtered(self):
        rows = inventory('container', [
            {'name':'one','ipAddress':{'type':'Private','ip':'10.0.0.2'}},
            {'name':'two','ipAddress':{'type':'Public','ip':'20.5.4.3','fqdn':'two.region.azurecontainer.io'}}
        ],'s','g')
        self.assertEqual({r['target'] for r in rows}, {'20.5.4.3','two.region.azurecontainer.io'})

    def test_storage_endpoints_are_parsed(self):
        rows = inventory('storage', [{'name':'x','primaryEndpoints':{'blob':'https://abc.blob.core.windows.net/'}}], 's','g')
        self.assertEqual(rows[0]['target'], 'abc.blob.core.windows.net')

    def test_hostname_validation(self):
        self.assertIsNone(safe_hostname('*.example.com'))
        self.assertIsNone(safe_hostname('https://example.com'))
        self.assertIsNone(public_ip('192.168.1.1'))

    @patch('azure_scope.az_inventory')
    def test_scoped_calls(self, fetch):
        fetch.return_value = []
        collect('my-sub', ['rg-1', 'rg-2'], ('sql',))
        self.assertEqual(fetch.call_count, 2)
        fetch.assert_any_call('sql', 'my-sub', 'rg-1')
        fetch.assert_any_call('sql', 'my-sub', 'rg-2')

if __name__ == '__main__':
    unittest.main()

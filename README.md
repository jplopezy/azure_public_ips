# Azure Scope Candidate Inventory

Read-only Azure CLI inventory to help prepare **authorized** penetration-testing scopes. It enumerates candidate ingress addresses and hostnames across explicitly selected subscription/resource groups; it **does not** verify ownership, perform network scans, or prove that any resource is authorized for testing.

## Improvements in v2

- Explicit `--subscription` and repeatable `--resource-group`; **never silently enumerate every subscription**.
- Retrieves associated public IP resources (not NAT egress-only IPs), App Services / Function Apps hostnames, SQL FQDNs, public Azure Container Instances, and Blob endpoints.
- Does not mistake App Service `outboundIpAddresses` for public inbound targets.
- Avoids inventing DNS names or double-appending `.database.windows.net` to SQL FQDNs.
- JSON output with Azure resource IDs for validation by a scope owner. No activity against returned hosts.
- Fails if an Azure CLI inventory call fails: a partial result is not treated as complete.

## Requirements

- Python 3.9+ (`az` CLI separately installed, authenticated and permitted to read selected resource groups)
- Azure access with resource read permissions

## Usage

```bash
az login
az account list --output table
python3 azure_scope.py --subscription YOUR-SUBSCRIPTION-ID \
  --resource-group AUTHORIZED-RG --output scope-2026.json

# Repeat to include a second specifically approved resource group:
./azureips.sh --subscription YOUR-SUBSCRIPTION-ID \
  --resource-group RG-1 --resource-group RG-2 --output scope-review.json

# Restrict API calls if an account lacks access to some resource types:
python3 azure_scope.py --subscription YOUR-SUBSCRIPTION-ID \
  --resource-group RG-1 --service public-ip --service webapp --output scope-review.json
```

Output files are designed for **human review** and include the service, resource name, resource ID, group, candidate host/IP and a review note. Do **not** feed them automatically into Nmap/Nuclei. Azure resources may be shared, restricted by a firewall, or belong to third parties behind custom domains. Confirm contractual authorization and exclusions separately.

No results are written until all selected inventory operations succeed. The script will not overwrite an existing output file.

## Offline tests

```bash
python3 -m unittest discover -s tests -v
```

## Limitations

This release intentionally prioritizes accurate basic candidates over exhaustive Azure surface enumeration. It does not cover Front Door, CDN, Private Link, API Management, managed Kubernetes ingress, cross-subscription resources, DNS aliases or custom endpoint ownership verification. A missing candidate is not evidence of a secure or inaccessible resource.

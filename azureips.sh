#!/bin/bash

# Script created by Juan Pablo Lopez Yacubian (6/19/2023)

# This script fetches all public IP addresses and relevant addressing data linked 
# to your Azure account focusing on Virtual Machines, Load Balancers, SQL Servers,
# Synapse Workspaces SQL Pools, Containers, App Services, and Azure Functions.

# Delete output file if it already exists
rm -f azureips.txt

# Get the list of resource groups
resource_groups=$(az group list --query "[].name" -o tsv)

for resource_group in $resource_groups; do
    # For each resource group, get the list of Virtual Machines
    vms=$(az vm list --resource-group $resource_group --query "[].name" -o tsv)

    for vm in $vms; do
        # For each Virtual Machine, get the public IP address
        vm_ip=$(az vm show -d --resource-group $resource_group --name $vm --query publicIps --output tsv)
        echo "VM: $vm, Public IP: $vm_ip" >> azureips.txt
    done

    # For each resource group, get the list of Load Balancers
    lbs=$(az network lb list --resource-group $resource_group --query "[].name" -o tsv)

    for lb in $lbs; do
        # For each Load Balancer, get the public IP addresses
        lb_ips_ids=$(az network lb frontend-ip list --resource-group $resource_group --lb-name $lb --query "[].publicIpAddress.id" -o tsv)

        if [ -n "$lb_ips_ids" ]; then
            lb_ips=$(echo $lb_ips_ids | xargs -n1 basename)
            echo "Load Balancer: $lb, Public IPs: $lb_ips" >> azureips.txt
        else
            echo "Load Balancer: $lb, Public IPs: None" >> azureips.txt
        fi
    done

    # For each resource group, get the list of SQL servers
    sql_servers=$(az sql server list --resource-group $resource_group --query "[].name" -o tsv)

    for sql_server in $sql_servers; do
        # For each SQL server, get the connection address
        sql_server_address=$(az sql server show --resource-group $resource_group --name $sql_server --query fullyQualifiedDomainName -o tsv)
        echo "SQL Server: $sql_server, Address: $sql_server_address" >> azureips.txt
    done

    # For each resource group, get the list of Synapse workspaces
    synapse_workspaces=$(az synapse workspace list --resource-group $resource_group --query "[].name" -o tsv)

    for synapse_workspace in $synapse_workspaces; do
        # For each Synapse workspace, get the list of SQL pools
        synapse_sql_pools=$(az synapse sql pool list --workspace-name $synapse_workspace --resource-group $resource_group --query "[].name" -o tsv)

        for synapse_sql_pool in $synapse_sql_pools; do
            # For each SQL pool, get the server address
            synapse_sql_pool_address=$(az synapse sql pool show --resource-group $resource_group --workspace-name $synapse_workspace --name $synapse_sql_pool --query sourceDatabaseId -o tsv)
            echo "Synapse SQL Pool: $synapse_sql_pool, Server Address: $synapse_sql_pool_address" >> azureips.txt
        done
    done

    # For each resource group, get the list of Containers
    containers=$(az container list --resource-group $resource_group --query "[].name" -o tsv)

    for container in $containers; do
        # For each Container, get the public IP address
        container_ip=$(az container show --resource-group $resource_group --name $container --query ipAddress.ip --output tsv)
        echo "Container: $container, Public IP: $container_ip" >> azureips.txt
    done

    # For each resource group, get the list of App Services
    webapps=$(az webapp list --resource-group $resource_group --query "[].name" -o tsv)

    for webapp in $webapps; do
        # For each App Service, get the outbound IP addresses
        webapp_ips=$(az webapp show --resource-group $resource_group --name $webapp --query outboundIpAddresses --output tsv)
        echo "Web App: $webapp, Outbound IPs: $webapp_ips" >> azureips.txt
    done

    # For each resource group, get the list of Azure Functions
    functionapps=$(az functionapp list --resource-group $resource_group --query "[].name" -o tsv)

    for functionapp in $functionapps; do
        # For each Azure Function, get the outbound IP addresses
        functionapp_ips=$(az functionapp show --resource-group $resource_group --name $functionapp --query outboundIpAddresses --output tsv)
        echo "Function App: $functionapp, Outbound IPs: $functionapp_ips" >> azureips.txt
    done
done

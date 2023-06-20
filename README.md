# Azure Public IP Fetching Script

This script was inspired by [aws_public_ips](https://github.com/arkadiyt/aws_public_ips), which fetches all public IPs associated with an AWS account. The idea behind our script is similar - to quickly determine the scope and initiate a scan for pen testing tasks.

Currently, our script supports the most important services in Azure. These include:

1. **Virtual Machines (VMs)**: The script collects the public IP addresses of all VMs within the specified resource groups.

2. **Load Balancers (LBs)**: The script fetches the public IP addresses of all load balancers within the specified resource groups.

3. **SQL Servers**: The script gathers the Fully Qualified Domain Names (FQDNs) for all SQL servers within the specified resource groups. While these are not IPs, they effectively serve the same purpose of addressing the resource.

4. **Synapse Workspaces SQL Pools**: The script retrieves the server addresses associated with SQL pools within Synapse Workspaces in the specified resource groups.

5. **Containers**: The script collects the public IP addresses of all Azure Container Instances within the specified resource groups.

6. **App Services (Web Apps)**: The script fetches the outbound IP addresses for all web apps within the specified resource groups.

7. **Azure Functions**: The script gathers the outbound IP addresses for all Azure Functions within the specified resource groups.

We always welcome improvements, so feel free to contribute!

## Usage

To use this script, first, make sure you have the Microsoft 'az' CLI installed and you are logged in to your Azure account. If not, you can install it and log in using the following command:

curl -sL https://aka.ms/InstallAzureCLIDeb

az login

Then, enter your credentials when prompted.

Once you're logged in, all you need to do is execute the 'azureips.sh' script. The output will include the public IPs and relevant addressing data of all the services within your specified Azure resource groups.

./azureips.sh

This script is an easy and efficient way to get a quick overview of your public-facing Azure resources, helping to speed up pen testing and other security-related tasks.


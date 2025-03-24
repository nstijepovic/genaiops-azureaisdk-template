#!/bin/bash
set -e

random_chars=$(LC_ALL=C tr -dc 'a-z' < /dev/urandom | fold -w 3 | head -n 1)
RESOURCE_GROUP="ml-secure-rg${random_chars}"
LOCATION="eastus"
WORKSPACE_NAME="secure-aml-ws${random_chars}"
VNET_NAME="ml-vnet${random_chars}"
SUBNET_PE_NAME="private-endpoints-subnet${random_chars}"
SUBNET_VPN="GatewaySubnet"

STORAGE_ACCOUNT_NAME="securemlstorage${random_chars}"
KEY_VAULT_NAME="secure-ml-kv${random_chars}"
APP_INSIGHTS_NAME="secure-ml-insights${random_chars}"
CONTAINER_REGISTRY_NAME="securemlregistry${random_chars}"
VPN_PUBLIC_IP="VNet1GWpip1${random_chars}"
VPN_NAME="VNet1GW${random_chars}"
HUB_NAME="my_private_hub${random_chars}"
PROJECT_NAME="my_private_project${random_chars}"
CONNECTION_NAME="my_private_connection${random_chars}"
COMPUTE_NAME="testcompute${random_chars}"

BLOB_DNS_ZONE_NAME="privatelink.blob.core.windows.net"
FILE_DNS_ZONE_NAME="privatelink.file.core.windows.net"
QUEUE_DNS_ZONE_NAME="privatelink.queue.core.windows.net"
TABLE_DNS_ZONE_NAME="privatelink.table.core.windows.net"
KV_DNS_ZONE_NAME="privatelink.vaultcore.azure.net"
CR_DNS_ZONE_NAME="privatelink.azurecr.io"
AI_DNS_ZONE_NAME="privatelink.monitor.azure.com"
AML_DNS_ZONE_NAME="privatelink.api.azureml.ms"
NOTEBOOK_DNS_ZONE_NAME="privatelink.notebooks.azure.net"

###

az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

az network vnet create \
    --name "$VNET_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --address-prefix "10.0.0.0/16"

az network vnet subnet create \
    --name "$SUBNET_PE_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --vnet-name "$VNET_NAME" \
    --address-prefix "10.0.1.0/24" \
    --private-endpoint-network-policies Disabled \
    --private-link-service-network-policies Disabled

az network vnet subnet create \
    --name "$SUBNET_VPN" \
    --resource-group "$RESOURCE_GROUP" \
    --vnet-name "$VNET_NAME" \
    --address-prefix "10.0.2.0/24" \
    --private-endpoint-network-policies Disabled \
    --private-link-service-network-policies Disabled

sub_id=$(az network vnet subnet create \
    --name "DNS" \
    --resource-group "$RESOURCE_GROUP" \
    --vnet-name "$VNET_NAME" \
    --address-prefix "10.0.3.0/24" \
    --private-endpoint-network-policies Disabled \
    --private-link-service-network-policies Disabled \
    --delegations Microsoft.Network/dnsResolvers \
    --query "id" -o tsv)

###
vnet_id=$(az network vnet show --name "$VNET_NAME" --resource-group "$RESOURCE_GROUP" --query "id" -o tsv)

DNS_NAME="dns-resolver${random_chars}"

az dns-resolver create \
  --dns-resolver-name $DNS_NAME \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --id $vnet_id 

ENDPOINT_NAME="inbound-endpoint${random_chars}"

az dns-resolver inbound-endpoint create \
  --name $ENDPOINT_NAME \
  --dns-resolver-name $DNS_NAME \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --ip-configurations "[{\"private-ip-allocation-method\":\"Dynamic\",\"id\":\"$sub_id\"}]" 
  
inbound_endpoint_ip=$(az dns-resolver inbound-endpoint show \
  --name $ENDPOINT_NAME \
  --dns-resolver-name $DNS_NAME \
  --resource-group "$RESOURCE_GROUP" \
  --query "ipConfigurations[0].privateIpAddress" \
  --output tsv)

az network vnet update \
  --name $(basename $vnet_id) \
  --resource-group "$RESOURCE_GROUP" \
  --dns-servers $inbound_endpoint_ip

az network public-ip create --name "$VPN_PUBLIC_IP" --resource-group "$RESOURCE_GROUP" --allocation-method Static --sku Standard --version IPv4 --zone 1 2 3

az network vnet-gateway create --name "$VPN_NAME" --public-ip-addresses "$VPN_PUBLIC_IP" --resource-group "$RESOURCE_GROUP" --vnet "$VNET_NAME" --gateway-type Vpn --vpn-type RouteBased --sku VpnGw2AZ --vpn-gateway-generation Generation2 --no-wait

###

link_name="${BLOB_DNS_ZONE_NAME//\./-}-link"

az network private-dns zone create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$BLOB_DNS_ZONE_NAME"

az network private-dns link vnet create \
    --resource-group "$RESOURCE_GROUP" \
    --zone-name "$BLOB_DNS_ZONE_NAME" \
    --name "$link_name" \
    --virtual-network "$vnet_id" \
    --registration-enabled false

storage_id=$(az storage account create \
    --name "$STORAGE_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --sku "Standard_LRS" \
    --kind "StorageV2" \
    --https-only true \
    --min-tls-version "TLS1_2" \
    --query "id" -o tsv)

az storage account update \
    --name "$STORAGE_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --public-network-access "Disabled"

blob_pe_id=$(az network private-endpoint create \
    --name "${STORAGE_ACCOUNT_NAME}-pe-b" \
    --resource-group "$RESOURCE_GROUP" \
    --vnet-name "$VNET_NAME" \
    --subnet "$SUBNET_PE_NAME" \
    --private-connection-resource-id $(az storage account show --name "$STORAGE_ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP" --query "id" -o tsv) \
    --group-id "blob" \
    --connection-name "${STORAGE_ACCOUNT_NAME}-connection" \
    --query "id" -o tsv)

nic_id=$(az network private-endpoint show --ids $blob_pe_id --query "networkInterfaces[0].id" -o tsv)
ip_address=$(az network nic show --ids $nic_id --query "ipConfigurations[0].privateIPAddress" -o tsv)

az network private-dns record-set a add-record \
    --resource-group "$RESOURCE_GROUP" \
    --zone-name "$BLOB_DNS_ZONE_NAME" \
    --record-set-name "$STORAGE_ACCOUNT_NAME" \
    --ipv4-address $ip_address

az network private-endpoint dns-zone-group create \
    --resource-group "$RESOURCE_GROUP" \
    --endpoint-name "${STORAGE_ACCOUNT_NAME}-pe-b" \
    --name "default" \
    --private-dns-zone "$BLOB_DNS_ZONE_NAME" \
    --zone-name "$BLOB_DNS_ZONE_NAME"

###

link_name="${TABLE_DNS_ZONE_NAME//\./-}-link"

az network private-dns zone create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$TABLE_DNS_ZONE_NAME"

az network private-dns link vnet create \
    --resource-group "$RESOURCE_GROUP" \
    --zone-name "$TABLE_DNS_ZONE_NAME" \
    --name "$link_name" \
    --virtual-network "$vnet_id" \
    --registration-enabled false

table_pe_id=$(az network private-endpoint create \
    --name "${STORAGE_ACCOUNT_NAME}-pe-t" \
    --resource-group "$RESOURCE_GROUP" \
    --vnet-name "$VNET_NAME" \
    --subnet "$SUBNET_PE_NAME" \
    --private-connection-resource-id $(az storage account show --name "$STORAGE_ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP" --query "id" -o tsv) \
    --group-id "table" \
    --connection-name "${STORAGE_ACCOUNT_NAME}-t-connection" \
    --query "id" -o tsv)

nic_id=$(az network private-endpoint show --ids $table_pe_id --query "networkInterfaces[0].id" -o tsv)
ip_address=$(az network nic show --ids $nic_id --query "ipConfigurations[0].privateIPAddress" -o tsv)

az network private-dns record-set a add-record \
    --resource-group "$RESOURCE_GROUP" \
    --zone-name "$TABLE_DNS_ZONE_NAME" \
    --record-set-name "$STORAGE_ACCOUNT_NAME" \
    --ipv4-address $ip_address

az network private-endpoint dns-zone-group create \
    --resource-group "$RESOURCE_GROUP" \
    --endpoint-name "${STORAGE_ACCOUNT_NAME}-pe-t" \
    --name default \
    --private-dns-zone "$TABLE_DNS_ZONE_NAME" \
    --zone-name "$TABLE_DNS_ZONE_NAME"

###

link_name="${FILE_DNS_ZONE_NAME//\./-}-link"

az network private-dns zone create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$FILE_DNS_ZONE_NAME"

az network private-dns link vnet create \
    --resource-group "$RESOURCE_GROUP" \
    --zone-name "$FILE_DNS_ZONE_NAME" \
    --name "$link_name" \
    --virtual-network "$vnet_id" \
    --registration-enabled false

file_pe_id=$(az network private-endpoint create \
    --name "${STORAGE_ACCOUNT_NAME}-f-pe" \
    --resource-group "$RESOURCE_GROUP" \
    --vnet-name "$VNET_NAME" \
    --subnet "$SUBNET_PE_NAME" \
    --private-connection-resource-id $(az storage account show --name "$STORAGE_ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP" --query "id" -o tsv) \
    --group-id "file" \
    --connection-name "${STORAGE_ACCOUNT_NAME}-f-connection" \
    --query "id" -o tsv)

nic_id=$(az network private-endpoint show --ids $file_pe_id --query "networkInterfaces[0].id" -o tsv)
ip_address=$(az network nic show --ids $nic_id --query "ipConfigurations[0].privateIPAddress" -o tsv)

az network private-dns record-set a add-record \
    --resource-group "$RESOURCE_GROUP" \
    --zone-name "$FILE_DNS_ZONE_NAME" \
    --record-set-name "$STORAGE_ACCOUNT_NAME" \
    --ipv4-address $ip_address

az network private-endpoint dns-zone-group create \
    --resource-group "$RESOURCE_GROUP" \
    --endpoint-name "${STORAGE_ACCOUNT_NAME}-f-pe" \
    --name default \
    --private-dns-zone "$FILE_DNS_ZONE_NAME" \
    --zone-name "$FILE_DNS_ZONE_NAME"

###

link_name="${QUEUE_DNS_ZONE_NAME//\./-}-link"

az network private-dns zone create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$QUEUE_DNS_ZONE_NAME"

az network private-dns link vnet create \
    --resource-group "$RESOURCE_GROUP" \
    --zone-name "$QUEUE_DNS_ZONE_NAME" \
    --name "$link_name" \
    --virtual-network "$vnet_id" \
    --registration-enabled false

queue_pe_id=$(az network private-endpoint create \
    --name "${STORAGE_ACCOUNT_NAME}-q-pe" \
    --resource-group "$RESOURCE_GROUP" \
    --vnet-name "$VNET_NAME" \
    --subnet "$SUBNET_PE_NAME" \
    --private-connection-resource-id $(az storage account show --name "$STORAGE_ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP" --query "id" -o tsv) \
    --group-id "queue" \
    --connection-name "${STORAGE_ACCOUNT_NAME}-q-connection" \
    --query "id" -o tsv)

nic_id=$(az network private-endpoint show --ids $queue_pe_id --query "networkInterfaces[0].id" -o tsv)
ip_address=$(az network nic show --ids $nic_id --query "ipConfigurations[0].privateIPAddress" -o tsv)

az network private-dns record-set a add-record \
    --resource-group "$RESOURCE_GROUP" \
    --zone-name "$QUEUE_DNS_ZONE_NAME" \
    --record-set-name "$STORAGE_ACCOUNT_NAME" \
    --ipv4-address $ip_address

az network private-endpoint dns-zone-group create \
    --resource-group "$RESOURCE_GROUP" \
    --endpoint-name "${STORAGE_ACCOUNT_NAME}-q-pe" \
    --name default \
    --private-dns-zone "$QUEUE_DNS_ZONE_NAME" \
    --zone-name "$QUEUE_DNS_ZONE_NAME"

###

link_name="${KV_DNS_ZONE_NAME//\./-}-link"

az network private-dns zone create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$KV_DNS_ZONE_NAME"

az network private-dns link vnet create \
    --resource-group "$RESOURCE_GROUP" \
    --zone-name "$KV_DNS_ZONE_NAME" \
    --name "$link_name" \
    --virtual-network "$vnet_id" \
    --registration-enabled false

kv_id=$(az keyvault create \
    --name "$KEY_VAULT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION"  \
    --query "id" -o tsv)

az keyvault update \
    --name "$KEY_VAULT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --public-network-access "Disabled"

kv_pe_id=$(az network private-endpoint create \
    --name "${KEY_VAULT_NAME}-pe" \
    --resource-group "$RESOURCE_GROUP" \
    --vnet-name "$VNET_NAME" \
    --subnet "$SUBNET_PE_NAME" \
    --private-connection-resource-id $(az keyvault show --name "$KEY_VAULT_NAME" --resource-group "$RESOURCE_GROUP" --query "id" -o tsv) \
    --group-id "vault" \
    --connection-name "${KEY_VAULT_NAME}-connection" \
    --query "id" -o tsv)

nic_id=$(az network private-endpoint show --ids $kv_pe_id --query "networkInterfaces[0].id" -o tsv)
ip_address=$(az network nic show --ids $nic_id --query "ipConfigurations[0].privateIPAddress" -o tsv)

az network private-dns record-set a add-record \
    --resource-group "$RESOURCE_GROUP" \
    --zone-name "$KV_DNS_ZONE_NAME" \
    --record-set-name "$KEY_VAULT_NAME" \
    --ipv4-address $ip_address

az network private-endpoint dns-zone-group create \
    --resource-group "$RESOURCE_GROUP" \
    --endpoint-name "${KEY_VAULT_NAME}-pe" \
    --name "default" \
    --private-dns-zone "$KV_DNS_ZONE_NAME" \
    --zone-name "$KV_DNS_ZONE_NAME"

###

link_name="${CR_DNS_ZONE_NAME//\./-}-link"

az network private-dns zone create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$CR_DNS_ZONE_NAME"

az network private-dns link vnet create \
    --resource-group "$RESOURCE_GROUP" \
    --zone-name "$CR_DNS_ZONE_NAME" \
    --name "$link_name" \
    --virtual-network "$vnet_id" \
    --registration-enabled false

acr_id=$(az acr create \
    --name "$CONTAINER_REGISTRY_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --sku "Premium" \
    --admin-enabled true  \
    --query "id" -o tsv)

az acr update \
    --name "$CONTAINER_REGISTRY_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --public-network-enabled false

acr_pe_id=$(az network private-endpoint create \
    --name "${CONTAINER_REGISTRY_NAME}-pe" \
    --resource-group "$RESOURCE_GROUP" \
    --vnet-name "$VNET_NAME" \
    --subnet "$SUBNET_PE_NAME" \
    --private-connection-resource-id $(az acr show --name "$CONTAINER_REGISTRY_NAME" --resource-group "$RESOURCE_GROUP" --query "id" -o tsv) \
    --group-id "registry" \
    --connection-name "${CONTAINER_REGISTRY_NAME}-connection" \
    --query "id" -o tsv)

nic_id=$(az network private-endpoint show --ids $acr_pe_id --query "networkInterfaces[0].id" -o tsv)
ip_address=$(az network nic show --ids $nic_id --query "ipConfigurations[0].privateIPAddress" -o tsv)

az network private-endpoint dns-zone-group create \
    --resource-group "$RESOURCE_GROUP" \
    --endpoint-name "${CONTAINER_REGISTRY_NAME}-pe" \
    --name "default" \
    --private-dns-zone "$CR_DNS_ZONE_NAME" \
    --zone-name "$CR_DNS_ZONE_NAME"

###

monitor_id=$(az monitor app-insights component create \
    --app "$APP_INSIGHTS_NAME" \
    --location "$LOCATION" \
    --resource-group "$RESOURCE_GROUP" \
    --application-type "web"  \
    --query "id" -o tsv)

###

hub_id=$(az ml workspace create --kind hub \
    --resource-group "$RESOURCE_GROUP" \
    --name "$HUB_NAME" \
    --location "$LOCATION" \
    --storage-account $storage_id \
    --key-vault $kv_id \
    --container-registry $acr_id \
    --application-insights $monitor_id \
    --public-network-access Disabled \
    --image-build-compute "ibc_compute" \
    --managed-network allow_internet_outbound \
    --system-datastores-auth-mode "identity" \
    --query "id" -o tsv)


###

hub_pe_id=$(az network private-endpoint create \
    --name "${HUB_NAME}-pe" \
    --resource-group "$RESOURCE_GROUP" \
    --vnet-name "$VNET_NAME" \
    --subnet "$SUBNET_PE_NAME" \
    --private-connection-resource-id $(az ml workspace show --name "$HUB_NAME" --resource-group "$RESOURCE_GROUP" --query "id" -o tsv) \
    --group-id "amlworkspace" \
    --location "$LOCATION" \
    --connection-name "${HUB_NAME}-connection" \
    --query "id" -o tsv)

###

link_name="privatelink.api.azureml.ms-link"

az network private-dns zone create \
    -g "$RESOURCE_GROUP" \
    --name 'privatelink.api.azureml.ms'

az network private-dns link vnet create \
    -g "$RESOURCE_GROUP" \
    --zone-name privatelink.api.azureml.ms \
    --name $link_name \
    --virtual-network "$vnet_id" --registration-enabled false


nic_id=$(az network private-endpoint show --ids $hub_pe_id --query "networkInterfaces[0].id" -o tsv)
ip_address=$(az network nic show --ids $nic_id --query "ipConfigurations[0].privateIPAddress" -o tsv)

az network private-dns record-set a add-record \
    --resource-group "$RESOURCE_GROUP" \
    --zone-name "privatelink.api.azureml.ms" \
    --record-set-name "$HUB_NAME" \
    --ipv4-address $ip_address

az network private-endpoint dns-zone-group create \
    -g "$RESOURCE_GROUP" \
    --endpoint-name "${HUB_NAME}-pe" \
    --name default \
    --private-dns-zone 'privatelink.api.azureml.ms' \
    --zone-name 'privatelink.api.azureml.ms'

###

link_name="privatelink.notebooks.azure.net-link"

az network private-dns zone create \
    -g "$RESOURCE_GROUP" \
    --name 'privatelink.notebooks.azure.net'

az network private-dns link vnet create \
    -g "$RESOURCE_GROUP" \
    --zone-name 'privatelink.notebooks.azure.net' \
    --name $link_name \
    --virtual-network "$vnet_id" --registration-enabled false

az network private-endpoint dns-zone-group add \
    -g "$RESOURCE_GROUP" \
    --endpoint-name "${HUB_NAME}-pe" \
    --name default \
    --private-dns-zone 'privatelink.notebooks.azure.net' \
    --zone-name 'privatelink.notebooks.azure.net'

nic_id=$(az network private-endpoint show --ids $hub_pe_id --query "networkInterfaces[0].id" -o tsv)
ip_address=$(az network nic show --ids $nic_id --query "ipConfigurations[0].privateIPAddress" -o tsv)

az network private-dns record-set a add-record \
    --resource-group "$RESOURCE_GROUP" \
    --zone-name "privatelink.notebooks.azure.net" \
    --record-set-name "$HUB_NAME" \
    --ipv4-address $ip_address

###

az ml workspace provision-network --name "$HUB_NAME" -g "$RESOURCE_GROUP"

###

pid=$(az ml workspace create --kind project \
    --resource-group "$RESOURCE_GROUP" \
    --name "$PROJECT_NAME" \
    --location "$LOCATION" \
    --hub-id $hub_id \
    --query "identity.principal_id" -o tsv)


###
IDENTITY_NAME="sadasaddasd"

az identity create \
  --name $IDENTITY_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

PRINCIPAL_ID=$(az identity show \
  --name $IDENTITY_NAME \
  --resource-group $RESOURCE_GROUP \
  --query principalId \
  --output tsv)

IDENTITY_RESOURCE_ID=$(az identity show \
  --name $IDENTITY_NAME \
  --resource-group $RESOURCE_GROUP \
  --query id \
  --output tsv)

az role assignment create \
  --role "Reader" \
  --assignee-object-id $PRINCIPAL_ID \
  --assignee-principal-type ServicePrincipal \
  --scope $storage_id

az role assignment create \
  --role "Storage Account Contributor" \
  --assignee-object-id $PRINCIPAL_ID \
  --assignee-principal-type ServicePrincipal \
  --scope $storage_id

az role assignment create \
  --role "Storage Blob Data Contributor" \
  --assignee-object-id $PRINCIPAL_ID \
  --assignee-principal-type ServicePrincipal \
  --scope $storage_id

az role assignment create \
  --role "Storage File Data Privileged Contributor" \
  --assignee-object-id $PRINCIPAL_ID \
  --assignee-principal-type ServicePrincipal \
  --scope $storage_id

az role assignment create \
  --role "Storage Table Data Contributor" \
  --assignee-object-id $PRINCIPAL_ID \
  --assignee-principal-type ServicePrincipal \
  --scope $storage_id

sleep 100

az ml compute create --name "$COMPUTE_NAME" --size Standard_E4ds_v4 --type computeinstance --resource-group "$RESOURCE_GROUP" --workspace-name  "$HUB_NAME" --enable-node-public-ip false --identity-type UserAssigned --user-assigned-identities $IDENTITY_RESOURCE_ID

###

#az ml connection create --file {connection.yml} --resource-group "$RESOURCE_GROUP" --workspace-name "$HUB_NAME"

###
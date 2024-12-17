param(
    [Parameter(Mandatory=$false)]
    [string]$storageAccountName,
    
    [Parameter(Mandatory=$false)]
    [string]$resourceGroup,

    [Parameter(Mandatory=$false)]
    [string]$location = "eastus",

    [Parameter(Mandatory=$false)]
    [string]$skuName = "Standard_LRS"
)

# Import utility functions
. "$PSScriptRoot/utils.ps1"

if (-not $resourceGroup) {
    $resourceGroup = Read-Host -Prompt "Enter the resource group"
}

if (-not $storageAccountName) {
    $storageAccountName = Read-Host -Prompt "Enter the storage account name"
}

# Get or create resource group
$resourceGroup = Get-OrCreateResourceGroup -resourceGroupName $resourceGroup

# wait for the resource group to be ready
while (-not (Get-AzResourceGroup -Name $resourceGroup -ErrorAction SilentlyContinue)) {
    Write-Host "Waiting for resource group '$resourceGroup' to be ready..."
    Start-Sleep -Seconds 5
}

Write-Host "Deploying Storage Account '$storageAccountName'..."
az deployment group create `
    --resource-group $resourceGroup `
    --template-file "$PSScriptRoot/storage-template.json" `
    --parameters `
        storageAccountName=$storageAccountName `
        location=$location `
        skuName=$skuName `
        allowBlobPublicAccess=true `
        allowSharedKeyAccess=true

# Check if the deployment was successful
if ($?) {
    Write-Host "Storage resources deployed successfully."
} else {
    Write-Host "Deployment failed."
}

# example of running the script
# .\deploy-storage-resources.ps1 -storageAccountName "shannonstorage" -resourceGroup "nextech-shannon-rg" -location "eastus"

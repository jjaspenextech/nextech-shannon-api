param(
    [Parameter(Mandatory=$false)]
    [string]$siteName,
    
    [Parameter(Mandatory=$false)]
    [string]$resourceGroup,

    [Parameter(Mandatory=$false)]
    [string]$allowedOrigins,

    [Parameter(Mandatory=$false)]
    [string]$sku = "F1",

    [Parameter(Mandatory=$false)]
    [string]$location = "eastus2"
)

# Import utility functions
. "$PSScriptRoot/utils.ps1"

if (-not $resourceGroup) {
    $resourceGroup = Read-Host -Prompt "Enter the resource group"
}

if (-not $siteName) {
    $siteName = Read-Host -Prompt "Enter the Python API site name"
    $siteName = "$($siteName)-api"
}

# if allow origins is not provided, set it to the site name
if (-not $allowedOrigins) {
    $allowedOrigins = "[https://$($siteName).azurewebsites.net]"
}

# Print the parameters for debugging
Write-Output "Parameters:"
Write-Output "siteName: $siteName"
Write-Output "planName: $planName"
Write-Output "sku: $sku"
Write-Output "allowedOrigins: $allowedOrigins"

# Get or create resource group and plan
$resourceGroup = Get-OrCreateResourceGroup -resourceGroupName $resourceGroup -location $location
if (-not $resourceGroup) {
    Write-Host "Failed to create the resource group. Exiting..."
    exit 1
}

$planName = if ($env:CUSTOM_PLAN_NAME) { $env:CUSTOM_PLAN_NAME } else { "$($siteName)-plan" }
$planName = Get-OrCreateAppServicePlan -planName $planName -resourceGroup $resourceGroup -sku $sku -kind "linux"
if (-not $planName) {
    Write-Host "Failed to create the App Service Plan. Exiting..."
    exit 1
}

# Fetch the resource ID of the App Service Plan
$planResourceId = az resource show --resource-group $resourceGroup --name $planName --resource-type "Microsoft.Web/serverfarms" --query "id" -o tsv
if (-not $planResourceId) {
    Write-Host "Failed to fetch the resource ID of the App Service Plan. Exiting..."
    exit 1
}

Write-Host "App Service Plan Resource ID: $planResourceId"

# Simulate the deployment to see the template with parameters
Write-Host "Simulating deployment to see the template with parameters..."
az deployment group what-if `
    --resource-group $resourceGroup `
    --template-file "$PSScriptRoot/python-api-template.json" `
    --parameters `
        siteName=$siteName `
        serverFarmId=$planResourceId `
        sku=$sku `
        allowedOrigins=$allowedOrigins

# Deploy the Python API App Service
Write-Host "Deploying Python API App Service '$siteName'..."
az deployment group create `
    --resource-group $resourceGroup `
    --template-file "$PSScriptRoot/python-api-template.json" `
    --parameters `
        siteName=$siteName `
        serverFarmId=$planResourceId `
        sku=$sku `
        allowedOrigins=$allowedOrigins

# Check if the deployment was successful
if ($?) {
    # Configure Python version and startup command
    Write-Host "Configuring Python settings..."
    az webapp config set --name $siteName --resource-group $resourceGroup --linux-fx-version "PYTHON|3.12"
    az webapp config set --name $siteName --resource-group $resourceGroup --startup-file "pip install -r requirements.txt && python -m uvicorn main:app --host 0.0.0.0"
} else {
    Write-Host "Deployment failed. Skipping configuration steps."
}

# example of how to call this script
# .\deploy-python-api-azure-resources.ps1 -siteName "my-site" -resourceGroup "my-resource-group" -allowedOrigins @("https://my-site.azurewebsites.net") -sku "F1"

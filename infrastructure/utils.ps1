# Gets or creates a resource group with the given name
function Get-OrCreateResourceGroup {
    param (
        [Parameter(Mandatory=$true)]
        [string]$resourceGroupName
    )

    Write-Host "Checking resource group '$resourceGroupName'..."
    $rg = az group show --name $resourceGroupName 2>$null
    if (-not $rg) {
        Write-Host "Creating resource group '$resourceGroupName'..."
        az group create --name $resourceGroupName --location "eastus2"
    } else {
        Write-Host "Using existing resource group '$resourceGroupName'."
    }
    return $resourceGroupName
}

# Gets or creates an App Service Plan with the given name
function Get-OrCreateAppServicePlan {
    param (
        [Parameter(Mandatory=$true)]
        [string]$planName,
        
        [Parameter(Mandatory=$true)]
        [string]$resourceGroup,
        
        [Parameter(Mandatory=$true)]
        [string]$sku,

        [Parameter(Mandatory=$false)]
        [string]$location="eastus",

        [Parameter(Mandatory=$false)]
        [string]$kind=""
    )

    Write-Host "Checking App Service Plan '$planName'..."
    $plan = az appservice plan show --name $planName --resource-group $resourceGroup 2>$null
    if ($kind -eq "linux") {
        $templateFile = "$PSScriptRoot/linux-plan-template.json"
    } else {
        $templateFile = "$PSScriptRoot/windows-plan-template.json"
    }
    if (-not $plan) {
        Write-Host "Creating App Service Plan '$planName'..."
        az deployment group create `
            --resource-group $resourceGroup `
            --template-file $templateFile `
            --parameters planName=$planName sku=$sku location=$location
    } else {
        Write-Host "Using existing App Service Plan '$planName'."
    }
    return $planName
} 

function Get-AzResourceGroup {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Name
    )
    return az group show --name $Name 2>$null
}

function Get-AzAppServicePlan {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Name,
        [Parameter(Mandatory=$true)]
        [string]$ResourceGroup
    )
    return az appservice plan show --name $Name --resource-group $ResourceGroup 2>$null
}

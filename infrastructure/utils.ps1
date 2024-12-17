# Gets or creates a resource group with the given name
function Get-OrCreateResourceGroup {
    param (
        [Parameter(Mandatory=$true)]
        [string]$resourceGroupName,

        [Parameter(Mandatory=$false)]
        [string]$location = "eastus2"
    )

    Write-Host "Checking resource group '$resourceGroupName'..."
    $rg = az group show --name $resourceGroupName 2>$null
    if (-not $rg) {
        Write-Host "Creating resource group '$resourceGroupName'..."
        $result = az group create --name $resourceGroupName --location $location 2>$null
        if ($result.Contains("ERROR")) {
            Write-Host "Error creating resource group: $result"
            exit 1
        }

        # wait for the resource group to be ready, maximum 2 minutes
        $maxAttempts = 120/5
        $attempt = 0
        # get status of the resource group
        $test_rg = az group show --name $resourceGroupName | ConvertFrom-Json
        Write-Host "test_rg: $test_rg"
        $rg = az group show --name $resourceGroupName 2>$null | ConvertFrom-Json
        while (-not $rg) {
            Write-Host "Waiting for resource group '$resourceGroupName' to be ready..."
            Start-Sleep -Seconds 5
            $attempt++
            if ($attempt -ge $maxAttempts) {
                Write-Host "Resource group '$resourceGroupName' did not become ready within the timeout period."
                exit 1
            }
            $rg = az group show --name $resourceGroupName 2>$null
        }
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
        [string]$kind = "windows",

        [Parameter(Mandatory=$false)]
        [string]$location="eastus2"
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
        $result = az deployment group create `
            --resource-group $resourceGroup `
            --template-file $templateFile `
            --parameters planName=$planName sku=$sku location=$location 2>$null
        if ($result.Contains("ERROR")) {
            Write-Host "Error creating app service plan: $result"
            exit 1
        }

        # wait for the app service plan to be ready, maximum 2 minutes
        $maxAttempts = 120/5
        $attempt = 0
        $plan = az appservice plan show --name $planName --resource-group $resourceGroup 2>$null
        while (-not $plan) {
            Write-Host "Waiting for app service plan '$planName' to be ready..."
            Start-Sleep -Seconds 5
            $attempt++
            if ($attempt -ge $maxAttempts) {
                Write-Host "App service plan '$planName' did not become ready within the timeout period."
                exit 1
            }
            $plan = az appservice plan show --name $planName --resource-group $resourceGroup 2>$null
        }
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
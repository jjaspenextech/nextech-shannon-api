param(    
    [Parameter(Mandatory=$false)]
    [string]$projectName = "enterprise-llm-chat"
)

$organizationUrl = $env:PERSONAL_ADO_ORGANIZATION
$pat = $env:PERSONAL_ADO_TOKEN

# Encode PAT for authentication
$base64AuthInfo = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes(":$($pat)"))
$headers = @{
    Authorization = "Basic $base64AuthInfo"
    'Content-Type' = 'application/json'
}

# Create project
$createProjectUrl = "$organizationUrl/_apis/projects?api-version=7.0"
$projectBody = @{
    name = $projectName
    description = "Enterprise LLM Chat Application"
    visibility = "private"
    capabilities = @{
        versioncontrol = @{
            sourceControlType = "Git"
        }
        processTemplate = @{
            templateTypeId = "6b724908-ef14-45cf-84f8-768b5384da45" # Agile process template
        }
    }
} | ConvertTo-Json

Write-Host "Creating project '$projectName'..."
$project = Invoke-RestMethod -Uri $createProjectUrl -Method Post -Headers $headers -Body $projectBody

# Wait for project creation to complete
Start-Sleep -Seconds 5

# Create main repository
$repoUrl = "$organizationUrl/$projectName/_apis/git/repositories?api-version=7.0"
$repoBody = @{
    name = "enterprise-llm-chat"
    project = @{
        id = $project.id
    }
} | ConvertTo-Json

Write-Host "Creating main repository..."
$repo = Invoke-RestMethod -Uri $repoUrl -Method Post -Headers $headers -Body $repoBody

# Create pipeline definition
$pipelineUrl = "$organizationUrl/$projectName/_apis/pipelines?api-version=7.0"
$pipelineBody = @{
    name = "Infrastructure Pipeline"
    folder = "\"
    configuration = @{
        type = "yaml"
        path = "/azure-pipelines.yml"
        repository = @{
            id = $repo.id
            type = "azureReposGit"
        }
    }
} | ConvertTo-Json

Write-Host "Creating pipeline definition..."
$pipeline = Invoke-RestMethod -Uri $pipelineUrl -Method Post -Headers $headers -Body $pipelineBody

Write-Host "Setup complete!"
Write-Host "Project URL: $organizationUrl/$projectName" 
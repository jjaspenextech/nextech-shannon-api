# Create a 'dist' directory and copy files, excluding .local.env and __pycache__
Write-Host "Preparing files for deployment..."
# the dist path is one folder up from the script root
$distPath = "$PSScriptRoot/../dist"
$appPath = "$PSScriptRoot/../app"
if (Test-Path $distPath) {
    Remove-Item -Recurse -Force $distPath
}
New-Item -ItemType Directory -Path $distPath

# Copy files to 'dist', excluding .local.env and __pycache__ directories
Copy-Item -Path $appPath -Destination $distPath -Recurse -Exclude ".local.env", "__pycache__"

# example of how to call this script
# .\prepare-python-api.ps1
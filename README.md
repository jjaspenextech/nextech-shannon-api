# Enterprise LLM Chat API

Python FastAPI backend for the Enterprise LLM Chat application.

## Prerequisites

- Python 3.12+
- Azure CLI installed and configured
- Azure subscription
- Azure DevOps account with appropriate permissions

## Environment Variables Required

```env
AZURE_OPENAI_API_KEY=<your-azure-openai-key>
AZURE_OPENAI_URL=<your-azure-openai-url>
AZURE_OPENAI_API_VERSION=<api-version>
AZURE_OPENAI_MODEL=<model-name>
AZURE_SUBSCRIPTION_ID=<subscription-id>
```

## Deployment Instructions

### 1. Deploy Azure Resources

The `infrastructure` folder contains scripts and templates for deploying the API to Azure:

Navigate to the infrastructure folder

```bash
cd api/infrastructure
```

Deploy the Python API (interactive mode)

```bash
.\deploy-python-api.ps1 -siteName "your-api-name" -resourceGroup "your-resource-group-name"
```

Deploy the Azure Storage Tables

```bash
.\deploy-storage-resources.ps1 -storageAccountName "your-storage-account-name" -resourceGroup "your-resource-group-name"
```

## Local Development

1. Create a virtual environment:

```bash
python -m venv .venv
```

2. Activate the virtual environment:

```bash
source venv/bin/activate # On Windows: .\venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the FastAPI server:

```bash
uvicorn main:app --reload
```


terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  
  backend "azurerm" {
    # Will be configured in pipeline
  }
}

provider "azurerm" {
  features {}
}

# Resource Group
resource "azurerm_resource_group" "rg" {
  name     = "${var.project_name}-rg"
  location = var.location
}

# App Service Plan
resource "azurerm_service_plan" "plan" {
  name                = "${var.project_name}-plan"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type            = "Linux"
  sku_name           = var.app_service_sku

  tags = var.tags
}

# App Service
resource "azurerm_linux_web_app" "api" {
  name                = "${var.project_name}-api"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  service_plan_id     = azurerm_service_plan.plan.id

  site_config {
    application_stack {
      python_version = "3.12"
    }
    always_on = false

    cors {
      allowed_origins = var.allowed_origins
    }
  }

  app_settings = {
    "AZURE_OPENAI_API_KEY"       = ""
    "AZURE_OPENAI_URL"           = ""
    "AZURE_OPENAI_API_VERSION"   = ""
    "AZURE_OPENAI_MODEL"         = ""
    "AZURE_SUBSCRIPTION_ID"      = ""
  }

  tags = var.tags
}

# Storage Account
resource "azurerm_storage_account" "storage" {
  name                     = "${var.project_name}storage"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  blob_properties {
    cors_rule {
      allowed_headers    = ["*"]
      allowed_methods    = ["GET", "POST", "PUT", "DELETE"]
      allowed_origins    = var.allowed_origins
      exposed_headers    = ["*"]
      max_age_in_seconds = 3600
    }
  }

  tags = var.tags
}

# Storage Tables
resource "azurerm_storage_table" "tables" {
  for_each             = toset(["users", "projects", "conversations", "messages", "contexts", "signupCodes"])
  name                 = each.key
  storage_account_name = azurerm_storage_account.storage.name
}

# Storage Containers
resource "azurerm_storage_container" "contexts" {
  name                  = "contexts"
  storage_account_name  = azurerm_storage_account.storage.name
  container_access_type = "container"
} 
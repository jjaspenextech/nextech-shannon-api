variable "project_name" {
  type        = string
  description = "Base name for all resources"
}

variable "location" {
  type        = string
  description = "Azure region for resources"
  default     = "eastus2"
}

variable "app_service_sku" {
  type        = string
  description = "SKU for App Service Plan"
  default     = "F1"
}

variable "allowed_origins" {
  type        = list(string)
  description = "Allowed CORS origins"
  default     = ["*"]
}

variable "tags" {
  type        = map(string)
  description = "Tags for resources"
  default = {
    Environment = "Development"
    Project     = "Enterprise LLM Chat"
  }
} 
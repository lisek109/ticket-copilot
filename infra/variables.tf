variable "prefix" {
  description = "Short prefix used for resource names."
  type        = string
  default     = "ticketcopilot"
}

variable "location" {
  description = "Azure region."
  type        = string
  default     = "westeurope"
}

variable "resource_group_name" {
  description = "Resource group name."
  type        = string
  default     = "tomekcopilot-rg"
}

variable "container_image" {
  description = "Full container image reference (ACR login server + repo + tag)."
  type        = string
  default     = "" # set after first ACR push!!!!
}

variable "budget_amount_eur" {
  description = "Monthly budget amount in EUR for cost control."
  type        = number
  default     = 200
}

variable "budget_email" {
  description = "Email to notify when budget thresholds are hit."
  type        = string
  default     = "tomasz@onet.pl"
}

variable "azure_openai_endpoint" {
  type        = string
  description = "Azure OpenAI endpoint, e.g. https://xxx.openai.azure.com"
}

variable "azure_openai_deployment" {
  type        = string
  description = "Azure OpenAI deployment name (model deployment)."
}

variable "azure_openai_api_version" {
  type        = string
  description = "Azure OpenAI api-version."
  default     = "2024-02-15-preview"
}

variable "azure_openai_api_key" {
  type        = string
  description = "Azure OpenAI API key (SECRET)."
  sensitive   = true
}

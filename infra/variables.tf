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

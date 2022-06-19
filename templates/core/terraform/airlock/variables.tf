variable "tre_id" {}
variable "location" {}
variable "resource_group_name" {}
variable "airlock_storage_subnet_id" {}
variable "airlock_events_subnet_id" {}
variable "enable_local_debugging" {}
variable "virtual_network_id" {}
variable "api_principal_id" {}

variable "docker_registry_server" {
  type        = string
  description = "Docker registry server"
}

variable "airlock_processor_image_repository" {
  type        = string
  description = "Repository for Airlock processor image"
  default     = "microsoft/azuretre/airlock-processor"
}

variable "mgmt_resource_group_name" {
  type        = string
  description = "Shared management resource group"
}

variable "mgmt_acr_name" {
  type        = string
  description = "Management ACR name"
}

variable "arm_subscription_id" {
  description = "The TRE subscription id."
  type        = string
  default     = ""
}

variable "airlock_app_service_plan_sku_size" {
  type    = string
  default = "P1v3"
}

variable "airlock_processor_subnet_id" {}

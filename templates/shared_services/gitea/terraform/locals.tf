locals {
  core_vnet                = "vnet-${var.tre_id}"
  core_resource_group_name = "rg-${var.tre_id}"
  webapp_name              = "gitea-${var.tre_id}"
}
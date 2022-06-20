data "azurerm_private_dns_zone" "eventgrid" {
  name                = "privatelink.eventgrid.azure.net"
  resource_group_name = var.resource_group_name
}

# Event grid topics
resource "azurerm_eventgrid_topic" "step_result" {
  name                          = local.step_result_topic_name
  location                      = var.location
  resource_group_name           = var.resource_group_name
  public_network_access_enabled = false

  identity {
    type = "SystemAssigned"
  }

  tags = {
    Publishers = "Airlock Processor;"
  }
}

resource "azurerm_role_assignment" "servicebus_sender_step_result" {
  scope                = data.azurerm_servicebus_namespace.airlock_sb.id
  role_definition_name = "Azure Service Bus Data Sender"
  principal_id         = azurerm_eventgrid_topic.step_result.principal_id
}


resource "azurerm_private_endpoint" "eg_step_result" {
  name                = "pe-eg-step-result-${var.tre_id}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.airlock_events_subnet_id
  lifecycle { ignore_changes = [tags] }

  private_dns_zone_group {
    name                 = "private-dns-zone-group"
    private_dns_zone_ids = [data.azurerm_private_dns_zone.eventgrid.id]
  }

  private_service_connection {
    name                           = "psc-eg-${var.tre_id}"
    private_connection_resource_id = azurerm_eventgrid_topic.step_result.id
    is_manual_connection           = false
    subresource_names              = ["topic"]
  }
}


resource "azurerm_eventgrid_topic" "status_changed" {
  name                          = local.status_changed_topic_name
  location                      = var.location
  resource_group_name           = var.resource_group_name
  public_network_access_enabled = false

  identity {
    type = "SystemAssigned"
  }

  tags = {
    Publishers = "TRE API;"
  }
}

resource "azurerm_role_assignment" "servicebus_sender_status_changed" {
  scope                = data.azurerm_servicebus_namespace.airlock_sb.id
  role_definition_name = "Azure Service Bus Data Sender"
  principal_id         = azurerm_eventgrid_topic.status_changed.principal_id
}

resource "azurerm_private_endpoint" "eg_status_changed" {
  name                = "pe-eg-status-changed-${var.tre_id}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.airlock_events_subnet_id
  lifecycle { ignore_changes = [tags] }

  private_dns_zone_group {
    name                 = "private-dns-zone-group"
    private_dns_zone_ids = [data.azurerm_private_dns_zone.eventgrid.id]
  }

  private_service_connection {
    name                           = "psc-eg-${var.tre_id}"
    private_connection_resource_id = azurerm_eventgrid_topic.status_changed.id
    is_manual_connection           = false
    subresource_names              = ["topic"]
  }
}


# System topic
resource "azurerm_eventgrid_system_topic" "import_inprogress_blob_created" {
  name                   = local.import_inprogress_sys_topic_name
  location               = var.location
  resource_group_name    = var.resource_group_name
  source_arm_resource_id = azurerm_storage_account.sa_import_in_progress.id
  topic_type             = "Microsoft.Storage.StorageAccounts"

  identity {
    type = "SystemAssigned"
  }

  tags = {
    Publishers = "airlock;import-in-progress-sa"
  }

  depends_on = [
    azurerm_storage_account.sa_import_in_progress
  ]

  lifecycle { ignore_changes = [tags] }
}

resource "azurerm_role_assignment" "servicebus_sender_import_inprogress_blob_created" {
  scope                = data.azurerm_servicebus_namespace.airlock_sb.id
  role_definition_name = "Azure Service Bus Data Sender"
  principal_id         = azurerm_eventgrid_system_topic.import_inprogress_blob_created.principal_id
}


resource "azurerm_eventgrid_system_topic" "import_rejected_blob_created" {
  name                   = local.import_rejected_sys_topic_name
  location               = var.location
  resource_group_name    = var.resource_group_name
  source_arm_resource_id = azurerm_storage_account.sa_import_rejected.id
  topic_type             = "Microsoft.Storage.StorageAccounts"

  identity {
    type = "SystemAssigned"
  }

  tags = {
    Publishers = "airlock;import-rejected-sa"
  }

  depends_on = [
    azurerm_storage_account.sa_import_rejected
  ]

  lifecycle { ignore_changes = [tags] }
}

resource "azurerm_role_assignment" "servicebus_sender_import_rejected_blob_created" {
  scope                = data.azurerm_servicebus_namespace.airlock_sb.id
  role_definition_name = "Azure Service Bus Data Sender"
  principal_id         = azurerm_eventgrid_system_topic.import_rejected_blob_created.principal_id
}

resource "azurerm_eventgrid_system_topic" "export_approved_blob_created" {
  name                   = local.export_approved_sys_topic_name
  location               = var.location
  resource_group_name    = var.resource_group_name
  source_arm_resource_id = azurerm_storage_account.sa_export_approved.id
  topic_type             = "Microsoft.Storage.StorageAccounts"

  identity {
    type = "SystemAssigned"
  }

  tags = {
    Publishers = "airlock;export-approved-sa"
  }

  depends_on = [
    azurerm_storage_account.sa_export_approved
  ]

  lifecycle { ignore_changes = [tags] }
}

resource "azurerm_role_assignment" "servicebus_sender_export_approved_blob_created" {
  scope                = data.azurerm_servicebus_namespace.airlock_sb.id
  role_definition_name = "Azure Service Bus Data Sender"
  principal_id         = azurerm_eventgrid_system_topic.export_approved_blob_created.principal_id
}


# Custom topic (for scanning)
resource "azurerm_eventgrid_topic" "scan_result" {
  name                          = local.scan_result_topic_name
  location                      = var.location
  resource_group_name           = var.resource_group_name
  public_network_access_enabled = false

  identity {
    type = "SystemAssigned"
  }

  tags = {
    Publishers = "airlock;custom scanning service;"
  }

  lifecycle { ignore_changes = [tags] }
}

resource "azurerm_role_assignment" "servicebus_sender_scan_result" {
  scope                = data.azurerm_servicebus_namespace.airlock_sb.id
  role_definition_name = "Azure Service Bus Data Sender"
  principal_id         = azurerm_eventgrid_topic.scan_result.principal_id
}

resource "azurerm_private_endpoint" "eg_scan_result" {
  name                = "pe-eg-scan-result-${var.tre_id}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.airlock_events_subnet_id
  lifecycle { ignore_changes = [tags] }

  private_dns_zone_group {
    name                 = "private-dns-zone-group"
    private_dns_zone_ids = [data.azurerm_private_dns_zone.eventgrid.id]
  }

  private_service_connection {
    name                           = "psc-eg-${var.tre_id}"
    private_connection_resource_id = azurerm_eventgrid_topic.scan_result.id
    is_manual_connection           = false
    subresource_names              = ["topic"]
  }
}

## Subscriptions

resource "azurerm_eventgrid_event_subscription" "step_result" {
  name  = local.step_result_eventgrid_subscription_name
  scope = azurerm_eventgrid_topic.step_result.id

  service_bus_queue_endpoint_id = azurerm_servicebus_queue.step_result.id

  delivery_identity {
    type = "SystemAssigned"
  }

  depends_on = [
    azurerm_eventgrid_topic.step_result
  ]
}

resource "azurerm_eventgrid_event_subscription" "status_changed" {
  name  = local.status_changed_eventgrid_subscription_name
  scope = azurerm_eventgrid_topic.status_changed.id

  service_bus_queue_endpoint_id = azurerm_servicebus_queue.status_changed.id

  delivery_identity {
    type = "SystemAssigned"
  }

  depends_on = [
    azurerm_eventgrid_topic.status_changed
  ]
}

resource "azurerm_eventgrid_event_subscription" "import_inprogress_blob_created" {
  name  = local.import_inprogress_eventgrid_subscription_name
  scope = azurerm_storage_account.sa_import_in_progress.id

  service_bus_topic_endpoint_id = azurerm_servicebus_topic.blob_created.id

  delivery_identity {
    type = "SystemAssigned"
  }

  depends_on = [
    azurerm_eventgrid_system_topic.import_inprogress_blob_created
  ]
}

resource "azurerm_eventgrid_event_subscription" "import_rejected_blob_created" {
  name  = local.import_rejected_eventgrid_subscription_name
  scope = azurerm_storage_account.sa_import_rejected.id

  service_bus_topic_endpoint_id = azurerm_servicebus_topic.blob_created.id

  delivery_identity {
    type = "SystemAssigned"
  }

  # Todo add Dead_letter

  depends_on = [
    azurerm_eventgrid_system_topic.import_rejected_blob_created
  ]
}

resource "azurerm_eventgrid_event_subscription" "export_approved_blob_created" {
  name  = local.export_approved_eventgrid_subscription_name
  scope = azurerm_storage_account.sa_export_approved.id

  service_bus_topic_endpoint_id = azurerm_servicebus_topic.blob_created.id

  delivery_identity {
    type = "SystemAssigned"
  }

  depends_on = [
    azurerm_eventgrid_system_topic.export_approved_blob_created
  ]
}


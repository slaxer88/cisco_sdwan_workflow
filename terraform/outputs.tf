output "system_template_id" {
  description = "ID of the system feature template"
  value       = sdwan_cisco_system_feature_template.test_system.id
}

output "vpn0_template_id" {
  description = "ID of the VPN 0 (transport) feature template"
  value       = sdwan_cisco_vpn_feature_template.test_vpn0.id
}

output "vpn0_interface_template_id" {
  description = "ID of the VPN 0 interface feature template"
  value       = sdwan_cisco_vpn_interface_feature_template.test_vpn0_if.id
}

output "vpn1_template_id" {
  description = "ID of the VPN 1 (service) feature template"
  value       = sdwan_cisco_vpn_feature_template.test_vpn1.id
}

output "vpn512_template_id" {
  description = "ID of the VPN 512 (management) feature template"
  value       = sdwan_cisco_vpn_feature_template.test_vpn512.id
}

output "device_template_id" {
  description = "ID of the device template"
  value       = sdwan_feature_device_template.test_device.id
}

output "localized_policy_id" {
  description = "ID of the localized policy"
  value       = sdwan_localized_policy.test_policy.id
}

output "deployment_summary" {
  description = "Summary of all deployed resources"
  value = {
    site_id         = var.test_site_id
    system_ip       = var.test_system_ip
    hostname        = var.test_hostname
    device_template = sdwan_feature_device_template.test_device.name
    policy          = sdwan_localized_policy.test_policy.name
    feature_templates = [
      sdwan_cisco_system_feature_template.test_system.name,
      sdwan_cisco_vpn_feature_template.test_vpn0.name,
      sdwan_cisco_vpn_interface_feature_template.test_vpn0_if.name,
      sdwan_cisco_vpn_feature_template.test_vpn1.name,
      sdwan_cisco_vpn_feature_template.test_vpn512.name,
    ]
  }
}

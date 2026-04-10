resource "sdwan_feature_device_template" "test_device" {
  name        = "TF_Test_Device_9999"
  description = "Terraform-managed device template for test site 9999"
  device_type = var.device_types[0]

  general_templates = [
    {
      id   = sdwan_cisco_system_feature_template.test_system.id
      type = "cisco_system"
    },
    {
      id   = sdwan_cisco_vpn_feature_template.test_vpn0.id
      type = "cisco_vpn"
      sub_templates = [
        {
          id   = sdwan_cisco_vpn_interface_feature_template.test_vpn0_if.id
          type = "cisco_vpn_interface"
        }
      ]
    },
    {
      id   = sdwan_cisco_vpn_feature_template.test_vpn1.id
      type = "cisco_vpn"
    },
    {
      id   = sdwan_cisco_vpn_feature_template.test_vpn512.id
      type = "cisco_vpn"
    }
  ]
}

resource "sdwan_localized_policy" "test_policy" {
  name        = "TF_Test_Policy_9999"
  description = "Terraform-managed localized policy for test site 9999"

  flow_visibility_ipv4        = true
  flow_visibility_ipv6        = false
  application_visibility_ipv4 = true
  application_visibility_ipv6 = false
  implicit_acl_logging        = true
  log_frequency               = 1000
}

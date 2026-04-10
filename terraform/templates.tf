resource "sdwan_cisco_system_feature_template" "test_system" {
  name         = "TF_Test_System_9999"
  description  = "Terraform-managed system template for test site 9999"
  device_types = var.device_types

  hostname  = var.test_hostname
  system_ip = var.test_system_ip
  site_id   = var.test_site_id
  timezone  = "Asia/Seoul"

  console_baud_rate     = "9600"
  max_omp_sessions      = 2
  track_default_gateway = true
  track_transport       = true
  admin_tech_on_failure = true
}

resource "sdwan_cisco_vpn_feature_template" "test_vpn0" {
  name         = "TF_Test_VPN0_9999"
  description  = "Terraform-managed transport VPN for test site 9999"
  device_types = var.device_types

  vpn_id = 0

  ipv4_static_routes = [
    {
      prefix = "0.0.0.0/0"
      next_hops = [
        {
          address  = var.test_vpn0_default_gw
          distance = 1
        }
      ]
    }
  ]

  dns_ipv4_servers = [
    {
      address = "8.8.8.8"
      role    = "primary"
    },
    {
      address = "8.8.4.4"
      role    = "secondary"
    }
  ]
}

resource "sdwan_cisco_vpn_interface_feature_template" "test_vpn0_if" {
  name         = "TF_Test_VPN0_IF_9999"
  description  = "Terraform-managed WAN interface for test site 9999"
  device_types = var.device_types

  interface_name = var.test_wan_interface
  address        = var.test_wan_ip
  shutdown       = false

  tunnel_interface_encapsulations = [
    {
      encapsulation = "ipsec"
    }
  ]
  tunnel_interface_color         = var.test_wan_color
  tunnel_interface_allow_all     = false
  tunnel_interface_allow_bgp     = false
  tunnel_interface_allow_dhcp    = true
  tunnel_interface_allow_dns     = true
  tunnel_interface_allow_icmp    = true
  tunnel_interface_allow_ssh     = true
  tunnel_interface_allow_https   = true
  tunnel_interface_allow_ntp     = true
  tunnel_interface_allow_ospf    = false
  tunnel_interface_allow_stun    = true
  tunnel_interface_allow_snmp    = false
  tunnel_interface_allow_netconf = false
}

resource "sdwan_cisco_vpn_feature_template" "test_vpn1" {
  name         = "TF_Test_VPN1_9999"
  description  = "Terraform-managed service VPN for test site 9999"
  device_types = var.device_types

  vpn_id   = 1
  vpn_name = "TF_SERVICE"

  omp_advertise_ipv4_routes = [
    {
      protocol = "connected"
    },
    {
      protocol = "static"
    }
  ]
}

resource "sdwan_cisco_vpn_feature_template" "test_vpn512" {
  name         = "TF_Test_VPN512_9999"
  description  = "Terraform-managed management VPN for test site 9999"
  device_types = var.device_types

  vpn_id = 512
}

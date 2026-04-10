variable "vmanage_url" {
  description = "vManage URL (e.g. https://10.70.131.199:43145)"
  type        = string
}

variable "vmanage_username" {
  description = "vManage username"
  type        = string
  sensitive   = true
}

variable "vmanage_password" {
  description = "vManage password"
  type        = string
  sensitive   = true
}

variable "device_types" {
  description = "Target device types for templates"
  type        = list(string)
  default     = ["vedge-C8000V"]
}

variable "test_site_id" {
  description = "Site ID for test templates"
  type        = number
  default     = 9999
}

variable "test_system_ip" {
  description = "System IP for test templates"
  type        = string
  default     = "10.255.99.1"
}

variable "test_hostname" {
  description = "Hostname for test templates"
  type        = string
  default     = "TF-TEST-ROUTER"
}

variable "test_vpn0_default_gw" {
  description = "Default gateway IP for VPN 0 transport"
  type        = string
  default     = "10.0.0.1"
}

variable "test_wan_interface" {
  description = "WAN interface name"
  type        = string
  default     = "GigabitEthernet1"
}

variable "test_wan_ip" {
  description = "WAN interface IP with CIDR"
  type        = string
  default     = "10.0.0.99/24"
}

variable "test_wan_color" {
  description = "WAN tunnel color"
  type        = string
  default     = "biz-internet"
}

terraform {
  required_version = ">= 1.0"

  required_providers {
    sdwan = {
      source  = "CiscoDevNet/sdwan"
      version = "~> 0.11"
    }
  }

  # 로컬 state (PoC)
  # 프로덕션에서는 S3/Terraform Cloud로 전환
  # backend "s3" {
  #   bucket         = "sdwan-terraform-state"
  #   key            = "sdwan/terraform.tfstate"
  #   region         = "ap-northeast-2"
  #   dynamodb_table = "sdwan-terraform-lock"
  #   encrypt        = true
  # }
}

provider "sdwan" {
  url      = var.vmanage_url
  username = var.vmanage_username
  password = var.vmanage_password
  insecure = true
}

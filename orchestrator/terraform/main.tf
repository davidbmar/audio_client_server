provider "aws" {
  region = "us-east-2"
}


#These are just .tf files not modules.
## Load other components like SQS and Secrets Manager
#module "sqs" {
##  source = "./sqs.tf"
#}
#
#module "secrets" {
#  source = "./secrets.tf"
#}
#

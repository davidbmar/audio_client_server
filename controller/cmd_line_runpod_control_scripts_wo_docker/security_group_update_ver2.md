# API Gateway Security Group Rule Updater

## Overview

This Python script updates an AWS EC2 Security Group with ingress rules for API Gateway IP ranges. It's designed to work specifically with the us-east-2 region, fetching the latest API Gateway IP ranges, consolidating them, and adding them to a specified security group.

## Prerequisites

- Python 3.6+
- boto3 library
- requests library
- An AWS account with appropriate permissions
- The Security Group ID you want to update

## Installation

1. Ensure you have Python 3.6 or later installed.
2. Install required libraries:

   ```
   pip install boto3 requests
   ```

3. Set up your AWS credentials. You can do this by:
   - Configuring the AWS CLI (`aws configure`)
   - Setting environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
   - Using an IAM role if running on an EC2 instance

## Usage

1. Update the `security_group_id` variable in the script with your target Security Group ID.
2. Run the script:

   ```
   python security_group_updater.py
   ```

## How It Works
0. This is to protect the port 9000 and allow access only from API GATEWAY ranges

1. **Fetch IP Ranges**: The script downloads the latest AWS IP range information and filters for API Gateway IPs in the us-east-2 region.

2. **Consolidate Ranges**: It then consolidates these IP ranges to minimize the number of security group rules needed.

3. **Update Security Group**: The script attempts to add each consolidated IP range as a new inbound rule to the specified security group.

## Functions

### `fetch_api_gateway_ips_for_region(region='us-east-2')`

Fetches and returns a list of IP networks for API Gateway in the specified region.

### `consolidate_cidr_ranges(ip_ranges)`

Consolidates a list of IP networks into a smaller list of broader CIDR ranges where possible.

## Error Handling

- The script will skip any duplicate rules.
- If the security group rule limit is reached, the script will stop adding new rules and print a message.
- Other errors during rule addition are printed for debugging.

## Limitations

- The script is set to work only with the us-east-2 region. Modify the region parameter in `fetch_api_gateway_ips_for_region()` to use a different region.
- AWS limits the number of rules per security group (typically 60 for VPC security groups). If you hit this limit, consider using alternative methods like Network ACLs.

## Security Considerations

- Ensure that the AWS credentials used have the minimum required permissions to modify the target security group.
- Regularly review and audit the security group rules added by this script.
- Consider implementing more granular controls if your security requirements demand it.

## Troubleshooting

- If you encounter permission errors, verify that your AWS credentials have the necessary permissions to modify security groups.
- For any "ClientError" messages, refer to the AWS SDK documentation for error code meanings.

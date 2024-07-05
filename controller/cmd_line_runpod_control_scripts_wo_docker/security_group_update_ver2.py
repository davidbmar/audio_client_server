#!/usr/bin/python3

import boto3
import requests
import json
import ipaddress

def fetch_api_gateway_ips_for_region(region='us-east-2'):
    response = requests.get('https://ip-ranges.amazonaws.com/ip-ranges.json')
    ip_ranges = json.loads(response.text)['prefixes']
    return [ipaddress.ip_network(item['ip_prefix']) for item in ip_ranges
            if item["service"] == "API_GATEWAY" and item["region"] == region]

def consolidate_cidr_ranges(ip_ranges):
    sorted_ranges = sorted(ip_ranges)
    consolidated = [sorted_ranges[0]]
    for current in sorted_ranges[1:]:
        last = consolidated[-1]
        if current.subnet_of(last):
            continue
        elif current.supernet_of(last):
            consolidated[-1] = current
        elif last.broadcast_address + 1 >= current.network_address:
            consolidated[-1] = ipaddress.ip_network(last.supernet(new_prefix=last.prefixlen - 1))
        else:
            consolidated.append(current)
    return consolidated

sts = boto3.client('sts')
identity = sts.get_caller_identity()
print(json.dumps(identity, indent=2))

# Fetch and consolidate IP ranges for us-east-2
api_gateway_ips = fetch_api_gateway_ips_for_region('us-east-2')
consolidated_ranges = consolidate_cidr_ranges(api_gateway_ips)

print(f"Original IP ranges for us-east-2: {len(api_gateway_ips)}")
print(f"Consolidated IP ranges for us-east-2: {len(consolidated_ranges)}")

# Connect to EC2
ec2 = boto3.client('ec2', region_name='us-east-2')
security_group_id = 'sg-048c6c90805884eef'  # Replace with your security group ID

# Update security group
for ip_range in consolidated_ranges:
    try:
        response = ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 9000,
                    'ToPort': 9000,
                    'IpRanges': [{'CidrIp': str(ip_range)}]
                }
            ]
        )
        print(f"Added rule for {ip_range}")
    except ec2.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
            print(f"Rule for {ip_range} already exists")
        elif e.response['Error']['Code'] == 'RulesPerSecurityGroupLimitExceeded':
            print(f"Reached maximum rules. Last added: {ip_range}")
            break
        else:
            print(f"Error adding rule for {ip_range}: {e}")

print("Security group update completed")

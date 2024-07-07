# Setting up a Secure API Gateway with FastAPI and Apache

## Overview

This document outlines the process of setting up a secure API Gateway that proxies requests to a FastAPI application running on an EC2 instance, protected by Apache. The setup ensures that only the API Gateway can access the application directly, enhancing security.

## High-Level Steps

1. Set up EC2 instance with FastAPI application
2. Configure Apache as a reverse proxy
3. Set up API Gateway in AWS
4. Configure API Gateway to proxy requests to EC2
5. Secure EC2 instance by restricting access to API Gateway IPs only

## Detailed Steps

### 1. EC2 and FastAPI Setup

- Launch an EC2 instance
- Install necessary dependencies (Python, FastAPI, Uvicorn)
- Create and run FastAPI application listening on localhost:9000

### 2. Apache Configuration

- Install Apache on EC2 instance
- Configure Apache as a reverse proxy to forward requests to FastAPI
- Set up SSL/TLS with Let's Encrypt

### 3. API Gateway Setup

- Create a new API in API Gateway
- Set up a proxy resource with `{proxy+}` path
- Configure ANY method for the proxy resource

### 4. API Gateway Integration

- Set up HTTP_PROXY integration in API Gateway
- Point the integration to your EC2's public domain (e.g., https://yourdomain.com/pods/{proxy})
- Deploy the API to a stage (e.g., "dev")

### 5. Security Configuration

- Update EC2 security group to allow inbound traffic only from API Gateway IP ranges
- Remove any rules allowing direct access to port 9000 from 0.0.0.0/0

## Key Points and Learnings

1. **FastAPI Configuration**: Ensure FastAPI is configured to run on localhost to prevent direct external access.

2. **Apache Proxy**: Properly configure Apache to forward requests to FastAPI. This is crucial for the API Gateway integration to work.

3. **API Gateway Proxy Setup**: Use `{proxy+}` in API Gateway to catch all paths and HTTP_PROXY integration type for seamless forwarding.

4. **SSL/TLS**: Ensure proper SSL/TLS setup on your EC2 instance for secure communication.

5. **Security Groups**: Carefully manage EC2 security groups. Allow incoming traffic on port 443 from API Gateway IP ranges only.

6. **Testing**: Thoroughly test the setup at each stage:
   - Direct access to FastAPI (should work locally on EC2)
   - Access through your domain (should work)
   - Access through API Gateway (should work)
   - Direct external access to port 9000 (should fail)

7. **IP Range Management**: API Gateway IP ranges can change. Consider automating the security group update process.

8. **Logging and Monitoring**: Implement comprehensive logging in FastAPI and monitor CloudWatch logs for API Gateway to track requests and diagnose issues.

## Notes

- Keep your Terraform scripts (if used) version controlled for easy management and reproduction of the infrastructure.
- Regularly update your API Gateway IP ranges in the EC2 security group.
- Consider using AWS Systems Manager Session Manager for secure EC2 access without opening SSH ports.

## Troubleshooting Tips

1. If API Gateway calls fail, check:
   - API Gateway configuration (especially the integration URL)
   - Apache logs
   - FastAPI application logs
   - EC2 security group rules

2. For SSL/TLS issues, verify:
   - Certificate validity
   - Apache SSL configuration

3. If local tests on EC2 succeed but external calls fail, review:
   - Security group settings
   - Apache configuration
   - Network ACLs (if applicable)

## Future Improvements

1. Implement API key authentication in API Gateway for additional security.
2. Set up CloudWatch alarms for monitoring API Gateway and EC2 health.
3. Consider using AWS WAF with API Gateway for additional protection against web exploits.
4. Explore using AWS Lambda for portions of your API that don't require a persistent server.

---

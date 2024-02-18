STAGING_AUDIO2SCRIPTVIEWER_INPUT_FIFO_QUEUE_URL# Terraform and Python Integration Documentation 

## Terraform infrastucture setup.

```console
terraform init
terraform plan
terraform apply
```

# Outputs from TF
Post TF apply, after running "terraform apply" there should be the following outputs:
Outputs:

```console
staging_audio2scriptviewer_input_fifo_queue_url = "https://sqs.us-east-2.amazonaws.com/635071011057/staging_audio2scriptviewer_input_.fifo"
staging_audio2scriptviewer_output_fifo_queue_url = "https://sqs.us-east-2.amazonaws.com/635071011057/staging_audio2scriptviewer_output_.fifo"
```

# Build scripts or CI pipelines
Before running the scripts which require these SQS queues you need to export and get these env variables like this:

```console
export STAGING_AUDIO2SCRIPTVIEWER_INPUT_FIFO_QUEUE_URL=$(terraform output -raw staging_audio2scriptviewer_input_fifo_queue_url)
export STAGING_AUDIO2SCRIPTVIEWER_OUTPUT_FIFO_QUEUE_URL=$(terraform output -raw staging_audio2scriptviewer_output_fifo_queue_url)
```

So to get these env variables into your shell run:
```console
'source setup_env_vars.sh'
```

#So in the python scripts, to drive off of this infrastucture you should use something like this:
```console
STAGING_AUDIO2SCRIPTVIEWER_INPUT_FIFO_QUEUE_URL = os.getenv('STAGING_AUDIO2SCRIPTVIEWER_INPUT_FIFO_QUEUE_URL')
STAGING_AUDIO2SCRIPTVIEWER_OUTPUT_FIFO_QUEUE_URL = os.getenv('STAGING_AUDIO2SCRIPTVIEWER_OUTPUT_FIFO_QUEUE_URL')

def send_message_to_queue(message_body):
    response = sqs_client.send_message(
        QueueUrl=STAGING_AUDIO2SCRIPTVIEWER_INPUT_FIFO_QUEUE_URL,
        MessageBody=message_body
    )
    return response
```

---
## Terraform Resource Naming Conventions
Terraform resources should be named following a clear, consistent pattern that reflects the environment, purpose, and type of resource. 

## Python Integration
When Terraform resource names change, these can be reflected in Python through the use of Terraform outputs and environment variables.

## Terraform Outputs
Outputs can be defined in Terraform to expose resource properties, such as an SQS queue URL, which can then be used in Python code.

```hcl
output "order_processing_queue_url" {
  value = aws_sqs_queue.order_processing_queue_dev.url
}


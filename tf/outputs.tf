# outputs.tf

output "sqs_queue_url" {
  value = aws_sqs_queue.queue.id
}

output "input_bucket_name" {
  value = aws_s3_bucket.input_bucket.bucket
}

output "output_bucket_name" {
  value = aws_s3_bucket.output_bucket.bucket
}

output "application_role_arn" {
  value = aws_iam_role.application_role.arn
}


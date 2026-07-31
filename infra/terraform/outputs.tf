output "app_url" {
  value       = "http://${aws_lb.main.dns_name}"
  description = "Public URL of the application"
}

output "ecr_repository_url" {
  value       = aws_ecr_repository.app.repository_url
  description = "ECR repository URL — used by GitHub Actions to push images"
}

output "deploy_role_arn" {
  value       = aws_iam_role.github_actions_deploy.arn
  description = "IAM role ARN for GitHub Actions — set as AWS_ROLE_ARN secret"
}

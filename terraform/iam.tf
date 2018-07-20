resource "aws_iam_policy" "ecs_ci_drainer_asg_notification_policy" {
  name = "ECSCIDrainerAutoScalingGroupNotificationPolicy"

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Resource": "*",
            "Action": [
                "sqs:SendMessage",
                "sqs:GetQueueUrl",
                "sns:Publish"
            ]
        }
    ]
}
EOF
}

resource "aws_iam_policy" "ecs_ci_drainer_lambda_excution_policy" {
  name = "ECSCIDrainerLambdaExcutionPolicy"
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "ec2:DescribeInstances",
                "ec2:DescribeInstanceAttribute",
                "ec2:DescribeInstanceStatus",
                "ec2:DescribeHosts",
                "ecs:ListContainerInstances",
                "ecs:DescribeContainerInstances",
                "ecs:ListTasks",
                "ecs:DescribeTasks",
                "ecs:listServices",
                "ecs:DescribeServices",
                "ecs:updateService"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Resource": "*",
            "Action": [
                "sns:ListSubscriptions",
                "sns:Publish"
            ]
        }
    ]
}
EOF
}


resource "aws_iam_role" "ecs_lambda_execute_role_for_container_instance_draining" {
  name = "ECS-LambdaExecuteRoleForContainerInstanceDraining"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "ecs_lambda_excution_role_instance_drainig" {
  role = "${aws_iam_role.ecs_lambda_execute_role_for_container_instance_draining.name}"
  policy_arn = "${aws_iam_policy.ecs_ci_drainer_lambda_excution_policy.arn}"
}

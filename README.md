## Intro
AWS-ECS 클러스터 인스턴스가 `Scale-In`될때 드레이닝 해주는 예시 프로젝트입니다.


## Quick start

1. Run `pip install -r requirements.txt`<br />
2. Update `config.yaml`
3. Run `lambda deploy`
	* 배포툴로 [python-lambda](https://github.com/nficano/python-lambda) 라이브러리를 사용하고 있습니다.
4. SNS 주제를 만들고 배포된 람다 함수를 구독
5. 수명주기 후크 생성
	```
    aws autoscaling put-lifecycle-hook --lifecycle-hook-name <훅이름> --auto-scaling-group-name <AS그룹 이름> --lifecycle-transition "autoscaling:EC2_INSTANCE_TERMINATING" --notification-target-arn <SNS ARN> --role-arn <Role ARN> --heartbeat-timeout 300
	```


## Invoke

1. `event.json`을 활용하여 로컬에서 테스트할 수 있습니다.
2. `lambda invoke -v` 명령어로 로컬에서 테스트할 수 있습니다.


## Deploy

`lambda deploy` 명령어를 통해 배포할 수 있습니다(실행하면 `AWS-Lambda` 함수를 만듬). 


## ASG LifeCycle Role
```
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
```

## Lambda Execute Role
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "autoscaling:CompleteLifecycleAction",
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "ec2:DescribeInstances",
                "ec2:DescribeInstanceAttribute",
                "ec2:DescribeInstanceStatus",
                "ec2:DescribeHosts",
                "ecs:ListContainerInstances",
                "ecs:SubmitContainerStateChange",
                "ecs:SubmitTaskStateChange",
                "ecs:DescribeContainerInstances",
                "ecs:UpdateContainerInstancesState",
                "ecs:ListTasks",
                "ecs:DescribeTasks",
                "sns:Publish",
                "sns:ListSubscriptions"
            ],
            "Resource": "*"
        }
    ]
}
```

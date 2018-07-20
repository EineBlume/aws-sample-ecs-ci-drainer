# -*- coding: utf-8 -*-
import base64
import json
import logging
import time

import boto3

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Establish boto3 session
session = boto3.session.Session()
logger.info(f'SESSION: {session.region_name}')

ec2_client = session.client(service_name='ec2')
ecs_client = session.client(service_name='ecs')
asg_client = session.client('autoscaling')
sns_client = session.client('sns')
lambda_client = session.client('lambda')


def _get_cluster_name(ec2_instance_id):
    resp = ec2_client.describe_instance_attribute(InstanceId=ec2_instance_id, Attribute='userData')
    logger.info(f'Describe Instance UserData: {resp}')
    user_data = resp['UserData']
    user_data = base64.b64decode(user_data['Value'])
    tokens = map(lambda x: x.decode('utf-8'), user_data.split())
    for token in tokens:
        if token.find("ECS_CLUSTER") > -1:
            # Split and get the cluster name
            cluster_name = token.split('=')[1]
            return cluster_name
    return None


def _get_container_instance(ec2_instance_id, cluster_name=None):
    if not cluster_name:
        cluster_name = _get_cluster_name(ec2_instance_id)
    if not cluster_name:
        return None

    paginator = ecs_client.get_paginator('list_container_instances')
    pages = paginator.paginate(cluster=cluster_name)

    for page in pages:
        container_instances = page['containerInstanceArns']
        container_resp = ecs_client.describe_container_instances(cluster=cluster_name,
                                                                 containerInstances=container_instances)
        for container_instance in container_resp['containerInstances']:
            if container_instance['ec2InstanceId'] == ec2_instance_id:
                return container_instance
    return None


def _get_task_count_of_container_instance(cluster_name, container_instance_id):
    resp = ecs_client.list_tasks(cluster=cluster_name, containerInstance=container_instance_id)
    logger.debug(f'ListTask Resp: {resp}')
    return len(resp['taskArns'])


def _handle(event):
    line = event['Records'][0]['Sns']['Message']
    message = json.loads(line)

    if 'LifecycleTransition' not in message.keys():
        return

    if 'autoscaling:EC2_INSTANCE_TERMINATING' not in message['LifecycleTransition']:
        return

    ec2_instance_id = message['EC2InstanceId']
    logger.info(f'EC2 Instance ID: {ec2_instance_id}')
    if not ec2_instance_id:
        return

    cluster_name = _get_cluster_name(ec2_instance_id)
    logger.info(f'ClusterName: {cluster_name}')
    if not cluster_name:
        return

    container_instance = _get_container_instance(ec2_instance_id, cluster_name=cluster_name)
    logger.info(f'ContainerInstance: {container_instance}')
    if not container_instance:
        return

    container_instance_id = container_instance['containerInstanceArn']
    container_instance_status = container_instance['status']
    if container_instance_status != 'DRAINING':
        logger.info(f'<ContainerInstance: {container_instance_id}> make status to DRAINING...')
        ecs_client.update_container_instances_state(cluster=cluster_name,
                                                    containerInstances=[container_instance_id],
                                                    status='DRAINING')

    task_count = _get_task_count_of_container_instance(cluster_name, container_instance_id)
    logger.info(f'<ContainerInstance: {container_instance_id}> Task Count: {task_count}')

    # Tasks are not running
    if task_count <= 0:
        logger.info("No tasks are running on instance, completing lifecycle action....")
        hook_name = message['LifecycleHookName']
        asg_group_name = message['AutoScalingGroupName']
        resp = asg_client.complete_lifecycle_action(LifecycleHookName=hook_name,
                                                    AutoScalingGroupName=asg_group_name,
                                                    LifecycleActionResult='CONTINUE',
                                                    InstanceId=ec2_instance_id)
        logger.info(f'Complete Lifecycle Resp: {resp}')
        logger.info("Lifecycle hook action Completed.")
        return

    if task_count > 0:
        topic_arn = event['Records'][0]['Sns']['TopicArn']
        response = sns_client.list_subscriptions()
        for key in response['Subscriptions']:
            if key['TopicArn'] == topic_arn and key['Protocol'] == 'lambda':
                logger.info("Publish to SNS topic %s", topic_arn)

                # 10초 대기
                time.sleep(10)

                resp = sns_client.publish(
                    TopicArn=topic_arn,
                    Message=json.dumps(message),
                    Subject='Publishing SNS message to invoke lambda again..'
                )
                logger.info(f'SNS Publish Resp: {resp}')


@raven_client.capture_exceptions
def handler(event, context):
    logger.info(f'Lambda Event: {event}')

    # noinspection PyBroadException
    try:
        _handle(event)
    except Exception:
        raven_client.captureException()

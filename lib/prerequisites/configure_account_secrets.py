#!/usr/bin/env python3
# Copyright Amazon.com and its affiliates; all rights reserved. This file is Amazon Web Services Content and may not be duplicated or distributed without permission.
# SPDX-License-Identifier: MIT-0
import boto3
import os
import getpass

from lib.configuration import (
    DEPLOYMENT, GITHUB_TOKEN, get_all_configurations
)

if __name__ == '__main__':
    github_token = getpass.getpass(prompt='Enter Github access token value for CodePipeline: ')

    if not github_token:
        raise RuntimeError('You must provide a value for the Github access token')

    response = input((
        "\n"
        f"AWS_PROFILE: {os.environ['AWS_PROFILE']}\n"
        'Are you sure you want to add a secret to AWS Secrets Manager with name '
        f'{get_all_configurations()[DEPLOYMENT][GITHUB_TOKEN]} '
        f'in account: {boto3.client("sts").get_caller_identity().get("Account")} '
        f'and region: {boto3.session.Session().region_name}?\n\n'
        'This should be the Central Deployment Account ID\n\n'
        '(y/n)'
    ))

    if response.lower() == 'y':
        secrets_manager_client = boto3.client('secretsmanager')
        secret_name = get_all_configurations()[DEPLOYMENT][GITHUB_TOKEN]
        print(f'Pushing secret: {secret_name}')
        secrets_manager_client.create_secret(Name=secret_name, SecretString=github_token)
# Copyright Amazon.com and its affiliates; all rights reserved. This file is Amazon Web Services Content and may not be duplicated or distributed without permission.
# SPDX-License-Identifier: MIT-0
import pytest
import aws_cdk as cdk
from aws_cdk.assertions import Template

from boto_mocking_helper import *
from lib.s3_bucket_zones_stack import S3BucketZonesStack

import lib.configuration as configuration
from lib.configuration import (
    DEV, PROD, TEST
)


def test_resource_types_and_counts(monkeypatch):
	monkeypatch.setattr(configuration.boto3, 'client', mock_boto3_client)

	app = cdk.App()

	bucket_stacks = {}
	for environment in [DEV, TEST, PROD]:
		bucket_stacks[environment] = S3BucketZonesStack(
			app,
			f'{environment}-BucketsStackForTests',
			target_environment=environment,
			deployment_account_id=mock_account_id,
		)

	# All stacks should be generated before calling Template methods
	for environment in bucket_stacks.keys():
		template = Template.from_stack(bucket_stacks[environment])
		template.resource_count_is('AWS::S3::Bucket', 4)
		template.resource_count_is('AWS::KMS::Key', 1)


def test_stack_has_correct_outputs(monkeypatch):
	monkeypatch.setattr(configuration.boto3, 'client', mock_boto3_client)

	app = cdk.App()

	bucket_stack = S3BucketZonesStack(
		app,
		'Dev-BucketsStackForTests',
		target_environment='Dev',
		deployment_account_id=mock_account_id,
	)

	template = Template.from_stack(bucket_stack)
	stack_outputs = template.find_outputs('*')

	collect_bucket_output = False
	cleanse_bucket_output = False
	consume_bucket_output = False
	access_logs_bucket_output = False
	s3_kms_key_output = False
	for output_id in stack_outputs.keys():
		output_name = stack_outputs[output_id]['Export']['Name']

		if output_name.find('CollectBucketName') != -1:
			collect_bucket_output = True
		if output_name.find('CleanseBucketName') != -1:
			cleanse_bucket_output = True
		if output_name.find('ConsumeBucketName') != -1:
			consume_bucket_output = True
		if output_name.find('S3AccessLogBucket') != -1:
			access_logs_bucket_output = True
		if output_name.find('S3KmsKeyArn') != -1:
			s3_kms_key_output = True

	assert collect_bucket_output, 'Missing CF output for collect bucket'
	assert cleanse_bucket_output, 'Missing CF output for cleanse bucket'
	assert consume_bucket_output, 'Missing CF output for consume bucket'
	assert access_logs_bucket_output, 'Missing CF output for access logs bucket'
	assert s3_kms_key_output, 'Missing CF output for s3 kms key'
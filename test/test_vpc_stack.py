# Copyright Amazon.com and its affiliates; all rights reserved. This file is Amazon Web Services Content and may not be duplicated or distributed without permission.
# SPDX-License-Identifier: MIT-0
import pytest
import aws_cdk as cdk
from aws_cdk.assertions import Template

from boto_mocking_helper import *
from lib.vpc_stack import VpcStack

import lib.configuration as configuration
from lib.configuration import (
    DEV, PROD, TEST, ACCOUNT_ID, REGION, VPC_CIDR, RESOURCE_NAME_PREFIX, LOGICAL_ID_PREFIX
)

def mock_get_local_configuration_with_vpc(environment, local_mapping = None):
    return {
        ACCOUNT_ID: mock_account_id,
        REGION: mock_region,
        VPC_CIDR: '10.0.0.0/24',
        # Mix Deploy environment variables so we can return one dict for all environments
        LOGICAL_ID_PREFIX: 'TestLake',
        RESOURCE_NAME_PREFIX: 'testlake',
    }

def test_resource_types_and_counts(monkeypatch):
    monkeypatch.setattr(configuration.boto3, 'client', mock_boto3_client)
    monkeypatch.setattr(configuration, 'get_local_configuration', mock_get_local_configuration_with_vpc)

    app = cdk.App()
    vpc_stack = VpcStack(
        app,
        'Dev-VpcStackForTests',
        target_environment=DEV,
        # Explicitly specify account and region to get 3 AZs
        env=cdk.Environment(
            account=mock_account_id,
            region=mock_region
        )
    )

    # All stacks should be generated before calling Template methods
    template = Template.from_stack(vpc_stack)

    template.resource_count_is('AWS::EC2::VPC', 1)
    template.resource_count_is('AWS::EC2::Subnet', 6)
    template.resource_count_is('AWS::EC2::RouteTable', 6)
    template.resource_count_is('AWS::EC2::SecurityGroup', 1)
    template.resource_count_is('AWS::EC2::VPCEndpoint', 7)
    template.resource_count_is('AWS::Logs::LogGroup', 1)


def test_stack_has_correct_outputs(monkeypatch):
    monkeypatch.setattr(configuration.boto3, 'client', mock_boto3_client)
    monkeypatch.setattr(configuration, 'get_local_configuration', mock_get_local_configuration_with_vpc)

    app = cdk.App()

    vpc_stack = VpcStack(
        app,
        'Dev-VpcStackForTests',
        target_environment=DEV,
        env=cdk.Environment(
            account=mock_account_id,
            region=mock_region
        )
    )

    template = Template.from_stack(vpc_stack)
    stack_outputs = template.find_outputs('*')

    vpc_availabiliity_zone_outputs = 0
    subnet_outputs = 0
    route_table_outputs = 0
    vpc_output = False
    security_group_output = False

    for output_id in stack_outputs.keys():
        output_name = stack_outputs[output_id]['Export']['Name']

        if output_name.find('AvailabilityZone') != -1:
            vpc_availabiliity_zone_outputs += 1
        if output_name.find('SubnetId') != -1:
            subnet_outputs += 1
        if output_name.find('RouteTable') != -1:
            route_table_outputs += 1
        if output_name.find('SharedSecurityGroupId') != -1:
            security_group_output = True
        if output_name.find('VpcId') != -1:
            vpc_output = True

    assert vpc_availabiliity_zone_outputs == 3, \
        'Unexpected number of CF outputs for availability zones'
    assert subnet_outputs == 3, 'Unexpected number of CF outputs for subnets'
    assert route_table_outputs == 3, 'Unexpected number of CF outputs for route tables'
    assert security_group_output, 'Unexpected number of CF outputs for security groups'
    assert vpc_output, 'Unexpected number of CF outputs for vpcs'


def test_error_when_empty_env_specified(monkeypatch):
    monkeypatch.setattr(configuration.boto3, 'client', mock_boto3_client)

    app = cdk.App()

    with pytest.raises(RuntimeError) as e_info:
        VpcStack(
            app,
            'Dev-VpcStackForTests',
            target_environment=DEV,
            # Specify empty environment to trigger error
            env=cdk.Environment()
        )

    assert e_info.match('availability zones'), \
        'Expected Runtime Error for missing environment parameters not raised'


def test_vpc_has_three_availability_zones(monkeypatch):
    monkeypatch.setattr(configuration.boto3, 'client', mock_boto3_client)
    monkeypatch.setattr(configuration, 'get_local_configuration', mock_get_local_configuration_with_vpc)

    app = cdk.App()

    vpc_stack = VpcStack(
        app,
        'Dev-VpcStackForTests',
        target_environment=DEV,
        # Explicitly specify account and region to get 3 AZs
        env=cdk.Environment(
            account=mock_account_id,
            region=mock_region
        )
    )

    assert len(vpc_stack.availability_zones) == 3, \
        'Unexpected number of availability zones in the vpc'
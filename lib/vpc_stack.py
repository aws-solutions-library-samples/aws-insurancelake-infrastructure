# Copyright Amazon.com and its affiliates; all rights reserved. This file is Amazon Web Services Content and may not be duplicated or distributed without permission.
# SPDX-License-Identifier: MIT-0
import aws_cdk as cdk
from constructs import Construct
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_logs as logs

from .configuration import (
    AVAILABILITY_ZONE_1, AVAILABILITY_ZONE_2, AVAILABILITY_ZONE_3, ROUTE_TABLE_1, ROUTE_TABLE_2, ROUTE_TABLE_3,
    SHARED_SECURITY_GROUP_ID, SUBNET_ID_1, SUBNET_ID_2, SUBNET_ID_3, VPC_CIDR, VPC_ID, PROD, TEST,
    get_environment_configuration, get_logical_id_prefix
)


class VpcStack(cdk.Stack):

    def __init__(
            self, scope: Construct, construct_id: str, 
            target_environment: str, env: cdk.Environment,
            **kwargs
        ):
        """CloudFormation stack to create VPC and related resources

        Parameters
        ----------
        scope
            Parent of this stack, usually an App or a Stage, but could be any construct
        construct_id
            The construct ID of this stack; if stackName is not explicitly defined,
            this ID (and any parent IDs) will be used to determine the physical ID of the stack
        target_environment
            The target environment for stacks in the deploy stage
        env
            AWS environment definition (account, region) to pass to stacks
        kwargs: optional
            Optional keyword arguments to pass up to parent Stack class

        Raises
        ------
        RuntimeError
            If environment settings cause less than 3 AZs to be created with the VPC
        """
        super().__init__(scope, construct_id, env=env, **kwargs)

        # Reference: https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_ec2.Vpc.html#maxazs
        if env.account is None or env.region is None:
            raise RuntimeError(f'Supplied env parameter {env} does not contain account or region; '
                'stack requires explicit account and region so that VPC is created with 3 availability '
                'zones which are expected by the ETL resource stacks (imported values)')

        self.target_environment = target_environment
        self.mappings = get_environment_configuration(target_environment)
        self.logical_id_prefix = get_logical_id_prefix()
        vpc_cidr = self.mappings[VPC_CIDR]
        if (target_environment == PROD or target_environment == TEST):
            self.removal_policy = cdk.RemovalPolicy.RETAIN
            self.log_retention = logs.RetentionDays.SIX_MONTHS
        else:
            self.removal_policy = cdk.RemovalPolicy.DESTROY
            self.log_retention = logs.RetentionDays.ONE_MONTH

        self.vpc = ec2.Vpc(
            self,
            f'{self.logical_id_prefix}Vpc',
            vpc_name=f'{target_environment}{self.logical_id_prefix}Vpc',
            ip_addresses=ec2.IpAddresses.cidr(vpc_cidr),
            max_azs=3,
        )
        if len(self.vpc.availability_zones) < 3:
            raise RuntimeError(f'Selected region {env.region} provides less than 3 availability zones '
                'for the VPC, which are expected by the ETL resource stacks (imported values)')

        cloudwatch_flow_log_group = logs.LogGroup(
            self,
            f'{target_environment}{self.logical_id_prefix}VpcFlowLogGroup',
            removal_policy=self.removal_policy,
            retention=self.log_retention,
        )
        self.vpc.add_flow_log(
            f'{target_environment}{self.logical_id_prefix}VpcFlowLog',
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(cloudwatch_flow_log_group),
            traffic_type=ec2.FlowLogTrafficType.ALL,
        )

        # Do not specifiy an explicit security group name per AWS CDK recommendation:
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/SecurityGroup.html
        self.shared_security_group = ec2.SecurityGroup(
            self,
            f'{target_environment}{self.logical_id_prefix}SharedIngressSecurityGroup',
            vpc=self.vpc,
            description='Shared Security Group for Data Lake resources with self-referencing ingress rule.',
            allow_all_outbound=True,    # Change to False to explicityly allow outbound traffic
        )
        self.shared_security_group.add_ingress_rule(
            peer=self.shared_security_group,
            connection=ec2.Port.all_traffic(),
            description='Self-referencing ingress rule',
        )

        self.add_vpc_endpoints()
        self.add_cloudformation_exports()


    def add_vpc_endpoints(self):
        """Adds VPC Gateway and Interface endpoints to VPC
        """
        for service_name in [ 'S3', 'DYNAMODB' ]:
            service = getattr(ec2.GatewayVpcEndpointAwsService, service_name)
            pascal_service_name = service_name.title().replace('_', '')
            self.vpc.add_gateway_endpoint(
                f'{self.target_environment}{self.logical_id_prefix}{pascal_service_name}Endpoint',
                service=service,
            )

        for service_name in [ 'GLUE', 'KMS', 'SSM', 'SECRETS_MANAGER', 'STEP_FUNCTIONS' ]:
            service = getattr(ec2.InterfaceVpcEndpointAwsService, service_name)
            pascal_service_name = service_name.title().replace('_', '')
            self.vpc.add_interface_endpoint(
                f'{self.target_environment}{self.logical_id_prefix}{pascal_service_name}Endpoint',
                service=service,
                security_groups=[self.shared_security_group],
            )


    def add_cloudformation_exports(self):
        """Add Cloudformation exports to VPC Stack
        These stack outputs that are programmatically synchronized. Specifically, these outputs
        are imported in the ETL stack using Fn:ImportValue, which expects the values to be
        present and the names to be unique
        """
        cdk.CfnOutput(
            self,
            f'{self.target_environment}{self.logical_id_prefix}Vpc',
            value=self.vpc.vpc_id,
            export_name=self.mappings[VPC_ID],
        )

        for az_number in range(3):
            az_mapping_element = globals()[f'AVAILABILITY_ZONE_{az_number + 1}']
            az_value = self.vpc.availability_zones[az_number]
            cdk.CfnOutput(
                self,
                f'{self.target_environment}{self.logical_id_prefix}VpcAvailabilityZone{az_number + 1}',
                value=az_value,
                export_name=self.mappings[az_mapping_element],
            )

        for subnet_number in range(3):
            subnet_mapping_element = globals()[f'SUBNET_ID_{subnet_number + 1}']
            subnet_value = self.vpc.private_subnets[subnet_number].subnet_id
            cdk.CfnOutput(
                self,
                f'{self.target_environment}{self.logical_id_prefix}VpcPrivateSubnet{subnet_number + 1}',
                value=subnet_value,
                export_name=self.mappings[subnet_mapping_element],
            )

        for rt_number in range(3):
            rt_mapping_element = globals()[f'ROUTE_TABLE_{rt_number + 1}']
            rt_value = self.vpc.private_subnets[rt_number].route_table.route_table_id
            cdk.CfnOutput(
                self,
                f'{self.target_environment}{self.logical_id_prefix}VpcRouteTable{rt_number + 1}',
                value=rt_value,
                export_name=self.mappings[rt_mapping_element],
            )

        cdk.CfnOutput(
            self,
            f'{self.target_environment}{self.logical_id_prefix}SharedSecurityGroup',
            value=self.shared_security_group.security_group_id,
            export_name=self.mappings[SHARED_SECURITY_GROUP_ID]
        )
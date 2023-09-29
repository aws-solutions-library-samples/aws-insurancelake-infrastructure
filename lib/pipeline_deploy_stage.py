# Copyright Amazon.com and its affiliates; all rights reserved. This file is Amazon Web Services Content and may not be duplicated or distributed without permission.
# SPDX-License-Identifier: MIT-0
import aws_cdk as cdk
from constructs import Construct
from .vpc_stack import VpcStack
from .s3_bucket_zones_stack import S3BucketZonesStack
from .tagging import tag
from .configuration import VPC_CIDR, get_environment_configuration, get_logical_id_prefix

class PipelineDeployStage(cdk.Stage):
    def __init__(
        self, scope: Construct, construct_id: str,
        target_environment: str, deployment_account_id: str, env: cdk.Environment,
        **kwargs
    ):
        """Adds deploy stage to CodePipeline

        Parameters
        ----------
        scope
            Parent of this stack, usually an App or a Stage, but could be any construct
        construct_id
            The construct ID of this stack; if stackName is not explicitly defined,
            this ID (and any parent IDs) will be used to determine the physical ID of the stack
        target_environment
            The target environment for stacks in the deploy stage
        deployment_account_id
            Account ID of the deployment account (in case it is different)
        env
            AWS environment definition (account, region) to pass to stacks
        kwargs: optional
            Optional keyword arguments
        """
        super().__init__(scope, construct_id, **kwargs)

        mappings = get_environment_configuration(target_environment)
        logical_id_prefix = get_logical_id_prefix()

        if VPC_CIDR in mappings:
            vpc_stack = VpcStack(
                self,
                f'{logical_id_prefix}InfrastructureVpc',
                description='InsuranceLake stack for networking resources (uksb-1tu7mtee2)',
                target_environment=target_environment,
                env=env,
                **kwargs,
            )
            tag(vpc_stack, target_environment)

        bucket_stack = S3BucketZonesStack(
            self,
            f'{logical_id_prefix}InfrastructureS3BucketZones',
            description='InsuranceLake stack for three S3 buckets used to store data (uksb-1tu7mtee2)',
            target_environment=target_environment,
            deployment_account_id=deployment_account_id,
            env=env,
            **kwargs,
        )
        tag(bucket_stack, target_environment)
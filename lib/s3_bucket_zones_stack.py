# Copyright Amazon.com and its affiliates; all rights reserved. This file is Amazon Web Services Content and may not be duplicated or distributed without permission.
# SPDX-License-Identifier: MIT-0
import aws_cdk as cdk
from constructs import Construct
import aws_cdk.aws_iam as iam
import aws_cdk.aws_kms as kms
import aws_cdk.aws_s3 as s3

from .configuration import (
    PROD, S3_ACCESS_LOG_BUCKET, S3_CONFORMED_BUCKET, S3_KMS_KEY, S3_PURPOSE_BUILT_BUCKET, S3_RAW_BUCKET, TEST,
    get_environment_configuration, get_logical_id_prefix, get_resource_name_prefix,
)


class S3BucketZonesStack(cdk.Stack):
    def __init__(
        self, scope: Construct, construct_id: str,
        target_environment: str, deployment_account_id: str,
        **kwargs
    ):
        """CloudFormation stack to create AWS KMS Key, Amazon S3 buckets, and bucket policies.

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
            The AWS account ID for the deployment account
        kwargs: optional
            Optional keyword arguments to pass up to parent Stack class
        """
        super().__init__(scope, construct_id, **kwargs)

        self.target_environment = target_environment
        mappings = get_environment_configuration(target_environment)
        logical_id_prefix = get_logical_id_prefix()
        resource_name_prefix = get_resource_name_prefix()
        if (target_environment == PROD or target_environment == TEST):
            self.removal_policy = cdk.RemovalPolicy.RETAIN
        else:
            self.removal_policy = cdk.RemovalPolicy.DESTROY

        s3_kms_key = self.create_kms_key(
            deployment_account_id,
            logical_id_prefix,
            resource_name_prefix,
        )
        access_logs_bucket = self.create_access_logs_bucket(
            f'{target_environment}{logical_id_prefix}AccessLogsBucket',
            f'{target_environment.lower()}-{resource_name_prefix}-{self.account}-{self.region}-access-logs',
        )
        collect_bucket = self.create_data_lake_bucket(
            f'{target_environment}{logical_id_prefix}CollectBucket',
            f'{target_environment.lower()}-{resource_name_prefix}-{self.account}-{self.region}-collect',
            access_logs_bucket,
            s3_kms_key,
        )
        cleanse_bucket = self.create_data_lake_bucket(
            f'{target_environment}{logical_id_prefix}CleanseBucket',
            f'{target_environment.lower()}-{resource_name_prefix}-{self.account}-{self.region}-cleanse',
            access_logs_bucket,
            s3_kms_key,
        )
        consume_bucket = self.create_data_lake_bucket(
            f'{target_environment}{logical_id_prefix}ConsumeBucket',
            f'{target_environment.lower()}-{resource_name_prefix}-{self.account}-{self.region}-consume',
            access_logs_bucket,
            s3_kms_key,
        )

        # Stack Outputs that are programmatically synchronized
        # Specifically, these outputs are imported in the ETL stack using Fn:ImportValue,
        # which expects the values to be present

        cdk.CfnOutput(
            self,
            f'{target_environment}{logical_id_prefix}KmsKeyArn',
            value=s3_kms_key.key_arn,
            export_name=mappings[S3_KMS_KEY]
        )
        cdk.CfnOutput(
            self,
            f'{target_environment}{logical_id_prefix}AccessLogsBucketName',
            value=access_logs_bucket.bucket_name,
            export_name=mappings[S3_ACCESS_LOG_BUCKET]
        )
        cdk.CfnOutput(
            self,
            f'{target_environment}{logical_id_prefix}CollectBucketName',
            value=collect_bucket.bucket_name,
            export_name=mappings[S3_RAW_BUCKET]
        )
        cdk.CfnOutput(
            self,
            f'{target_environment}{logical_id_prefix}CleanseBucketName',
            value=cleanse_bucket.bucket_name,
            export_name=mappings[S3_CONFORMED_BUCKET]
        )
        cdk.CfnOutput(
            self,
            f'{target_environment}{logical_id_prefix}ConsumeBucketName',
            value=consume_bucket.bucket_name,
            export_name=mappings[S3_PURPOSE_BUILT_BUCKET]
        )

    def create_kms_key(
        self,
        deployment_account_id: str,
        logical_id_prefix: str,
        resource_name_prefix: str
    ) -> kms.Key:
        """Creates an AWS KMS Key and attaches a Key policy

        Parameters
        ----------
        deployment_account_id
            Account ID of the deployment account (in case it is different)
        logical_id_prefix
            The logical ID prefix to apply to the key
        resource_name_prefix
            The resource name prefix to apply to the key alias

        Returns
        -------
        kms.Key
            Created KMS key construct
        """
        s3_kms_key = kms.Key(
            self,
            f'{self.target_environment}{logical_id_prefix}KmsKey',
            # Gives account users admin access to the key
            admins=[iam.AccountPrincipal(self.account)],
            description='Key used for encrypting InsuranceLake S3 Buckets, DynamoDB Tables, SNS Topics, Glue Job resources',
            removal_policy=self.removal_policy,
            enable_key_rotation=True,
            pending_window=cdk.Duration.days(30),
            alias=f'{self.target_environment.lower()}-{resource_name_prefix}-kms-key',
        )
        # Gives account users and deployment account users access to use the key
        # for deploying and changing S3 buckets
        s3_kms_key.add_to_resource_policy(
            iam.PolicyStatement(
                sid='DeploymentAndEnvUserKeyAccess',
                principals=[
                    iam.AccountPrincipal(self.account),
                    iam.AccountPrincipal(deployment_account_id),
                ],
                actions=[
                    'kms:Encrypt',
                    'kms:Decrypt',
                    'kms:ReEncrypt*',
                    'kms:GenerateDataKey*',
                    'kms:DescribeKey',
                ],
                resources=["*"],
            )
        )
        # SNS Topic will be created in the ETL stack and used for encryption
        # KMS Grant policy allows subscribers to read encrypted events
        # TODO: Consider a separate key for the ETL stack encryption
        s3_kms_key.add_to_resource_policy(
            iam.PolicyStatement(
                sid='SNSEncryptedTopicKeyAccess',
                principals=[
                    iam.ServicePrincipal('sns.amazonaws.com'),
                ],
                actions=[
                    'kms:Decrypt',
                    'kms:GenerateDataKey*'
                ],
                resources=['*'],
            )
        )
        # KMS Grant policy allows log readers to read encrypted logs
        s3_kms_key.add_to_resource_policy(
            iam.PolicyStatement(
                sid='LogsEncryptedLogsKeyAccess',
                principals=[
                    iam.ServicePrincipal('logs.amazonaws.com'),
                ],
                actions=[
                    'kms:Decrypt',
                    'kms:GenerateDataKey*'
                ],
                resources=['*'],
            )
        )
        return s3_kms_key

    def create_data_lake_bucket(
        self,
        logical_id: str,
        bucket_name: str,
        access_logs_bucket: s3.Bucket,
        s3_kms_key: kms.Key
    ) -> s3.Bucket:
        """Creates an Amazon S3 bucket and attaches bucket policy with necessary guardrails.
        It enables server-side encryption using provided KMS key and leverage S3 bucket key feature.

        logical_id
            The logical id to apply to the bucket
        bucket_name
            The name for the bucket resource
        access_logs_bucket
            The S3 bucket resource to target for Access Logging
        s3_kms_key
            The KMS Key to use for encryption of data at rest

        Returns
        -------
        s3.Bucket
            The bucket resource that was created
        """
        lifecycle_rules = [
            s3.LifecycleRule(
                enabled=True,
                expiration=cdk.Duration.days(60),
                noncurrent_version_expiration=cdk.Duration.days(30),
            )
        ]
        if self.target_environment == PROD:
            lifecycle_rules = [
                s3.LifecycleRule(
                    enabled=True,
                    expiration=cdk.Duration.days(2555),
                    noncurrent_version_expiration=cdk.Duration.days(90),
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=cdk.Duration.days(365),
                        )
                    ]
                )
            ]
        bucket = s3.Bucket(
            self,
            id=logical_id,
            access_control=s3.BucketAccessControl.PRIVATE,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            bucket_key_enabled=True,
            bucket_name=bucket_name,
            encryption=s3.BucketEncryption.KMS,
            encryption_key=s3_kms_key,
            lifecycle_rules=lifecycle_rules,
            public_read_access=False,
            removal_policy=self.removal_policy,
            versioned=True,
            object_ownership=s3.ObjectOwnership.OBJECT_WRITER,
            server_access_logs_bucket=access_logs_bucket,
            server_access_logs_prefix=f'{bucket_name}-',
        )
        policy_document_statements = [
            iam.PolicyStatement(
                sid='OnlyAllowSecureTransport',
                effect=iam.Effect.DENY,
                principals=[iam.AnyPrincipal()],
                actions=[
                    's3:GetObject',
                    's3:PutObject',
                ],
                resources=[f'{bucket.bucket_arn}/*'],
                conditions={'Bool': {'aws:SecureTransport': 'false'}}
            )
        ]
        # Prevents user deletion of buckets
        if self.target_environment == PROD or self.target_environment == TEST:
            policy_document_statements.append(
                iam.PolicyStatement(
                    sid='BlockUserDeletionOfBucket',
                    effect=iam.Effect.DENY,
                    principals=[iam.AnyPrincipal()],
                    actions=[
                        's3:DeleteBucket',
                    ],
                    resources=[bucket.bucket_arn],
                    conditions={'StringLike': {'aws:userId': f'arn:aws:iam::{self.account}:user/*'}}
                )
            )
        for statement in policy_document_statements:
            bucket.add_to_resource_policy(statement)

        return bucket

    def create_access_logs_bucket(self, logical_id: str, bucket_name: str) -> s3.Bucket:
        """Creates an Amazon S3 bucket to store S3 server access logs. It attaches bucket policy
        with necessary guardrails. It enables server-side encryption using provided KMS key and
        leverage S3 bucket key feature.

        logical_id
            The logical id to apply to the bucket
        bucket_name
            The name for the bucket resource
        s3_kms_key
            The KMS Key to use for encryption of data at rest

        Returns
        -------
        s3.Bucket
            The bucket resource that was created
        """
        access_logs_intelligent_tiering = s3.IntelligentTieringConfiguration(
            name='ServerAccessLogsDeepArchiveConfiguration',
            archive_access_tier_time=cdk.Duration.days(90),
            deep_archive_access_tier_time=cdk.Duration.days(180),
        )

        access_logs_bucket = s3.Bucket(
            self,
            id=logical_id,
            access_control=s3.BucketAccessControl.LOG_DELIVERY_WRITE,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            bucket_name=bucket_name,
            # Server access log buckets only support S3-managed keys
            # for default bucket encryption
            encryption=s3.BucketEncryption.S3_MANAGED,
            public_read_access=False,
            removal_policy=self.removal_policy,
            versioned=True,
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_PREFERRED,
            intelligent_tiering_configurations=[
                access_logs_intelligent_tiering
            ],
        )

        return access_logs_bucket
<!--
  Title: AWS InsuranceLake
  Description: Serverless data lake solution accelerator and reference architecture fit for the insurance industry built on AWS
  Author: cvisi@amazon.com
  -->
# InsuranceLake Infrastructure

The InsuranceLake solution is comprised of two codebases: [Infrastructure](https://github.com/aws-samples/aws-insurancelake-infrastructure) and [ETL](https://github.com/aws-samples/aws-insurancelake-etl). This codebase and the documentation that follows is specific to the Infrastructure. For more comprehensive documentation, including several ways to get started quickly, refer to the [InsuranceLake ETL with CDK Pipeline README](https://github.com/aws-samples/aws-insurancelake-etl/blob/main/README.md).

This solution helps you deploy ETL processes and data storage resources to create an InsuranceLake. It uses Amazon S3 buckets for storage, [AWS Glue](https://docs.aws.amazon.com/glue/) for data transformation, and [AWS CDK Pipelines](https://docs.aws.amazon.com/cdk/latest/guide/cdk_pipeline.html). The solution is originally based on the AWS blog [Deploy data lake ETL jobs using CDK Pipelines](https://aws.amazon.com/blogs/devops/deploying-data-lake-etl-jobs-using-cdk-pipelines/).

[CDK Pipelines](https://docs.aws.amazon.com/cdk/api/latest/docs/pipelines-readme.html) is a construct library module for painless continuous delivery of CDK applications. CDK stands for Cloud Development Kit. It is an open source software development framework to define your cloud application resources using familiar programming languages.

Specifically, this solution helps you to:

1. Deploy a 3 Cs (Collect, Cleanse, Consume) InsuranceLake
1. Deploy ETL jobs needed make common insurance industry data souces available in a data lake
1. Use pySpark Glue jobs and supporting resoures to perform data transforms in a modular approach
1. Build and replicate the application in multiple environments quickly
1. Deploy ETL jobs from a central deployment account to multiple AWS environments such as Dev, Test, and Prod
1. Leverage the benefit of self-mutating feature of CDK Pipelines; specifically, the pipeline itself is infrastructure as code and can be changed as part of the deployment
1. Increase the speed of prototyping, testing, and deployment of new ETL jobs

![InsuranceLake High Level Architecture](./resources/insurancelake-highlevel-architecture.png)

---

## Contents

* [Architecture](#architecture)
  * [InsuranceLake](#insurance-lake)
  * [Infrastructure](#infrastructure)
* [Codebase](#codebase)
  * [Source code Structure](#source-code-structure)
  * [Automation Scripts](#automation-scripts)
* [Authors and Reviewers](#authors-and-reviewers)
* [License Summary](#license-summary)

---

## Architecture

In this section we talk about the overall InsuranceLake architecture and the infrastructure component.

### InsuranceLake

As shown in the figure below, we use Amazon S3 for storage. We use three S3 buckets:
   1. Collect bucket to store raw data in its original format
   1. Cleanse/Curate bucket to store the data that meets the quality and consistency requirements of the lake
   1. Consume bucket for data that is used by analysts and data consumers of the lake (e.g. Amazon Quicksight, Amazon Sagemaker)

InsuranceLake is designed to support a number of source systems with different file formats and data partitions. To demonstrate, we have provided a CSV parser and sample data files for a source system with two data tables, which are uploaded to the Collect bucket.

We use AWS Lambda and AWS Step Functions for orchestration and scheduling of ETL workloads. We then use AWS Glue with pySpark for ETL and data cataloging, Amazon DynamoDB for transformation persistence, Amazon Athena for interactive queries and analysis. We use various AWS services for logging, monitoring, security, authentication, authorization, notification, build, and deployment.

**Note:** [AWS Lake Formation](https://aws.amazon.com/lake-formation/) is a service that makes it easy to set up a secure data lake in days. [Amazon QuickSight](https://aws.amazon.com/quicksight/) is a scalable, serverless, embeddable, machine learning-powered business intelligence (BI) service built for the cloud. These two services are not used in this solution but can be added.

![Conceptual Data Lake](./resources/Aws-cdk-insurancelake-data_lake.png)

---

### Infrastructure

The figure below represents the infrastructure resources we provision for Data Lake.

 1. Amazon Virtual Private Cloud (VPC)
 1. Subnets
 1. Security Groups
 1. Route Table(s)
 1. VPC Endpoints
 1. Amazon S3 buckets for:
    1. Collect data
    1. Cleanse/Curate data
    1. Consume data

![Data Lake Infrastructure Architecture](./resources/Aws-cdk-insurancelake-infra.png)

---

## Codebase

### Source Code Structure

Table below explains how this source code structured:

  | File / Folder    | Description  |
  |------------------| -------------|
  | [app.py](./app.py) | Application entry point. |
  | [code_commit_stack.py](./lib/code_commit_stack.py) | Optional stack to deploy an empty CodeCommit respository for mirroring. |
  | [pipeline_stack.py](./lib/pipeline_stack.py) | Pipeline stack entry point. |
  | [pipeline_deploy_stage.py](./lib/pipeline_deploy_stage.py) | Pipeline deploy stage entry point. |
  | [s3_bucket_zones_stack.py](./lib/s3_bucket_zones_stack.py) | Stack creates S3 buckets - raw, conformed, and purpose-built. This also creates an S3 bucket for server access logging and AWS KMS Key to enabled server side encryption for all buckets.|
  | [tagging.py](./lib/tagging.py) | Program to tag all provisioned resources. |
  | [vpc_stack.py](./lib/vpc_stack.py) | Contains all resources related to the VPC used by Data Lake infrastructure and services. This includes: VPC, Security Groups, and VPC Endpoints (both Gateway and Interface types). |
  | [test](./test)| This folder contains pytest unit tests |
  | [resources](./resources)| This folder has static resources such as architecture diagrams. |

---

### Automation scripts

This repository has the following automation scripts to complete steps before the deployment:

  | Script    | Purpose  |
  |-----------| -------------|
  | [bootstrap_deployment_account.sh](./lib/prerequisites/bootstrap_deployment_account.sh) | Used to bootstrap deployment account |
  | [bootstrap_target_account.sh](./lib/prerequisites/bootstrap_target_account.sh) | Used to bootstrap target environments for example dev, test, and production. |
  | [configure_account_secrets.py](./lib/prerequisites/configure_account_secrets.py) | Used to configure account secrets for GitHub access token. |

---

## Authors and Reviewers

The following people are involved in the design, architecture, development, testing, and review of this solution:

1. **Cory Visi**, Senior Solutions Architect, Amazon Web Services
1. **Ratnadeep Bardhan Roy**, Senior Solutions Architect, Amazon Web Services
1. **Isaiah Grant**, Cloud Consultant, 2nd Watch, Inc.
1. **Muhammad Zahid Ali**, Data Architect, Amazon Web Services
1. **Ravi Itha**, Senior Data Architect, Amazon Web Services
1. **Justiono Putro**, Cloud Infrastructure Architect, Amazon Web Services
1. **Mike Apted**, Principal Solutions Architect, Amazon Web Services
1. **Nikunj Vaidya**, Senior DevOps Specialist, Amazon Web Services

---

## License Summary

This sample code is made available under the MIT-0 license. See the LICENSE file.

Copyright Amazon.com and its affiliates; all rights reserved. This file is Amazon Web Services Content and may not be duplicated or distributed without permission.
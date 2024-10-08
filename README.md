<!--
  Title: AWS InsuranceLake
  Description: Serverless modern data lake solution and reference architecture fit for the insurance industry built on AWS
  Author: cvisi@amazon.com
  -->
# InsuranceLake Infrastructure

## Overview

This solution guidance helps you deploy extract, transform, load (ETL) processes and data storage resources to create InsuranceLake. It uses Amazon Simple Storage Service (Amazon S3) buckets for storage, [AWS Glue](https://docs.aws.amazon.com/glue/) for data transformation, and [AWS Cloud Development Kit (CDK) Pipelines](https://docs.aws.amazon.com/cdk/latest/guide/cdk_pipeline.html). The solution is originally based on the AWS blog [Deploy data lake ETL jobs using CDK Pipelines](https://aws.amazon.com/blogs/devops/deploying-data-lake-etl-jobs-using-cdk-pipelines/).

The best way to learn about InsuranceLake is to follow the [Quickstart guide](https://aws-solutions-library-samples.github.io/aws-insurancelake-etl/quickstart/) and try it out.

The InsuranceLake solution is comprised of two codebases: [Infrastructure](https://github.com/aws-solutions-library-samples/aws-insurancelake-infrastructure) and [ETL](https://github.com/aws-solutions-library-samples/aws-insurancelake-etl).

Specifically, this solution helps you to:

* Deploy a "3 Cs" (Collect, Cleanse, Consume) architecture InsuranceLake.
* Deploy ETL jobs needed to make common insurance industry data souces available in a data lake.
* Use pySpark Glue jobs and supporting resoures to perform data transforms in a modular approach.
* Build and replicate the application in multiple environments quickly.
* Deploy ETL jobs from a central deployment account to multiple AWS environments such as Dev, Test, and Prod.
* Leverage the benefit of self-mutating feature of CDK Pipelines; specifically, the pipeline itself is infrastructure as code and can be changed as part of the deployment.
* Increase the speed of prototyping, testing, and deployment of new ETL jobs.

![InsuranceLake High Level Architecture](https://raw.githubusercontent.com/aws-solutions-library-samples/aws-insurancelake-infrastructure/main/resources/insurancelake-highlevel-architecture.png)

---

## Contents

* [Architecture](#architecture)
    * [Collect, Cleanse, Consume](#collect-cleanse-consume)
    * [Infrastructure](#infrastructure)
* [Codebase](#codebase)
    * [Source code Structure](#source-code-structure)
    * [Automation Scripts](#automation-scripts)
    * [Authors and Reviewers](#authors-and-reviewers)
* [License Summary](#license-summary)

---

## Architecture

This section explains the overall InsuranceLake architecture and the components of the infrastructure.

### Collect, Cleanse, Consume

As shown in the figure below, we use S3 for storage, specifically three different S3 buckets:
1. Collect bucket to store raw data in its original format.
1. Cleanse/Curate bucket to store the data that meets the quality and consistency requirements for the data source.
1. Consume bucket for data that is used by analysts and data consumers (for example, Amazon Quicksight, Amazon Sagemaker).

InsuranceLake is designed to support a number of source systems with different file formats and data partitions. To demonstrate, we have provided a CSV parser and sample data files for a source system with two data tables, which are uploaded to the Collect bucket.

We use AWS Lambda and AWS Step Functions for orchestration and scheduling of ETL workloads. We then use AWS Glue with PySpark for ETL and data cataloging, Amazon DynamoDB for transformation persistence, Amazon Athena for interactive queries and analysis. We use various AWS services for logging, monitoring, security, authentication, authorization, notification, build, and deployment.

**Note:** [AWS Lake Formation](https://aws.amazon.com/lake-formation/) is a service that makes it easy to set up a secure data lake in days. [Amazon QuickSight](https://aws.amazon.com/quicksight/) is a scalable, serverless, embeddable, machine learning-powered business intelligence (BI) service built for the cloud. [Amazon DataZone](https://aws.amazon.com/datazone/) is a data management service that makes it faster and easier for customers to catalog, discover, share, and govern data stored across AWS, on premises, and third-party sources. These three services are not used in this solution but can be added.

![Conceptual Data Lake](https://raw.githubusercontent.com/aws-solutions-library-samples/aws-insurancelake-infrastructure/main/resources/Aws-cdk-insurancelake-data_lake.png)

---

### Infrastructure

The figure below represents the infrastructure resources we provision for the data lake.

![InsuranceLake Infrastructure Architecture](https://raw.githubusercontent.com/aws-solutions-library-samples/aws-insurancelake-infrastructure/main/resources/Aws-cdk-insurancelake-infra.png)

* S3 buckets for:
    * Collected (raw) data
    * Cleansed and Curated data
    * Consume-ready (prepared) data
    * Server access logging
* Optional Amazon Virtual Private Cloud (Amazon VPC)
    * Subnets
    * Security groups
    * Route table(s)
    * Amazon VPC endpoints
* Supporting services, such as AWS Key Management Service (KMS)

---

## Codebase

### Source Code Structure

The table below explains how this source code is structured.

| File / Folder    | Description
|------------------| -------------
| [app.py](https://github.com/aws-solutions-library-samples/aws-insurancelake-infrastructure/blob/main/app.py) | Application entry point 
| [code_commit_stack.py](https://github.com/aws-solutions-library-samples/aws-insurancelake-infrastructure/blob/main/lib/code_commit_stack.py) | Optional stack to deploy an empty CodeCommit respository for mirroring
| [pipeline_stack.py](https://github.com/aws-solutions-library-samples/aws-insurancelake-infrastructure/blob/main/lib/pipeline_stack.py) | CodePipeline stack entry point
| [pipeline_deploy_stage.py](https://github.com/aws-solutions-library-samples/aws-insurancelake-infrastructure/blob/main/lib/pipeline_deploy_stage.py) | CodePipeline deploy stage entry point
| [s3_bucket_zones_stack.py](https://github.com/aws-solutions-library-samples/aws-insurancelake-infrastructure/blob/main/lib/s3_bucket_zones_stack.py) | Stack to create three S3 buckets (Collect, Cleanse, and Consume), supporting S3 bucket for server access logging, and KMS Key to enable server side encryption for all buckets
| [vpc_stack.py](https://github.com/aws-solutions-library-samples/aws-insurancelake-infrastructure/blob/main/lib/vpc_stack.py) | Stack to create all resources related to Amazon VPC, including virtual private clouds across multiple availability zones (AZs), security groups, and Amazon VPC endpoints
| [test](https://github.com/aws-solutions-library-samples/aws-insurancelake-infrastructure/blob/main/test)| This folder contains pytest unit tests
| [resources](https://github.com/aws-solutions-library-samples/aws-insurancelake-infrastructure/blob/main/resources)| This folder has static resources such as architecture diagrams

---

### Automation scripts

The table below lists the automation scripts to complete steps before the deployment.

| Script    | Purpose
|-----------| -------------
| [bootstrap_deployment_account.sh](https://github.com/aws-solutions-library-samples/aws-insurancelake-infrastructure/blob/main/lib/prerequisites/bootstrap_deployment_account.sh) | Used to bootstrap deployment account
| [bootstrap_target_account.sh](https://github.com/aws-solutions-library-samples/aws-insurancelake-infrastructure/blob/main/lib/prerequisites/bootstrap_target_account.sh) | Used to bootstrap target environments for example dev, test, and production
| [configure_account_secrets.py](https://github.com/aws-solutions-library-samples/aws-insurancelake-infrastructure/blob/main/lib/prerequisites/configure_account_secrets.py) | Used to configure account secrets for GitHub access token

---

## Authors

The following people are involved in the design, architecture, development, testing, and review of this solution:

* **Cory Visi**, Senior Solutions Architect, Amazon Web Services
* **Ratnadeep Bardhan Roy**, Senior Solutions Architect, Amazon Web Services
* **Jose Guay**, Enterprise Support, Amazon Web Services
* **Isaiah Grant**, Cloud Consultant, 2nd Watch, Inc.
* **Muhammad Zahid Ali**, Data Architect, Amazon Web Services
* **Ravi Itha**, Senior Data Architect, Amazon Web Services
* **Justiono Putro**, Cloud Infrastructure Architect, Amazon Web Services
* **Mike Apted**, Principal Solutions Architect, Amazon Web Services
* **Nikunj Vaidya**, Senior DevOps Specialist, Amazon Web Services

---

## License Summary

This sample code is made available under the MIT-0 license. See the LICENSE file.

Copyright Amazon.com and its affiliates; all rights reserved. This file is Amazon Web Services Content and may not be duplicated or distributed without permission.
# Copyright Amazon.com and its affiliates; all rights reserved. This file is Amazon Web Services Content and may not be duplicated or distributed without permission.
# SPDX-License-Identifier: MIT-0
import setuptools

with open('README.md', encoding='utf-8') as fp:
    long_description = fp.read()

setuptools.setup(
    name='aws-insurancelake-infrastructure',
    version='4.0.3',
    description='A CDK Python app for deploying foundational infrastructure for InsuranceLake in AWS',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/aws-samples/aws-insurancelake-infrastructure',
    author='Cory Visi <cvisi@amazon.com>, Ratnadeep Bardhan Roy <rdbroy@amazon.com>, Isaiah Grant <igrant@2ndwatch.com>, Ravi Itha <itharav@amazon.com>, Zahid Muhammad Ali <zhidli@amazon.com>',
    packages=setuptools.find_packages(),
    install_requires=[
        'aws-cdk-lib>=2.80.0',
        'constructs>=10.1.0',
    ],
    python_requires='>=3.9',
    keywords='aws-insurancelake-infrastructure aws cdk insurance datalake s3 vpc python',
    license='MIT-0',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: JavaScript',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Utilities',
        'Typing :: Typed',
    ],
)
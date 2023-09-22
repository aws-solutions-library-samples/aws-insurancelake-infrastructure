# Copyright Amazon.com and its affiliates; all rights reserved. This file is Amazon Web Services Content and may not be duplicated or distributed without permission.
# SPDX-License-Identifier: MIT-0
mock_account_id = 'notrealaccountid'
mock_region = 'us-east-1'

class mock_client_sts():

	@staticmethod
	def get_caller_identity():
		return { 'Account': mock_account_id }

def mock_boto3_client(client: str):
	if client == 'sts':
		return mock_client_sts
	else:
		raise RuntimeError(f'boto3 client {client} requested from mock but not implemented')
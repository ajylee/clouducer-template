import json
from itertools import chain
from uuid import UUID
from pathlib import Path
from typing import Dict
import logging

import boto3

import zsec_aws_tools as zaws
import zsec_aws_tools.aws_lambda as zaws_lambda
import zsec_aws_tools.sqs as zaws_sqs
import zsec_aws_tools.iam as zaws_iam
import zsec_aws_tools.dynamodb as zaws_dynamodb
import zsec_aws_tools.s3
import zsec_aws_tools.basic
from zsec_aws_tools_extensions import (
    PartialAWSResourceCollection,
    partial_resources,
    zip_string,
    PartialResource,
)
from zsec_aws_tools.basic import AWSResource
from zsec_aws_tools_extensions.ui import handle_cli_command
from zsec_aws_tools_extensions.deployment import MixedLambdaDynamoResourceRecorder

# WARNING: Make sure you change the manager when forking this template.
manager = "clouducer-template"  # recommended to use the full git project url

deployment_vars = json.loads(Path("deployment_vars.json").read_text())
recording_account = deployment_vars.get("recording_account")

profile = deployment_vars["profile"]

resources = PartialAWSResourceCollection()

table = resources.new_partial_resource(
    name="example_table",
    type_=zaws_dynamodb.Table,
    # WARNING Make sure you generate a new UUID when forking this template.
    # It is best to use lower case for convenient grepping.
    ztid=UUID("e0b30555-f1b3-4f3b-96bb-a381f4e32c55"),
    config=dict(
        AttributeDefinitions=[
            dict(AttributeName="arn", AttributeType="S"),
            dict(AttributeName="exception_type", AttributeType="S"),
        ],
        KeySchema=[
            dict(AttributeName="arn", KeyType="HASH"),
            dict(AttributeName="exception_type", KeyType="RANGE"),
        ],
        ProvisionedThroughput=dict(ReadCapacityUnits=5, WriteCapacityUnits=5,),
    ),
)

lambda_role = resources.new_partial_resource(
    type_=zaws_iam.Role,
    region_name="us-east-1",
    name="example-lambda-role",
    # WARNING Make sure you generate a new UUID when forking this template.
    # It is best to use lower case for convenient grepping.
    ztid=UUID("de41e513-99d8-43f9-a337-a94f05b4b98a"),
    config=dict(
        Path="/clouducer_test/",
        AssumeRolePolicyDocument=zaws_lambda.default_assume_role_policy_document_for_lambda,
        Policies=[
            # "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
            "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess",
            # "arn:aws:iam::aws:policy/AmazonSQSFullAccess",
        ],
        InlinePolicies=[
            dict(
                PolicyName="AllowDynamoDBAndSQSAccess",
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Sid": "PolicyStatementDynamoDB01",
                            "Action": [
                                "dynamodb:PutItem",
                                "dynamodb:UpdateItem",
                                "dynamodb:Query",
                                "dynamodb:Scan",
                                "dynamodb:DeleteItem",
                            ],
                            "Effect": "Allow",
                            "Resource": [table.partial_attribute("arn"),],
                        },
                        {
                            "Sid": "PolicyStatementSQS01",
                            "Action": "sqs:*",
                            "Resource": "*",
                            "Effect": "Allow",
                        },
                        {
                            "Sid": "PolicyStatementLambda01",
                            "Action": ["lambda:InvokeFunction", "lambda:GetFunction"],
                            "Resource": "*",
                            "Effect": "Allow",
                        },
                    ],
                },
            )
        ],
    ),
)

lambda_name = "example_lambda"

if 1:
    example_lambda = resources.new_partial_resource(
        name=lambda_name,
        type_=zaws_lambda.FunctionResource,
        ztid=UUID("71c7029f-b420-428a-8e53-05c53222c731"),
        config=dict(
            Runtime="python3.8",
            Role=lambda_role,
            Handler="main.lambda_handler",
            Code={
                "ZipFile": zip_string(
                    Path(f"../lambda_code/{lambda_name}.py").read_text()
                )
            },
            Timeout=60 * 10,
            Environment={"Variables": {"example_var_key": "example_var_value"}},
            Permissions=lambda self: [],
        ),
    )


def main():
    target_session = boto3.Session(profile_name=profile)

    # "complete" means to fill in the session, region_name, and manager. Partial resources can be reused
    # in to multiple regions and sessions.
    # If you want to deploy to multiple regions and accounts, you can loop over them here.
    completed_resources = resources.complete(
        session=target_session, region_name="us-east-1", manager=manager,
    )

    if recording_account:
        put_resource_record = zaws_lambda.FunctionResource(
            name="PutResourceRecordLambda",
            session=boto3.Session(profile_name=recording_account),
            region_name="us-east-1",
        )

        resources_by_zrn_table = (
            boto3.Session(profile_name=recording_account)
            .resource("dynamodb", region_name="us-east-1")
            .Table("resources_by_zrn")
        )

        recorder = MixedLambdaDynamoResourceRecorder(
            put_resource_record_lambda=put_resource_record,
            resources_by_zrn_table=resources_by_zrn_table,
            session_source=session_source,
        )
    else:
        recorder = None

    # call with --help for info.
    # takes "apply" and "destroy" verbs.
    handle_cli_command(
        manager,
        completed_resources,
        support_gc=True,
        gc_scope={
            "account_number": zsec_aws_tools.get_account_id(target_session),
            "manager": manager,
        },
        recorder=recorder,
    )


if __name__ == "__main__":
    main()

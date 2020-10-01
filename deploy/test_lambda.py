from zsec_aws_tools.aws_lambda import FunctionResource
import boto3
from main import example_lambda, resources, profile


completed_resources = resources.complete(session=boto3.Session(profile_name=profile))
completed_lambda: FunctionResource = completed_resources[example_lambda.ztid]

print(completed_lambda.invoke(json_codec=True))

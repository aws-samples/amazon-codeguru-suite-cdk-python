#!/usr/bin/env python3
import aws_cdk as cdk
from aws_cdk import Aspects
from cdk_nag import AwsSolutionsChecks

from codeguru_profiler_cdk_python_app.codeguru_profiler_cdk_python_stack import CodeguruProfilerCdkPythonAppStack


app = cdk.App()
CodeguruProfilerCdkPythonAppStack(app, "CodeguruProfilerCdkPythonAppStack",)

# Add AWS Solutions Checks to the entire app
Aspects.of(app).add(AwsSolutionsChecks())

app.synth()

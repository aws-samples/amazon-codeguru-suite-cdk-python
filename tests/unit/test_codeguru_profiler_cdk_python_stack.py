import aws_cdk as core
import aws_cdk.assertions as assertions

from codeguru_profiler_cdk_python_app.codeguru_profiler_cdk_python_stack import CodeguruProfilerCdkPythonAppStack

def test_sqs_queue_created():
    app = core.App()
    stack = CodeguruProfilerCdkPythonAppStack(app, "codeguru-profiler-cdk-python-app")
    template = assertions.Template.from_stack(stack)
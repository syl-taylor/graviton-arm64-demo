#!/usr/bin/env python3
import os

import aws_cdk as cdk

from arm64_demo.arm64_demo_stack import Arm64DemoStack

app = cdk.App()

Arm64DemoStack(app, "Arm64DemoStack",
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION')
    )
)

app.synth()

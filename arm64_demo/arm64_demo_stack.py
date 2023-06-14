from aws_cdk import (
    Aws,
    Stack,
    Duration,
    aws_codecommit as codecommit,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_codebuild as codebuild,
    aws_ecr as ecr,
    aws_iam as iam
)
from constructs import Construct

class Arm64DemoStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.aws_account = Aws.ACCOUNT_ID
        self.aws_region = Aws.REGION

        self.repository_name = "arm64_demo"

        # Existing resources
        self.src_repository = codecommit.Repository.from_repository_name(self, "Arm64DemoCodeCommitRepo",
            repository_name=self.repository_name
        )
        self.ecr_repository = ecr.Repository.from_repository_name(self, "Arm64DemoECRRepo",
            repository_name=self.repository_name
        )

        self.environment_variables_base={
            "ECR_REPO_NAME": codebuild.BuildEnvironmentVariable(
                value=self.repository_name
            ),
            "AWS_ACCOUNT_ID": codebuild.BuildEnvironmentVariable(
                value=self.aws_account
            ),
            "AWS_REGION": codebuild.BuildEnvironmentVariable(
                value=self.aws_region
            )
        }

        self.create_iam_policies()
        self.create_pipeline()

    def create_iam_policies(self):
        self.codecommit_policy = iam.PolicyStatement(
            sid="AllowSrcPulls",
            effect=iam.Effect.ALLOW,
            actions=[
                "codecommit:GitPull"
            ],
            resources=[f"arn:aws:codecommit:{self.aws_region}:{self.aws_account}:{self.repository_name}"]
        )
        self.ecr_ops_policy = iam.PolicyStatement(
            sid="AllowECROps",
            effect=iam.Effect.ALLOW,
            actions=[
                "ecr:BatchGetImage",
                "ecr:PutImage",
                "ecr:BatchCheckLayerAvailability",
                "ecr:CompleteLayerUpload",
                "ecr:UploadLayerPart",
                "ecr:InitiateLayerUpload",
                "ecr:GetDownloadUrlForLayer"
            ],
            resources=[f"arn:aws:ecr:{self.aws_region}:{self.aws_account}:repository/{self.repository_name}"]
        )
        self.ecr_auth_policy = iam.PolicyStatement(
            sid="AllowECRAuth",
            effect=iam.Effect.ALLOW,
            actions=[
                "ecr:GetAuthorizationToken"
            ],
            resources=["*"]
        )

    def create_pipeline(self):
        pipeline = codepipeline.Pipeline(self, "Arm64DemoPipeline")

        # Source code: CodeCommit Repo
        source_stage = pipeline.add_stage(stage_name="Source_Code")
        source_output = codepipeline.Artifact("SourceArtifact")
        source_stage.add_action(codepipeline_actions.CodeCommitSourceAction(
            action_name="Source_Code",
            repository=self.src_repository,
            output=source_output,
            branch='main',
            run_order=1
        ))

        # Build speed: Native
        build_native_speed_stage = pipeline.add_stage(
            placement=codepipeline.StagePlacement(
                just_after=source_stage
            ),
            stage_name="Concept_1A_Build_Speed_Native"
        )

        build_native_speed_x86_project = codebuild.Project(self, "Native_Speed_x86_Build",
            source=codebuild.Source.code_commit(
                repository=self.src_repository
            ),
            build_spec=codebuild.BuildSpec.from_source_filename("native_build/native_build.yml"),
            environment=codebuild.BuildEnvironment(
                compute_type=codebuild.ComputeType.LARGE,
                build_image=codebuild.LinuxBuildImage.STANDARD_4_0,
                privileged=True
            )
        )
        build_native_speed_x86_project.add_to_role_policy(self.codecommit_policy)
        build_native_speed_x86_project.add_to_role_policy(self.ecr_ops_policy)
        build_native_speed_x86_project.add_to_role_policy(self.ecr_auth_policy)

        build_native_speed_arm64_project = codebuild.Project(self, "Native_Speed_arm64_Build",
            source=codebuild.Source.code_commit(
                repository=self.src_repository
            ),
            build_spec=codebuild.BuildSpec.from_source_filename("native_build/native_build.yml"),
            environment=codebuild.BuildEnvironment(
                compute_type=codebuild.ComputeType.LARGE,
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_ARM_2,
                privileged=True
            )
        )
        build_native_speed_arm64_project.add_to_role_policy(self.codecommit_policy)
        build_native_speed_arm64_project.add_to_role_policy(self.ecr_ops_policy)
        build_native_speed_arm64_project.add_to_role_policy(self.ecr_auth_policy)

        build_native_speed_multi_arch_project = codebuild.Project(self, "Native_Speed_Multi-Arch_Build",
            source=codebuild.Source.code_commit(
                repository=self.src_repository
            ),
            build_spec=codebuild.BuildSpec.from_source_filename("native_build/native_build_multi_arch.yml"),
            environment=codebuild.BuildEnvironment(
                compute_type=codebuild.ComputeType.LARGE,
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_ARM_2,
                privileged=True
            )
        )
        build_native_speed_multi_arch_project.add_to_role_policy(self.codecommit_policy)
        build_native_speed_multi_arch_project.add_to_role_policy(self.ecr_ops_policy)
        build_native_speed_multi_arch_project.add_to_role_policy(self.ecr_auth_policy)

        envs = dict(self.environment_variables_base)
        envs.update({"FILES_LOCATION": codebuild.BuildEnvironmentVariable(value="native_speed")})
        envs.update({"CONTAINER_NAME": codebuild.BuildEnvironmentVariable(value="compute_bound_native")})
        envs.update({"PLATFORM": codebuild.BuildEnvironmentVariable(value="x86")})
        build_native_speed_stage.add_action(codepipeline_actions.CodeBuildAction(
            action_name="Native_Speed_x86_Build",
            input=source_output,
            project=build_native_speed_x86_project,
            environment_variables=envs,
            run_order=1
        ))
        envs.update({"PLATFORM": codebuild.BuildEnvironmentVariable(value="arm64")})
        build_native_speed_stage.add_action(codepipeline_actions.CodeBuildAction(
            action_name="Native_Speed_arm64_Build",
            input=source_output,
            project=build_native_speed_arm64_project,
            environment_variables=envs,
            run_order=1
        ))
        build_native_speed_stage.add_action(codepipeline_actions.CodeBuildAction(
            action_name="Native_Speed_Multi_Arch_Build",
            input=source_output,
            project=build_native_speed_multi_arch_project,
            environment_variables=envs,
            run_order=2
        ))

        # Build speed: Emulation
        build_emulated_speed_stage = pipeline.add_stage(
            placement=codepipeline.StagePlacement(
                just_after=build_native_speed_stage
            ),
            stage_name="Concept_1B_Build_Speed_Emulated"
        )

        build_emulated_speed_project = codebuild.Project(self, "Emulated_Speed_Multi-Arch_Build",
            source=codebuild.Source.code_commit(
                repository=self.src_repository
            ),
            build_spec=codebuild.BuildSpec.from_source_filename("emulated_speed/emulated_speed.yml"),
            environment=codebuild.BuildEnvironment(
                compute_type=codebuild.ComputeType.LARGE,
                build_image=codebuild.LinuxBuildImage.STANDARD_4_0,
                privileged=True
            ),
            timeout=Duration.minutes(120)
        )
        build_emulated_speed_project.add_to_role_policy(self.codecommit_policy)
        build_emulated_speed_project.add_to_role_policy(self.ecr_ops_policy)
        build_emulated_speed_project.add_to_role_policy(self.ecr_auth_policy)

        build_emulated_speed_stage.add_action(codepipeline_actions.CodeBuildAction(
            action_name="Emulated_Speed_Multi-Arch_Build",
            input=source_output,
            project=build_emulated_speed_project,
            environment_variables=self.environment_variables_base,
            run_order=1
        ))

        # Build Cases: Working
        build_software_running_stage = pipeline.add_stage(
            placement=codepipeline.StagePlacement(
                just_after=build_emulated_speed_stage
            ),
            stage_name="Concept_2A_Software_Running"
        )

        build_software_running_x86_project = codebuild.Project(self, "Software_Running_x86_Build",
            source=codebuild.Source.code_commit(
                repository=self.src_repository
            ),
            build_spec=codebuild.BuildSpec.from_source_filename("native_build/native_build.yml"),
            environment=codebuild.BuildEnvironment(
                compute_type=codebuild.ComputeType.LARGE,
                build_image=codebuild.LinuxBuildImage.STANDARD_4_0,
                privileged=True
            )
        )
        build_software_running_x86_project.add_to_role_policy(self.codecommit_policy)
        build_software_running_x86_project.add_to_role_policy(self.ecr_ops_policy)
        build_software_running_x86_project.add_to_role_policy(self.ecr_auth_policy)

        build_software_running_arm64_project = codebuild.Project(self, "Software_Running_arm64_Build",
            source=codebuild.Source.code_commit(
                repository=self.src_repository
            ),
            build_spec=codebuild.BuildSpec.from_source_filename("native_build/native_build.yml"),
            environment=codebuild.BuildEnvironment(
                compute_type=codebuild.ComputeType.LARGE,
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_ARM_2,
                privileged=True
            )
        )
        build_software_running_arm64_project.add_to_role_policy(self.codecommit_policy)
        build_software_running_arm64_project.add_to_role_policy(self.ecr_ops_policy)
        build_software_running_arm64_project.add_to_role_policy(self.ecr_auth_policy)

        build_software_running_multi_arch_project = codebuild.Project(self, "Software_Running_Multi-Arch_Build",
            source=codebuild.Source.code_commit(
                repository=self.src_repository
            ),
            build_spec=codebuild.BuildSpec.from_source_filename("native_build/native_build_multi_arch.yml"),
            environment=codebuild.BuildEnvironment(
                compute_type=codebuild.ComputeType.LARGE,
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_ARM_2,
                privileged=True
            )
        )
        build_software_running_multi_arch_project.add_to_role_policy(self.codecommit_policy)
        build_software_running_multi_arch_project.add_to_role_policy(self.ecr_ops_policy)
        build_software_running_multi_arch_project.add_to_role_policy(self.ecr_auth_policy)

        envs = dict(self.environment_variables_base)
        envs.update({"CONTAINER_NAME": codebuild.BuildEnvironmentVariable(value="software_running")})
        envs.update({"FILES_LOCATION": codebuild.BuildEnvironmentVariable(value="software_running")})
        envs.update({"PLATFORM": codebuild.BuildEnvironmentVariable(value="x86")})
        build_software_running_stage.add_action(codepipeline_actions.CodeBuildAction(
            action_name="Software_Running_x86_Build",
            input=source_output,
            project=build_software_running_x86_project,
            environment_variables=envs,
            run_order=1
        ))
        envs.update({"PLATFORM": codebuild.BuildEnvironmentVariable(value="arm64")})
        build_software_running_stage.add_action(codepipeline_actions.CodeBuildAction(
            action_name="Software_Running_arm64_Build",
            input=source_output,
            project=build_software_running_arm64_project,
            environment_variables=envs,
            run_order=1
        ))
        build_software_running_stage.add_action(codepipeline_actions.CodeBuildAction(
            action_name="Software_Running_Multi_Arch_Build",
            input=source_output,
            project=build_software_running_multi_arch_project,
            environment_variables=envs,
            run_order=2
        ))

        # Build Cases: Not Working
        build_software_not_running_stage = pipeline.add_stage(
            placement=codepipeline.StagePlacement(
                just_after=build_software_running_stage
            ),
            stage_name="Concept_2B_Software_Not_Running"
        )

        build_python_x86_project = codebuild.Project(self, "Python_x86_Build",
            source=codebuild.Source.code_commit(
                repository=self.src_repository
            ),
            build_spec=codebuild.BuildSpec.from_source_filename("native_build/native_build.yml"),
            environment=codebuild.BuildEnvironment(
                compute_type=codebuild.ComputeType.LARGE,
                build_image=codebuild.LinuxBuildImage.STANDARD_4_0,
                privileged=True
            )
        )
        build_python_x86_project.add_to_role_policy(self.codecommit_policy)
        build_python_x86_project.add_to_role_policy(self.ecr_ops_policy)
        build_python_x86_project.add_to_role_policy(self.ecr_auth_policy)

        build_python_fixes_arm64_project = codebuild.Project(self, "Python_Fixes_arm64_Build",
            source=codebuild.Source.code_commit(
                repository=self.src_repository
            ),
            build_spec=codebuild.BuildSpec.from_source_filename("native_build/native_build.yml"),
            environment=codebuild.BuildEnvironment(
                compute_type=codebuild.ComputeType.LARGE,
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_ARM_2,
                privileged=True
            )
        )
        build_python_fixes_arm64_project.add_to_role_policy(self.codecommit_policy)
        build_python_fixes_arm64_project.add_to_role_policy(self.ecr_ops_policy)
        build_python_fixes_arm64_project.add_to_role_policy(self.ecr_auth_policy)

        envs = dict(self.environment_variables_base)
        envs.update({"CONTAINER_NAME": codebuild.BuildEnvironmentVariable(value="python")})
        envs.update({"FILES_LOCATION": codebuild.BuildEnvironmentVariable(value="software_not_running/python_issues")})
        envs.update({"PLATFORM": codebuild.BuildEnvironmentVariable(value="x86")})
        build_software_not_running_stage.add_action(codepipeline_actions.CodeBuildAction(
            action_name="Python_x86_Build",
            input=source_output,
            project=build_python_x86_project,
            environment_variables=envs,
            run_order=1
        ))
        envs.update({"PLATFORM": codebuild.BuildEnvironmentVariable(value="arm64")})
        envs.update({"FILES_LOCATION": codebuild.BuildEnvironmentVariable(value="software_not_running/python_fixes")})
        build_software_not_running_stage.add_action(codepipeline_actions.CodeBuildAction(
            action_name="Python_Fixes_arm64_Build",
            input=source_output,
            project=build_python_fixes_arm64_project,
            environment_variables=envs,
            run_order=1
        ))

        build_nodejs_x86_project = codebuild.Project(self, "Nodejs_x86_Build",
            source=codebuild.Source.code_commit(
                repository=self.src_repository
            ),
            build_spec=codebuild.BuildSpec.from_source_filename("native_build/native_build.yml"),
            environment=codebuild.BuildEnvironment(
                compute_type=codebuild.ComputeType.LARGE,
                build_image=codebuild.LinuxBuildImage.STANDARD_4_0,
                privileged=True
            )
        )
        build_nodejs_x86_project.add_to_role_policy(self.codecommit_policy)
        build_nodejs_x86_project.add_to_role_policy(self.ecr_ops_policy)
        build_nodejs_x86_project.add_to_role_policy(self.ecr_auth_policy)

        build_nodejs_fixes_arm64_project = codebuild.Project(self, "Nodejs_Fixes_arm64_Build",
            source=codebuild.Source.code_commit(
                repository=self.src_repository
            ),
            build_spec=codebuild.BuildSpec.from_source_filename("native_build/native_build.yml"),
            environment=codebuild.BuildEnvironment(
                compute_type=codebuild.ComputeType.LARGE,
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_ARM_2,
                privileged=True
            )
        )
        build_nodejs_fixes_arm64_project.add_to_role_policy(self.codecommit_policy)
        build_nodejs_fixes_arm64_project.add_to_role_policy(self.ecr_ops_policy)
        build_nodejs_fixes_arm64_project.add_to_role_policy(self.ecr_auth_policy)

        envs = dict(self.environment_variables_base)
        envs.update({"CONTAINER_NAME": codebuild.BuildEnvironmentVariable(value="nodejs")})
        envs.update({"FILES_LOCATION": codebuild.BuildEnvironmentVariable(value="software_not_running/nodejs_issues")})
        envs.update({"PLATFORM": codebuild.BuildEnvironmentVariable(value="x86")})
        build_software_not_running_stage.add_action(codepipeline_actions.CodeBuildAction(
            action_name="Nodejs_x86_Build",
            input=source_output,
            project=build_nodejs_x86_project,
            environment_variables=envs,
            run_order=2
        ))
        envs.update({"PLATFORM": codebuild.BuildEnvironmentVariable(value="arm64")})
        envs.update({"FILES_LOCATION": codebuild.BuildEnvironmentVariable(value="software_not_running/nodejs_fixes")})
        build_software_not_running_stage.add_action(codepipeline_actions.CodeBuildAction(
            action_name="Nodejs_Fixes_arm64_Build",
            input=source_output,
            project=build_nodejs_fixes_arm64_project,
            environment_variables=envs,
            run_order=2
        ))

        # Runtime Tests
        build_runtime_tests_stage = pipeline.add_stage(
            placement=codepipeline.StagePlacement(
                just_after=build_software_not_running_stage
            ),
            stage_name="Concept_3A_Runtime_Tests"
        )

        build_go_tests_x86_project = codebuild.Project(self, "Go_Tests_x86_Build",
            source=codebuild.Source.code_commit(
                repository=self.src_repository
            ),
            build_spec=codebuild.BuildSpec.from_source_filename("native_build/native_build.yml"),
            environment=codebuild.BuildEnvironment(
                compute_type=codebuild.ComputeType.LARGE,
                build_image=codebuild.LinuxBuildImage.STANDARD_4_0,
                privileged=True
            )
        )
        build_go_tests_x86_project.add_to_role_policy(self.codecommit_policy)
        build_go_tests_x86_project.add_to_role_policy(self.ecr_ops_policy)
        build_go_tests_x86_project.add_to_role_policy(self.ecr_auth_policy)

        build_go_tests_arm64_project = codebuild.Project(self, "Go_Tests_arm64_Build",
            source=codebuild.Source.code_commit(
                repository=self.src_repository
            ),
            build_spec=codebuild.BuildSpec.from_source_filename("native_build/native_build.yml"),
            environment=codebuild.BuildEnvironment(
                compute_type=codebuild.ComputeType.LARGE,
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_ARM_2,
                privileged=True
            )
        )
        build_go_tests_arm64_project.add_to_role_policy(self.codecommit_policy)
        build_go_tests_arm64_project.add_to_role_policy(self.ecr_ops_policy)
        build_go_tests_arm64_project.add_to_role_policy(self.ecr_auth_policy)

        envs = dict(self.environment_variables_base)
        envs.update({"CONTAINER_NAME": codebuild.BuildEnvironmentVariable(value="go")})
        envs.update({"FILES_LOCATION": codebuild.BuildEnvironmentVariable(value="runtime_tests/go_tests_issues")})
        envs.update({"PLATFORM": codebuild.BuildEnvironmentVariable(value="x86")})
        build_runtime_tests_stage.add_action(codepipeline_actions.CodeBuildAction(
            action_name="Go_Tests_x86_Build",
            input=source_output,
            project=build_go_tests_x86_project,
            environment_variables=envs,
            run_order=1
        ))
        envs.update({"PLATFORM": codebuild.BuildEnvironmentVariable(value="arm64")})
        envs.update({"FILES_LOCATION": codebuild.BuildEnvironmentVariable(value="runtime_tests/go_tests_fixed")})
        build_runtime_tests_stage.add_action(codepipeline_actions.CodeBuildAction(
            action_name="Go_Tests_Fixes_arm64_Build",
            input=source_output,
            project=build_go_tests_arm64_project,
            environment_variables=envs,
            run_order=1
        ))

        # Performance Tests
        build_perf_tests_stage = pipeline.add_stage(
            placement=codepipeline.StagePlacement(
                just_after=build_runtime_tests_stage
            ),
            stage_name="Concept_3B_Performance_Tests"
        )

        build_perf_tests_x86_project = codebuild.Project(self, "XGBoost_x86_Build",
            source=codebuild.Source.code_commit(
                repository=self.src_repository
            ),
            build_spec=codebuild.BuildSpec.from_source_filename("native_build/native_build.yml"),
            environment=codebuild.BuildEnvironment(
                compute_type=codebuild.ComputeType.LARGE,
                build_image=codebuild.LinuxBuildImage.STANDARD_4_0,
                privileged=True
            )
        )
        build_perf_tests_x86_project.add_to_role_policy(self.codecommit_policy)
        build_perf_tests_x86_project.add_to_role_policy(self.ecr_ops_policy)
        build_perf_tests_x86_project.add_to_role_policy(self.ecr_auth_policy)

        build_perf_tests_arm64_project = codebuild.Project(self, "XGBoost_arm64_Build",
            source=codebuild.Source.code_commit(
                repository=self.src_repository
            ),
            build_spec=codebuild.BuildSpec.from_source_filename("native_build/native_build.yml"),
            environment=codebuild.BuildEnvironment(
                compute_type=codebuild.ComputeType.LARGE,
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_ARM_2,
                privileged=True
            )
        )
        build_perf_tests_arm64_project.add_to_role_policy(self.codecommit_policy)
        build_perf_tests_arm64_project.add_to_role_policy(self.ecr_ops_policy)
        build_perf_tests_arm64_project.add_to_role_policy(self.ecr_auth_policy)

        envs = dict(self.environment_variables_base)
        envs.update({"CONTAINER_NAME": codebuild.BuildEnvironmentVariable(value="xgboost")})
        envs.update({"FILES_LOCATION": codebuild.BuildEnvironmentVariable(value="perf_tests")})
        envs.update({"PLATFORM": codebuild.BuildEnvironmentVariable(value="x86")})
        build_perf_tests_stage.add_action(codepipeline_actions.CodeBuildAction(
            action_name="XGBoost_Perf_x86_Build",
            input=source_output,
            project=build_perf_tests_x86_project,
            environment_variables=envs,
            run_order=1
        ))
        envs.update({"PLATFORM": codebuild.BuildEnvironmentVariable(value="arm64")})
        build_perf_tests_stage.add_action(codepipeline_actions.CodeBuildAction(
            action_name="XGBoost_Perf_arm64_Build",
            input=source_output,
            project=build_perf_tests_arm64_project,
            environment_variables=envs,
            run_order=1
        ))

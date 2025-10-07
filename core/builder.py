import logging
from core.generator import CodeGenerator
from core.deployer import Deployer

logger = logging.getLogger("llm_agent.core.builder")


class Builder:
    """
    Full Build → Deploy → Notify orchestrator.
    """

    def __init__(self):
        self.generator = CodeGenerator()
        self.deployer = Deployer()

    def run_full_pipeline(self, brief, project_name):
        """
        Step 1. Generate project code
        Step 2. Deploy to GitHub
        Step 3. Return final result metadata
        """
        logger.info(f"🧠 Running full build pipeline for {project_name}")

        build_metadata = self.generator.orchestrate_build(brief, project_name)
        deploy_metadata = self.deployer.deploy_to_github(build_metadata)

        final = {
            "project": project_name,
            "build_output": build_metadata,
            "deployment": deploy_metadata,
        }

        logger.info(f"🎯 Pipeline completed for {project_name}")
        return final

import logging
from core.generator import CodeGenerator
from core.reviser import Reviser
from core.deployer import Deployer

logger = logging.getLogger("llm_agent.core.builder")


class Builder:
    """
    Full Build → Deploy → Notify orchestrator.
    """

    def __init__(self):
        self.generator = CodeGenerator()
        self.deployer = Deployer()

    async def run_full_pipeline(self, task, brief, checks, attachments):
        """
        Step 1. Generate project code
        Step 2. Deploy to GitHub
        Step 3. Return final result metadata
        """
        logger.info(f"🧠 Running full build pipeline for {task}")

        build_metadata = await self.generator.orchestrate_build(task, brief, checks, attachments)
        deploy_metadata = await self.deployer.deploy_to_github(build_metadata)

        final = {
            "project": task,
            "build_output": build_metadata,
            "deployment": deploy_metadata,
        }

        logger.info(f"🎯 Pipeline completed for {task}")
        return final
    
    async def run_revision_pipeline(self, task, brief, checks, attachments):
        """
        Step 1. Apply revision/refactor
        Step 2. Push changes to GitHub
        Step 3. Redeploy Pages
        """
        logger.info(f"🔁 Running revision pipeline for {task}")

        reviser = Reviser()
        deployer = Deployer()

        # Step 1: Refactor code
        revision_metadata = await reviser.apply_revision(task, brief, checks, attachments)

        # Step 2: Push updated files & redeploy Pages
        deployment_metadata = await deployer.deploy_to_github(revision_metadata)

        result = {
            "project": task,
            "revision_output": revision_metadata,
            "deployment": deployment_metadata
        }

        logger.info(f"✅ Revision pipeline complete for {task}")
        return result

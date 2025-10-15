import logging
from typing import Dict, Any
from services.github_service import GitHubService

logger = logging.getLogger("llm_agent.core.deployer")


class Deployer:
    """
    Handles deployment of generated project to GitHub Pages.
    """

    def __init__(self):
        self.github = GitHubService()

    async def deploy_to_github(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deploy generated files to GitHub and enable Pages.
        """
        repo_name = metadata["task"].strip().replace(" ", "-")
        files = metadata["saved_files"]

        logger.info(f"🚀 Starting deployment for {repo_name}...")

        repo_url = await self.github.get_or_create_repo(repo_name)
        commit_sha = self.github.upload_all_files_single_commit(repo_name, files)
        pages_url = self.github.enable_pages(repo_name)

        deployment_info = {
            "repo_name": repo_name,
            "commit_sha": commit_sha,
            "repo_url": repo_url,
            "pages_url": pages_url,
        }

        logger.info(f"✅ Deployment complete: {deployment_info}")
        return deployment_info

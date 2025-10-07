import os
import base64
import time
import logging
import requests
from github import Github
from typing import Dict, List

logger = logging.getLogger("llm_agent.services.github_service")


class GitHubService:
    """
    Handles GitHub interactions: repo creation, commits, and Pages enablement.
    Requires a GitHub personal access token (PAT) with 'repo' and 'pages' scopes.
    """

    def __init__(self):
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("❌ Missing GITHUB_TOKEN in environment.")
        self.client = Github(token)
        self.user = self.client.get_user()

    def create_repo(self, repo_name: str, private: bool = False) -> str:
        """Create a repository if not existing."""
        try:
            repo = self.user.create_repo(repo_name, private=private, auto_init=False)
            logger.info(f"✅ Created GitHub repo: {repo_name}")
        except Exception as e:
            # Fallback: reuse existing repo
            repo = self.user.get_repo(repo_name)
            logger.warning(f"⚠️ Repo already exists, using existing: {repo_name} ({e})")
        return repo.clone_url

    def upload_files(self, repo_name: str, files: List[str]):
        """Upload generated files to the repository."""
        repo = self.user.get_repo(repo_name)
        for filepath in files:
            filename = os.path.basename(filepath)
            content = open(filepath, "rb").read()
            encoded = base64.b64encode(content).decode("utf-8")

            try:
                repo.create_file(
                    path=filename,
                    message=f"Add {filename}",
                    content=base64.b64decode(encoded).decode("utf-8"),
                    branch="main",
                )
                logger.debug(f"📄 Uploaded {filename}")
            except Exception as e:
                logger.warning(f"⚠️ Skipping {filename}, possibly exists. ({e})")

    def add_license(self, repo_name: str):
        """Add an MIT License file."""
        license_text = """MIT License

Copyright (c) 2025 Student

Permission is hereby granted, free of charge, to any person obtaining a copy...
"""
        repo = self.user.get_repo(repo_name)
        try:
            repo.create_file("LICENSE", "Add MIT License", license_text, branch="main")
            logger.info("📜 Added LICENSE file.")
        except Exception as e:
            logger.warning(f"⚠️ Could not add LICENSE: {e}")

    def enable_pages(self, repo_name: str, branch: str = "main") -> str:
        """Enable GitHub Pages for the repo using REST API."""
        url = f"https://api.github.com/repos/{self.user.login}/{repo_name}/pages"
        headers = {
            "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {"source": {"branch": branch, "path": "/"}}

        response = requests.post(url, headers=headers, json=data)
        if response.status_code in (201, 204):
            pages_url = f"https://{self.user.login}.github.io/{repo_name}/"
            logger.info(f"🌐 GitHub Pages enabled at {pages_url}")
        elif response.status_code == 409:
            pages_url = f"https://{self.user.login}.github.io/{repo_name}/"
            logger.warning(f"⚠️ Pages site already exists for {repo_name}")
        else:
            pages_url = "Pages not available"
            logger.warning(f"❌ Failed to create Pages site: {response.status_code} {response.json()}")

        return pages_url



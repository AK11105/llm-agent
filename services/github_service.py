import os
import time
import asyncio
import logging
import requests
from github import Github, GithubException, InputGitTreeElement
from typing import List

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

    async def get_or_create_repo(self, repo_name: str, private: bool = False, retries: int = 3, delay: float = 1.0):
        """
        Async-safe GitHub repo creation with retry for propagation delay.
        """
        for attempt in range(retries):
            try:
                repo = self.user.get_repo(repo_name)
                print(f"Repo '{repo_name}' exists.")
                return repo.clone_url
            except GithubException as e:
                if e.status == 404:
                    try:
                        print(f"Repo '{repo_name}' not found. Creating it...")
                        repo = self.user.create_repo(repo_name, private=private, auto_init=True)
                        await asyncio.sleep(delay)  # Wait for GitHub propagation
                        repo = self.user.get_repo(repo_name)
                        return repo.clone_url
                    except GithubException as create_err:
                        if create_err.status == 422 and "name already exists" in str(create_err.data):
                            print(f"Repo '{repo_name}' already exists. Retrying get_repo...")
                            await asyncio.sleep(delay)
                        else:
                            raise
                else:
                    raise
        raise Exception(f"Failed to access or create repo '{repo_name}' after {retries} attempts")

    def upload_all_files_single_commit(
        self,
        repo_name: str,
        file_paths: List[str],
        include_license: bool = True,
        commit_message: str = "Add all generated project files"
    ) -> str:
        """
        Uploads all files (including LICENSE, README, etc.) in a single commit.
        Returns: Commit SHA
        """
        repo = self.user.get_repo(repo_name)

        try:
            ref = repo.get_git_ref("heads/main")
            base_commit = repo.get_commit(ref.object.sha)
        except GithubException as e:
            # Repo is empty or 'main' branch does not exist
            if e.status == 409:
                logger.warning("⚠️ Repo empty, creating initial commit on 'main' branch...")
                # Create a README as the first commit
                repo.create_file(
                    path="README.md",
                    message="Initial commit",
                    content=f"# {repo_name}\nInitial scaffold",
                    branch="main"
                )
                ref = repo.get_git_ref("heads/main")
                base_commit = repo.get_commit(ref.object.sha)
            else:
                raise

        # Collect files (and add license if needed)
        blobs = []
        for filepath in file_paths:
            filename = os.path.basename(filepath)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            blob = repo.create_git_blob(content, "utf-8")
            blobs.append((filename, blob))
            logger.debug(f"📦 Prepared blob for {filename}")

        if include_license:
            license_text = """MIT License

Copyright (c) 2025 Atharva Kulkarni

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
    """
            blob = repo.create_git_blob(license_text, "utf-8")
            blobs.append(("LICENSE", blob))
            logger.debug("📜 Prepared MIT LICENSE blob")

        # Build new tree
        tree_elements = [
            InputGitTreeElement(path=filename, mode="100644", type="blob", sha=blob.sha)
            for filename, blob in blobs
        ]   
        new_tree = repo.create_git_tree(tree_elements, base_commit.commit.tree)
        logger.debug("🌲 Created new Git tree for all files.")

        # Commit and update branch
        new_commit = repo.create_git_commit(commit_message, new_tree, [base_commit.commit])
        ref.edit(new_commit.sha)
        logger.info(f"✅ Pushed all files in single commit ({new_commit.sha})")

        return new_commit.sha



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

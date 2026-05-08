import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import json
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

# --- Mock Implementations (for demonstration without real LLM/Data Sources) ---
class MockLLM:
    """A mock LLM client to simulate responses for demonstration purposes."""
    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        # Simulate LLM response based on prompt keywords
        prompt_lower = prompt.lower()

        if "plan" in prompt_lower and "ci/cd failure" in prompt_lower:
            return json.dumps({
                "plan": [
                    {"step": 1, "task": "Identify specific error message and context from user query.", "agent": "KnowledgeRetrievalAgent"},
                    {"step": 2, "task": "Search recent CI/CD logs for 'permission denied' errors and relevant timestamps.", "agent": "KnowledgeRetrievalAgent"},
                    {"step": 3, "task": "Retrieve deployment pipeline configuration for the 'deploy-to-prod' stage.", "agent": "KnowledgeRetrievalAgent"},
                    {"step": 4, "task": "Analyze retrieved logs and configuration to diagnose the root cause of the permission denied error.", "agent": "DiagnosisAgent"},
                    {"step": 5, "task": "Propose a solution to fix the permission issue, e.g., update IAM policy or service account permissions.", "agent": "SolutionAgent"}
                ]
            })
        elif "identify specific error" in prompt_lower:
            return "Identified error: 'permission denied' on 'deploy-to-prod' stage. Key phrase: 'Failed to upload artifact: Access Denied'."
        elif "search recent ci/cd logs" in prompt_lower:
            return "Retrieved log snippet: ERROR: Permission denied for user 'jenkins' attempting to deploy to S3 bucket 'prod-artifacts'. Full log details indicate 's3:PutObject' permission missing."
        elif "retrieve deployment pipeline configuration" in prompt_lower:
            return "Retrieved config snippet: 'deploy-to-prod' stage uses IAM role 'arn:aws:iam::123456789012:role/jenkins-deployer-role'. This role is attached to the CI runner."
        elif "diagnose root cause" in prompt_lower:
            return "Diagnosis: The 'jenkins-deployer-role' attached to the CI/CD pipeline lacks the necessary S3 write permissions (`s3:PutObject`) for the `prod-artifacts` S3 bucket. The user 'jenkins' is implicitly assuming this role during deployment."
        elif "propose a solution" in prompt_lower:
            return "Solution: Update the IAM policy attached to the 'jenkins-deployer-role' to explicitly include `s3:PutObject` permission on the resource `arn:aws:s3:::prod-artifacts/*`. Ensure the policy is applied correctly and verify with a test deployment.\n\n```bash\naws iam attach-role-policy --role-name jenkins-deployer-role --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess # (for demonstration, use least privilege in prod)
# OR specific policy update:
# aws iam put-role-policy --role-name jenkins-deployer-role --policy-name S3ProdDeployPolicy --policy-document file://path/to/updated_policy.json
```"
        else:
            return f"Mock LLM received prompt: {prompt[:150]}... (Responding with a generic message)."

class MockDataSource:
    """A mock data source to simulate external knowledge bases like logs, configs, docs."""
    def query(self, query_type: str, context: str) -> str:
        if "recent CI/CD logs" in query_type and "permission denied" in context:
            return "Mocked CI/CD Log (recent relevant snippet):\n```\n2026-05-08T10:30:00Z INFO Starting deploy-to-prod stage...\n2026-05-08T10:30:15Z ERROR Failed to upload artifact: Access Denied. User 'arn:aws:iam::123456789012:user/jenkins' is not authorized to perform 's3:PutObject' on resource 'arn:aws:s3:::prod-artifacts/app-v1.0.tar.gz' with key 'app-v1.0.tar.gz'.\n```"
        elif "pipeline configuration" in query_type and "deploy-to-prod" in context:
            return "Mocked Pipeline Config (relevant section for deploy-to-prod):\n```yaml\nstages:\n  - build\n  - test\n  - deploy-to-prod\n\ndeploy-to-prod:\n  script:\n    - aws s3 cp ./app-artifact.tar.gz s3://prod-artifacts/\n  environment:\n    AWS_REGION: us-east-1\n    IAM_ROLE: jenkins-deployer-role # This role is assumed by the CI runner\n```"
        elif "documentation" in query_type:
            return "Mocked Docs: AWS S3 permissions for CI/CD often require `s3:PutObject` and `s3:GetObject` on target buckets for artifact deployment. Ensure the IAM role has the necessary policy attached for the specific bucket and actions.\nContextual tip: IAM policies can be inline or managed, and specific resource ARNs should be used for least privilege."
        elif "error message" in query_type:
            return f
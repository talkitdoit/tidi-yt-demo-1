import os
from typing import Dict, List, Optional
from dataclasses import dataclass
import asyncio
from abc import ABC, abstractmethod
from github import Github
import json
from pathlib import Path
import subprocess
from dotenv import load_dotenv
import aiohttp

# Load environment variables from .env file
load_dotenv()

@dataclass
class ApplicationSpec:
    """Defines the specifications for an application to be deployed"""
    name: str
    description: str
    framework: str  # Change to "go"
    target_framework: str  # Not really needed for Go but keep for compatibility
    container_port: int = 80

class BaseAgent(ABC):
    """Abstract base class for all agents in the system"""
    def __init__(self, name: str):
        self.name = name
        self.context: Dict = {}  # Stores agent-specific context/state
    
    @abstractmethod
    async def process(self, message: str) -> str:
        """Process incoming messages - must be implemented by child classes"""
        pass

    async def communicate(self, message: str) -> str:
        """Handles communication logging and message processing"""
        print(f"\n{self.name} processing: {message}")
        response = await self.process(message)
        print(f"{self.name} responds: {response}")
        return response

class CodeGeneratorAgent(BaseAgent):
    def __init__(self):
        super().__init__("CodeGenerator")
    
    async def process(self, message: str) -> str:
        # For demo purposes, we'll return a simple template
        # In a real implementation, this would integrate with an LLM
        return """
        package main

        import (
            "github.com/pulumi/pulumi/sdk/v3/go/pulumi"
            "github.com/pulumi/pulumi-azure-native/sdk/go/azure/cdn"
            "github.com/pulumi/pulumi-azure-native/sdk/go/azure/storage"
        )

        func main() {
            pulumi.Run(func(ctx *pulumi.Context) error {
                // Your static website infrastructure code will go here
                return nil
            })
        }
        """

class InfrastructureAgent(BaseAgent):
    def __init__(self):
        super().__init__("Infrastructure")
    
    async def generate_pulumi_code(self, app_spec: ApplicationSpec) -> str:
        return """
        package main

        import (
            "github.com/pulumi/pulumi/sdk/v3/go/pulumi"
            "github.com/pulumi/pulumi-azure-native/sdk/go/azure/storage"
            "github.com/pulumi/pulumi-azure-native/sdk/go/azure/cdn"
        )

        func main() {
            pulumi.Run(func(ctx *pulumi.Context) error {
                // Create a resource group
                resourceGroup, err := resources.NewResourceGroup(ctx, "resourceGroup", nil)
                if err != nil {
                    return err
                }

                // Create a storage account
                storageAccount, err := storage.NewStorageAccount(ctx, "sa", &storage.StorageAccountArgs{
                    ResourceGroupName: resourceGroup.Name,
                    Kind:             pulumi.String("StorageV2"),
                    Sku: &storage.SkuArgs{
                        Name: pulumi.String("Standard_LRS"),
                    },
                })
                if err != nil {
                    return err
                }

                // Enable static website hosting
                staticWebsite, err := storage.NewStorageAccountStaticWebsite(ctx, "staticWebsite", &storage.StorageAccountStaticWebsiteArgs{
                    AccountName:       storageAccount.Name,
                    ResourceGroupName: resourceGroup.Name,
                    IndexDocument:     pulumi.String("index.html"),
                })
                if err != nil {
                    return err
                }

                return nil
            })
        }
        """

    async def generate_pulumi_yaml(self, app_spec: ApplicationSpec) -> str:
        return f"""
name: {app_spec.name}
description: A static website deployed to Azure using Pulumi
runtime: go
"""

    async def process(self, message: str) -> str:
        return "Generated Pulumi Go code for Azure Functions"

class GitOpsAgent(BaseAgent):
    def __init__(self):
        super().__init__("GitOps")
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is not set")
        self.github = Github(github_token)
    
    async def process(self, message: str) -> str:
        return "Processing GitOps request"
    
    async def create_repository(self, app_spec: ApplicationSpec) -> str:
        try:
            # Create GitHub repository
            user = self.github.get_user()
            repo = user.create_repo(
                app_spec.name,
                description=app_spec.description,
                private=True
            )
            return f"Created repository: {repo.html_url}"
        except Exception as e:
            return f"Failed to create repository: {str(e)}"

    async def commit_code(self, app_spec: ApplicationSpec, app_code: str, pulumi_code: str) -> str:
        try:
            repo = self.github.get_user().get_repo(app_spec.name)
            base_path = Path("talkitdoit-demo-app")  # Use existing directory
            
            # Initialize git in the existing directory
            git_commands = [
                "git init",
                "git add .",
                'git commit -m "Initial commit"',
                f"git remote add origin {repo.clone_url}",
                "git branch -M main",
                "git push -u origin main"
            ]
            
            for cmd in git_commands:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    check=True,
                    cwd=str(base_path),
                    capture_output=True,
                    text=True
                )
                print(f"Executed: {cmd}")
                print(f"Output: {result.stdout}")
            
            return f"Code committed to repository: {repo.html_url}"
        except Exception as e:
            return f"Failed to commit code: {str(e)}"

class DeploymentAgent(BaseAgent):
    """Handles deployment operations using Pulumi"""
    def __init__(self):
        super().__init__("Deployment")
        # Load required credentials from environment
        self.azure_credentials = os.getenv('AZURE_CREDENTIALS')
        self.pulumi_token = os.getenv('PULUMI_ACCESS_TOKEN')
        if not self.azure_credentials or not self.pulumi_token:
            raise ValueError("AZURE_CREDENTIALS or PULUMI_ACCESS_TOKEN not set")
    
    async def process(self, message: str) -> str:
        # Add message parsing to determine the action
        if message.lower().startswith("destroy"):
            project_name = message.split()[-1]
            self.context["project_name"] = project_name
            return await self.destroy(project_name)
        else:
            # Extract project name from Deploy command
            project_name = message.split()[-1]
            self.context["project_name"] = project_name
            return await self.deploy()
    
    async def deploy(self) -> str:
        """
        Deploys the application using Pulumi:
        1. Sets up Azure credentials
        2. Configures Pulumi access
        3. Runs deployment commands
        4. Returns deployment status and outputs
        """
        try:
            # Set up Azure credentials
            azure_creds = json.loads(self.azure_credentials)
            os.environ['ARM_CLIENT_ID'] = azure_creds['clientId']
            os.environ['ARM_CLIENT_SECRET'] = azure_creds['clientSecret']
            os.environ['ARM_TENANT_ID'] = azure_creds['tenantId']
            os.environ['ARM_SUBSCRIPTION_ID'] = azure_creds['subscriptionId']
            
            # Set up Pulumi access
            os.environ['PULUMI_ACCESS_TOKEN'] = self.pulumi_token
            
            # Use the project name from context
            project_name = self.context.get("project_name")
            if not project_name:
                raise ValueError("No project name specified")
            
            project_path = Path(project_name)
            if not project_path.exists():
                raise ValueError(f"Project directory {project_name} does not exist")
            
            commands = [
                "pulumi login",
                "go mod tidy",
                f"pulumi stack select talkitdoit-org/{project_name}/dev",
                "pulumi config set azure-native:location eastus",
                "pulumi up --yes"
            ]
            
            for cmd in commands:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=str(project_path)
                )
                print(f"Executing: {cmd}")
                print(f"Output: {result.stdout}")
                if result.returncode != 0:
                    raise Exception(f"Command failed: {cmd}\nError: {result.stderr}")
            
            # After successful deployment, get the output URLs
            output_cmd = "pulumi stack output --json"
            output_result = subprocess.run(
                output_cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(project_path)
            )
            
            if output_result.returncode == 0:
                outputs = json.loads(output_result.stdout)
                return json.dumps({
                    "status": "success",
                    "message": "Deployment completed successfully",
                    "outputs": outputs
                })
            
            return json.dumps({
                "status": "success",
                "message": "Deployment completed successfully, but couldn't fetch URLs"
            })
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Deployment failed: {str(e)}"
            })

    async def destroy(self, project_name: str) -> str:
        """
        Destroys deployed infrastructure:
        1. Sets up credentials
        2. Runs Pulumi destroy commands
        3. Returns destruction status
        """
        try:
            # Set up Azure credentials
            azure_creds = json.loads(self.azure_credentials)
            os.environ['ARM_CLIENT_ID'] = azure_creds['clientId']
            os.environ['ARM_CLIENT_SECRET'] = azure_creds['clientSecret']
            os.environ['ARM_TENANT_ID'] = azure_creds['tenantId']
            os.environ['ARM_SUBSCRIPTION_ID'] = azure_creds['subscriptionId']
            
            # Set up Pulumi access
            os.environ['PULUMI_ACCESS_TOKEN'] = self.pulumi_token
            
            project_path = Path(project_name)
            
            # Run the destroy command
            commands = [
                "pulumi login",
                f"pulumi stack select talkitdoit-org/{project_name}/dev",
                "pulumi destroy --yes"  # --yes flag to automatically approve
            ]
            
            for cmd in commands:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=str(project_path)
                )
                print(f"Executing: {cmd}")
                print(f"Output: {result.stdout}")
                if result.returncode != 0:
                    raise Exception(f"Command failed: {cmd}\nError: {result.stderr}")
            
            return json.dumps({
                "status": "success",
                "message": "Application successfully destroyed"
            })
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Destroy failed: {str(e)}"
            })

class PulumiCopilotAgent(BaseAgent):
    def __init__(self):
        super().__init__("PulumiCopilot")
        self.pulumi_token = os.getenv('PULUMI_ACCESS_TOKEN')
        if not self.pulumi_token:
            raise ValueError("PULUMI_ACCESS_TOKEN not set")
        self.base_url = "https://api.pulumi.com/api/ai/chat/preview"
        self.headers = {
            "Authorization": f"token {self.pulumi_token}",
            "Content-Type": "application/json"
        }

    async def test_connection(self) -> str:
        try:
            payload = {
                "query": "Can you help me check my code?",
                "state": {
                    "client": {
                        "cloudContext": {
                            "orgId": "talkitdoit-org",
                            "url": "https://app.pulumi.com"
                        }
                    }
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload
                ) as response:
                    print(f"Status: {response.status}")
                    response_text = await response.text()
                    print(f"Response: {response_text}")
                    return json.dumps({
                        "status": "success" if response.status == 200 else "error",
                        "message": f"Status: {response.status}, Response: {response_text[:200]}"
                    })

        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Connection test failed: {str(e)}"
            })

    async def analyze_code(self, project_path: str) -> str:
        try:
            # Read the main.go file content
            main_go_path = Path(project_path) / "main.go"
            if not main_go_path.exists():
                return json.dumps({
                    "status": "error",
                    "message": f"main.go not found in {project_path}"
                })

            with open(main_go_path, 'r') as f:
                code_content = f.read()

            # Use the documented API format
            payload = {
                "query": f"Please analyze this Pulumi Go code for best practices and potential issues:\n\n```go\n{code_content}\n```",
                "state": {
                    "client": {
                        "cloudContext": {
                            "orgId": "talkitdoit-org",
                            "url": "https://app.pulumi.com"
                        }
                    }
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload
                ) as response:
                    response_text = await response.text()
                    try:
                        result = json.loads(response_text)
                        # Extract the analysis from the response
                        for message in result.get("messages", []):
                            if message.get("role") == "assistant" and message.get("kind") == "response":
                                return json.dumps({
                                    "status": "success",
                                    "analysis": message.get("content", "No analysis provided")
                                })
                        
                        return json.dumps({
                            "status": "error",
                            "message": "No analysis found in response"
                        })
                    except json.JSONDecodeError:
                        return json.dumps({
                            "status": "error",
                            "message": f"Failed to parse response: {response_text[:200]}..."
                        })

        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to analyze code: {str(e)}"
            })

    async def process(self, message: str) -> str:
        if message.lower() == "test connection":
            return await self.test_connection()
        elif "analyze" in message.lower():
            project_name = message.split()[-1]
            return await self.analyze_code(project_name)
        return "Unknown command"

class PlatformOrchestrator:
    def __init__(self):
        self.code_generator = CodeGeneratorAgent()
        self.infrastructure = InfrastructureAgent()
        self.gitops = GitOpsAgent()
        self.deployment = DeploymentAgent()
        self.copilot = PulumiCopilotAgent()
    
    async def create_new_project(self, template: str, project_name: str) -> str:
        try:
            # Create directory and initialize project
            os.makedirs(project_name, exist_ok=True)
            
            # First create the Pulumi project
            commands = [
                f"pulumi new {template} -s talkitdoit-org/{project_name}/dev --yes --force"
            ]
            
            for cmd in commands:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=project_name
                )
                print(f"Executing: {cmd}")
                print(f"Output: {result.stdout}")
                if result.returncode != 0:
                    raise Exception(f"Command failed: {cmd}\nError: {result.stderr}")

            # Create www directory if it doesn't exist
            www_dir = Path(project_name) / "www"
            www_dir.mkdir(exist_ok=True)

            # Create custom index.html with dark mode
            custom_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>> Hello, world!</title>
    <style>
        body {
            background-color: #1a1a1a;
            color: #e0e0e0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            line-height: 1.6;
        }

        h1 {
            color: #8b5cf6;
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }

        p {
            font-size: 1.2rem;
        }

        a {
            color: #a78bfa;
            text-decoration: none;
            transition: color 0.3s ease;
        }

        a:hover {
            color: #c4b5fd;
            text-decoration: underline;
        }

        .container {
            text-align: center;
            padding: 2rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>> Hello, world! 👋</h1>
        <p>Deployed by TALKITDOIT with 💜 from <a href="https://pulumi.com/">pulumi</a>.</p>
    </div>
</body>
</html>'''

            # Write the custom index.html
            index_path = www_dir / "index.html"
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(custom_html)
            
            return "Project created successfully with custom dark mode template"
        except Exception as e:
            raise Exception(f"Failed to create project: {str(e)}")

    async def process_request(self, app_spec: ApplicationSpec, action: str = "deploy") -> List[str]:
        responses = []
        
        if action == "destroy":
            destroy_response = await self.deployment.communicate(f"Destroy {app_spec.name}")
            responses.append(destroy_response)
        else:
            responses.append("Using newly created Pulumi project")
            
            # Continue with deployment
            await self.gitops.create_repository(app_spec)
            await self.gitops.commit_code(app_spec, "", "")
            deploy_response = await self.deployment.communicate(f"Deploy {app_spec.name}")
            responses.append(deploy_response)
        
        return responses 
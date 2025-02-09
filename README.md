# AI-Powered Platform Engineering Assistant 🤖

Exploring the potential for a smart assistant that helps developers create, deploy, and manage infrastructure, and for this demo purpose, a static website on Azure using Pulumi and Go. Built with Python as our AI agent classes and interacting with Pulumi Copilot via the API, this project showcases the integration of AI with modern cloud infrastructure.

This is not for production use, it is a demo project to showcase the potential of AI-powered platform engineering and we can develop this further in future videos, please leave a comment if you would like to see this developed further, thank you.

## 🔑 Required Accounts & Tools
##### I used the following accounts and tools for this demo:

<details>
<summary><b>Pulumi Cloud Account</b></summary>
Create a free account at <a href="https://app.pulumi.com/signup">app.pulumi.com/signup</a>
</details>

<details>
<summary><b>Azure Account</b></summary>
Set up your cloud environment at <a href="https://portal.azure.com/">portal.azure.com</a>
</details>

<details>
<summary><b>GitHub Account</b></summary>
Sign up at <a href="https://github.com/">github.com</a> (needed for future videos)
</details>

<details>
<summary><b>Python Environment</b></summary>
Download and install Python from <a href="https://www.python.org/downloads/">python.org/downloads</a>
</details>

<details>
<summary><b>Development Environment</b></summary>

- **Operating System**: macOS Sequoia 15.1
- **Terminal**: Ghostty v1.1.0
</details>


## 🚀 Quick Start


1. **Setup Prerequisites**
   ```bash
   # Create a directory for the project
   mkdir talkitdoit-demo-go-app
   cd talkitdoit-demo-go-app

   # Create a virtual environment
   python -m venv talkitdoit-demo-go-app

   # Activate the virtual environment
   source .venv/bin/activate

   # Install Python dependencies
   pip install -r requirements.txt

   # Login to Azure and get your subscription ID
   az login
   az account show --query id -o tsv

   # Create a service principal and get credentials
   az ad sp create-for-rbac --role Contributor \
                           --scopes /subscriptions/YOUR_SUBSCRIPTION_ID \
                           --name PulumiDeployment \
                           --query "{ clientId: appId, clientSecret: password, tenantId: tenant }"

   # The above command will output JSON similar to:
   # {
   #   "clientId": "...",
   #   "clientSecret": "...",
   #   "tenantId": "..."
   # }

   # Set up your environment variables in .env file
   AZURE_CREDENTIALS={"clientId": "...", "clientSecret": "...", "tenantId": "...", "subscriptionId": "..."}
   PULUMI_ACCESS_TOKEN=your_pulumi_token
   GITHUB_TOKEN=your_github_token
   ```

2. **Run the Assistant**
   ```bash
   python chat_interface.py
   ```

   ```bash
   🤖 Welcome to the AI Platform Engineering Assistant!
    -----------------------------------------------------
    I can help you create and manage static websites on Azure.
    You can ask me to:
      • Create a simple Go app for a static website
      • Deploy your application
      • Destroy your application

    What would you like to do? (type 'exit' to quit)
    -----------------------------------------------------
   ```

3. **Create and Deploy a Website**
   ```bash
   # When prompted, type:
   Create a static website

   # Enter a project name when asked
   my-demo-site

   # Review the AI analysis
   # Confirm deployment when ready
   yes
   ```

4. **View Results**
   - Check the `analysis/` directory for AI analysis
   - Access your website via the provided Azure URL
   - Review infrastructure in Pulumi Console

5. **Access the Website**

   ```bash
   # Select the originURL and paste in your browser:
   Deployment responds: {"status": "success", "message": "Deployment completed successfully", "outputs": {"cdnHostname": "endpointbd284f52.azureedge.net", "cdnURL": "http://endpointbd284f52.azureedge.net", "originHostname": "accountcafd690b.z13.web.core.windows.net", "originURL": "https://accountcafd690b.z13.web.core.windows.net/"}}
   ```

5. **Destroy the Website**
   ```bash
   # When prompted, type:
   Destroy the website
   ```

   ```bash
   # You will see this response:
   Deployment responds: {"status": "success", "message": "Application successfully destroyed"}

    Assistant: I've destroyed your application. Here's what I did:
    ✨ Application successfully destroyed
   ```

## 🌟 Key Features

- Create static website using a pulumi template, by using a simple chat interface
- AI-powered code analysis and suggestions
- Automated deployment to Azure
- Infrastructure as Code using Pulumi
- GitOps workflow integration (future video)

## 🔄 How It Works

The system follows this flow:

1. User interacts with Chat Interface
2. Platform Orchestrator coordinates actions
3. Code Generator creates project structure
4. Pulumi Copilot analyzes code
5. GitOps Agent manages repository (future video)
6. Deployment Agent handles Azure deployment

## 🛠️ Component Overview

1. **Chat Interface** (`chat_interface.py`)
   - Handles user interaction
   - Manages conversation flow
   - Tracks project state

2. **Platform Orchestrator** (`idea_code.py`)
   - Coordinates between different agents
   - Manages project lifecycle
   - Handles error scenarios

3. **Pulumi Copilot** (`pulumi_co_pilot.py`)
   - AI-powered code analysis
   - Infrastructure suggestions
   - Best practices recommendations

## 🔍 Typical Flow

1. User requests to create a static website
2. Assistant creates a new Pulumi project using Go template
3. Pulumi Copilot analyzes the infrastructure code
4. Code is committed to GitHub repository (future video)
5. Infrastructure is deployed to Azure
6. User gets deployment URLs and status

## 🔐 Prerequisites

- Azure Account
- Pulumi Account
- GitHub Account
- Required Environment Variables:
  - `AZURE_CREDENTIALS`
  - `PULUMI_ACCESS_TOKEN`
  - `GITHUB_TOKEN`

## 📁 Project Structure

- `chat_interface.py` - Main chat interface and user interaction
- `idea_code.py` - Core platform orchestration and agents
- `pulumi_co_pilot.py` - AI-powered code analysis integration
- `project_name_we_create/` - Generated project template
  - `main.go` - Pulumi infrastructure code
  - `www/` - Website assets
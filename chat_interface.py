import asyncio
from typing import List
import os
import sys
import json
from pathlib import Path
import datetime

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from idea_code import ApplicationSpec, PlatformOrchestrator
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

class AIChatInterface:
    """
    Main interface for user interaction with the platform
    Handles conversation flow and command processing
    """
    def __init__(self):
        self.orchestrator = PlatformOrchestrator()
        self.conversation_history: List[str] = []  # Tracks chat history
        self.current_project = None  # Tracks active project
        self.awaiting_project_name = False  # State flag for project name input
        self.awaiting_deployment_confirmation = False  # State flag for deployment confirmation
        self.analysis_dir = Path("analysis")  # Directory to store analysis files
        self.analysis_dir.mkdir(exist_ok=True)  # Create directory if it doesn't exist

    async def save_analysis_to_file(self, project_name: str, analysis: str):
        """Save Pulumi Copilot analysis to a markdown file"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{project_name}_analysis_{timestamp}.md"
        filepath = self.analysis_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Pulumi Copilot Analysis for {project_name}\n\n")
            f.write(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Analysis\n\n")
            f.write(analysis)

    async def process_message(self, user_message: str) -> str:
        """
        Main message processing pipeline:
        1. Tracks conversation history
        2. Handles different command types:
           - Project creation
           - Deployment
           - Destruction
           - General queries
        3. Manages conversation state
        4. Returns appropriate responses
        """
        self.conversation_history.append(f"User: {user_message}")
        message_lower = user_message.lower()

        # Handle project name input if we're waiting for it
        if self.awaiting_project_name:
            self.awaiting_project_name = False
            project_name = user_message.strip().replace(" ", "-").lower()
            try:
                creation_response = await self.orchestrator.create_new_project("static-website-azure-go", project_name)
                self.current_project = project_name
                
                # Analyze the code with Pulumi Copilot first
                analysis_response = await self.orchestrator.copilot.communicate(f"Analyze {project_name}")
                try:
                    analysis_data = json.loads(analysis_response)
                    if analysis_data.get("status") == "success":
                        # Save analysis to file
                        await self.save_analysis_to_file(
                            project_name, 
                            analysis_data.get("analysis", "No analysis provided")
                        )
                        
                        self.awaiting_deployment_confirmation = True
                        response = "\n".join([
                            f"I've created a new static website project '{project_name}' using Pulumi's Azure Go template.",
                            "\n🤖 Pulumi Copilot Analysis:",
                            analysis_data.get("analysis", "No analysis provided"),
                            "\nAnalysis has been saved to the 'analysis' directory.",
                            "\nWould you like me to proceed with deployment? (yes/no)"
                        ])
                    else:
                        response = "\n".join([
                            f"I've created the project '{project_name}', but the code analysis failed:",
                            analysis_data.get("message", "Unknown error"),
                            "Would you like to proceed with deployment anyway? (yes/no)"
                        ])
                        self.awaiting_deployment_confirmation = True
                except json.JSONDecodeError:
                    response = f"Project created, but failed to parse the code analysis. Would you like to proceed with deployment? (yes/no)"
                    self.awaiting_deployment_confirmation = True
            except Exception as e:
                response = f"Sorry, I encountered an error while creating the project: {str(e)}"

        # Handle deployment confirmation
        elif self.awaiting_deployment_confirmation and any(word in message_lower for word in ["yes", "sure", "okay"]):
            self.awaiting_deployment_confirmation = False
            app_spec = ApplicationSpec(
                name=self.current_project,
                description="A static website with Azure CDN",
                framework="go",
                target_framework="go",
                container_port=80
            )
            
            try:
                responses = await self.orchestrator.process_request(app_spec, "deploy")
                try:
                    deploy_data = json.loads(responses[-1])
                    if deploy_data.get("status") == "success":
                        response = "\n".join([
                            "I've deployed your application. Here's what happened:",
                            *[f"- {r}" for r in responses[:-1]],
                            f"✨ {deploy_data.get('message', 'Deployment completed successfully')}"
                        ])
                    else:
                        response = "\n".join([
                            "Deployment attempt completed. Here's what happened:",
                            *[f"- {r}" for r in responses]
                        ])
                except json.JSONDecodeError:
                    response = "\n".join([
                        "Deployment completed. Here's what happened:",
                        *[f"- {r}" for r in responses]
                    ])
            except Exception as e:
                response = f"Sorry, I encountered an error while deploying: {str(e)}"

        # Handle deployment command
        elif "deploy" in message_lower and self.current_project:
            app_spec = ApplicationSpec(
                name=self.current_project,
                description="A static website with Azure CDN",
                framework="go",
                target_framework="go",
                container_port=80
            )
            try:
                responses = await self.orchestrator.process_request(app_spec, "deploy")
                try:
                    deploy_data = json.loads(responses[-1])
                    if deploy_data.get("status") == "success":
                        response = "\n".join([
                            "I've deployed your application. Here's what happened:",
                            *[f"- {r}" for r in responses[:-1]],
                            f"✨ {deploy_data.get('message', 'Deployment completed successfully')}"
                        ])
                    else:
                        response = "\n".join([
                            "Deployment attempt completed. Here's what happened:",
                            *[f"- {r}" for r in responses]
                        ])
                except json.JSONDecodeError:
                    response = "\n".join([
                        "Deployment completed. Here's what happened:",
                        *[f"- {r}" for r in responses]
                    ])
            except Exception as e:
                response = f"Sorry, I encountered an error while deploying: {str(e)}"

        # Handle destroy request
        elif "destroy" in message_lower or "remove" in message_lower or "delete" in message_lower:
            if not self.current_project:
                response = "There's no active project to destroy. Would you like to create a new static website project?"
            else:
                app_spec = ApplicationSpec(
                    name=self.current_project,
                    description="A static website with Azure CDN",
                    framework="go",
                    target_framework="go",
                    container_port=80
                )
                try:
                    responses = await self.orchestrator.process_request(app_spec, "destroy")
                    try:
                        destroy_data = json.loads(responses[-1])
                        if destroy_data.get("status") == "success":
                            response = "\n".join([
                                "I've destroyed your application. Here's what I did:",
                                *[f"- {r}" for r in responses[:-1]],
                                f"✨ {destroy_data.get('message', 'Application destroyed successfully')}"
                            ])
                            self.current_project = None
                        else:
                            response = "\n".join([
                                "I've attempted to destroy your application. Here's what happened:",
                                *[f"- {r}" for r in responses]
                            ])
                    except json.JSONDecodeError:
                        response = "\n".join([
                            "I've attempted to destroy your application. Here's what happened:",
                            *[f"- {r}" for r in responses]
                        ])
                except Exception as e:
                    response = f"Sorry, I encountered an error while destroying the application: {str(e)}"

        # Handle create static website request
        elif "create" in message_lower and "static website" in message_lower:
            self.awaiting_project_name = True
            response = "What would you like to name your project? (Please provide a simple name, it will be converted to lowercase with hyphens)"

        # Handle initial greeting or unknown commands
        else:
            if self.current_project:
                response = (
                    f"I can help you manage your project '{self.current_project}'. "
                    "You can ask me to:\n"
                    "• Deploy your application\n"
                    "• Destroy your application\n"
                    "Or create a new static website"
                )
            else:
                response = (
                    "I can help you create and manage static websites on Azure. "
                    "Would you like me to create a simple Go app for a static website? "
                    "Just let me know!"
                )

        self.conversation_history.append(f"Assistant: {response}")
        return response

async def main():
    """
    Main entry point for the chat interface:
    1. Initializes chat interface
    2. Displays welcome message
    3. Runs main interaction loop
    4. Handles user input and displays responses
    """
    chat = AIChatInterface()
    
    print("\n🤖 Welcome to the AI Platform Engineering Assistant!")
    print("-----------------------------------------------------")
    print("I can help you create and manage static websites on Azure.")
    print("You can ask me to:")
    print("  • Create a simple Go app for a static website")
    print("  • Deploy your application")
    print("  • Destroy your application")
    print("\nWhat would you like to do? (type 'exit' to quit)")
    print("-----------------------------------------------------")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            print("\nGoodbye! Have a great day! 👋")
            break
            
        response = await chat.process_message(user_input)
        print(f"\nAssistant: {response}")

if __name__ == "__main__":
    asyncio.run(main()) 
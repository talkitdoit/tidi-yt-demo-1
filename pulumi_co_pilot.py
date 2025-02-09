import requests
import json

class PulumiCopilotClient:
    """Client for interacting with Pulumi's AI Copilot API"""
    def __init__(self, access_token, org_id):
        """Initialize client with authentication and organization details"""
        self.base_url = "https://api.pulumi.com"
        self.headers = {
            "Authorization": f"token {access_token}",
            "Content-Type": "application/json"
        }
        self.org_id = org_id

    def start_conversation(self, query, url):
        """
        Initiates a new conversation with Pulumi Copilot
        Args:
            query: Initial question or prompt
            url: Pulumi stack URL for context
        Returns:
            JSON response from Copilot API
        """
        endpoint = f"{self.base_url}/api/ai/chat/preview"
        
        payload = {
            "query": query,
            "state": {
                "client": {
                    "cloudContext": {
                        "orgId": self.org_id,
                        "url": url
                    }
                }
            }
        }
        
        response = requests.post(endpoint, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    def continue_conversation(self, query, url, conversation_id):
        """
        Continues an existing conversation thread
        Args:
            query: Follow-up question
            url: Pulumi stack URL
            conversation_id: ID of existing conversation
        Returns:
            JSON response with Copilot's answer
        """
        endpoint = f"{self.base_url}/api/ai/chat/preview"
        
        payload = {
            "query": query,
            "state": {
                "client": {
                    "cloudContext": {
                        "orgId": self.org_id,
                        "url": url
                    }
                }
            },
            "conversationId": conversation_id
        }
        
        response = requests.post(endpoint, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

# Example usage:
def main():
    # Replace these with your actual values
    ACCESS_TOKEN = "your_access_token"
    ORG_ID = "your_org_id"
    
    client = PulumiCopilotClient(ACCESS_TOKEN, ORG_ID)
    
    # Start a new conversation
    url = "https://app.pulumi.com/myorg/project1/dev/updates/4"  # Replace with your actual URL
    query = "Analyze this code and suggest improvements"
    
    try:
        # Start conversation
        response = client.start_conversation(query, url)
        conversation_id = response["conversationId"]
        
        # Print the assistant's response
        for message in response["messages"]:
            if message["role"] == "assistant" and message["kind"] == "response":
                print("Assistant:", message["content"])
        
        # Continue the conversation if needed
        follow_up_query = "Can you explain more about the first suggestion?"
        follow_up_response = client.continue_conversation(
            follow_up_query, 
            url, 
            conversation_id
        )
        
        # Print the follow-up response
        for message in follow_up_response["messages"]:
            if message["role"] == "assistant" and message["kind"] == "response":
                print("Assistant:", message["content"])
                
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
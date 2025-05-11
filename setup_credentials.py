import os
import json
import sys

def setup_credentials():
    """Helper script to set up Google Cloud credentials"""
    
    # Create secrets directory if it doesn't exist
    secrets_dir = os.path.join(os.path.dirname(__file__), "secrets")
    os.makedirs(secrets_dir, exist_ok=True)
    
    credentials_path = os.path.join(secrets_dir, "google-credentials.json")
    
    if os.path.exists(credentials_path):
        print(f"Credentials file already exists at: {credentials_path}")
        return
    
    print("""
    To use Google Cloud Text-to-Speech, you need to:
    
    1. Go to the Google Cloud Console: https://console.cloud.google.com/
    2. Create a new project or select an existing one
    3. Enable the Text-to-Speech API for your project
    4. Create a service account:
       - Go to "IAM & Admin" > "Service Accounts"
       - Click "Create Service Account"
       - Give it a name (e.g., "voice-synthesis")
       - Grant it the "Cloud Text-to-Speech API User" role
       - Click "Create and Continue"
       - Click "Done"
    5. Create a key for the service account:
       - Find your service account in the list
       - Click the three dots menu (⋮) on the right
       - Select "Manage keys"
       - Click "Add Key" > "Create new key"
       - Choose JSON format
       - Click "Create"
       - The key file will be downloaded automatically
    
    Once you have the JSON key file, paste its contents below and press Enter twice:
    """)
    
    credentials = []
    while True:
        try:
            line = input()
            if not line:
                break
            credentials.append(line)
        except EOFError:
            break
    
    if not credentials:
        print("No credentials provided. Exiting.")
        sys.exit(1)
    
    try:
        # Validate JSON
        json.loads("\n".join(credentials))
        
        # Save credentials
        with open(credentials_path, "w") as f:
            f.write("\n".join(credentials))
        
        print(f"\nCredentials saved to: {credentials_path}")
        print("\nYou can now run the voice synthesis service!")
        
    except json.JSONDecodeError:
        print("Invalid JSON format. Please try again.")
        sys.exit(1)

if __name__ == "__main__":
    setup_credentials() 
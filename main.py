import os
import sys
from dotenv import load_dotenv
from msreg_client import MotorsportRegClient



def main():
    print("MotorsportReg Member Manager")
    print("----------------------------")

    # Load environment variables from .env file
    load_dotenv()
    
    # Organization ID from environment
    ORG_ID = os.environ.get("MSR_ORG_ID")

    import json
    
    # specific credentials
    username = os.environ.get("MSR_USERNAME")
    password = os.environ.get("MSR_PASSWORD")

    if not username:
        username = input("Enter your MotorsportReg Email/Username: ")
    
    if not password:
        import getpass
        password = getpass.getpass("Enter your MotorsportReg Password: ")

    if not username or not password:
        print("Error: Username and password are required.")
        sys.exit(1)

    client = MotorsportRegClient(username, password, ORG_ID)

    print(f"\nConnecting to Organization ID: {ORG_ID}...")
    
    print("Fetching members...")
    members_data = client.get_members()

    if members_data:
        # Depending on the exact structure of the JSON response, we parse it.
        # Usually MSR returns a root element like {"response": {"members": [...]}} or just a list.
        # We will dump the raw response first for debugging/verification.
        
        # Simple pretty print of the structure
        # Attempt to list basic info if structure matches standard conventions
        # Structure observed: {"response": {"members": [...], "recordset": {...}}}
        response_data = members_data.get('response', {})
        print("DEBUG: response_data content:")
        print(json.dumps(response_data, indent=2))
        
        # Try to find the list of members
        if 'members' in response_data:
            members = response_data['members']
        elif 'payload' in response_data:
             payload = response_data['payload']
             if 'members' in payload:
                 members = payload['members']
             elif 'member' in payload:
                 members = payload['member']
                 if isinstance(members, dict):
                     members = [members]
        else:
            # Fallback for unexpected structures
            members = []
        
        if members:
            # Collect and save all available fields
            all_keys = set()
            for m in members:
                all_keys.update(m.keys())
            
            with open('available_fields.txt', 'w') as f:
                for key in sorted(all_keys):
                    f.write(f"{key}\n")
            
            print(f"\nFound {len(members)} members. Available fields written to 'available_fields.txt'.")
            for m in members:
                # Extract fields safely
                f_name = m.get('firstName', 'N/A')
                l_name = m.get('lastName', 'N/A')
                member_id = m.get('memberId', 'N/A')
                unique_id = m.get('uniqueId', 'N/A')
                member_end = m.get('memberEnd', 'N/A')
                print(f"{f_name},{l_name},{member_id},{unique_id},{member_end}")
        else:
            print("\nNo members found or unexpected response format.")
            
    else:
        print("\nFailed to retrieve data.")

if __name__ == "__main__":
    main()
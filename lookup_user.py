import os
import sys
import json
from dotenv import load_dotenv
from msreg_client import MotorsportRegClient



def get_all_members(client):
    print("Fetching member list from MotorsportReg...")
    members_data = client.get_members()
    
    if not members_data:
        print("Failed to retrieve data.")
        return []

    # Parsing logic from main.py
    response_data = members_data.get('response', {})
    
    members = []
    if 'members' in response_data:
        members = response_data['members']
    elif 'payload' in response_data:
        payload = response_data['payload']
        if 'members' in payload:
            members = payload['members']
        elif 'member' in payload:
            m = payload['member']
            if isinstance(m, dict):
                members = [m]
    
    return members

def search_members(members, query):
    query = query.lower().strip()
    results = []
    
    for m in members:
        # Searchable fields
        f_name = m.get('firstName', '').lower()
        l_name = m.get('lastName', '').lower()
        email = m.get('email', '').lower()
        member_id = str(m.get('memberId', '')).lower()
        unique_id = str(m.get('uniqueId', '')).lower()
        guid = m.get('id', '').lower()
        
        # Check for match (partial match for names/email, exact for IDs usually preferable but partial is ok for broad search)
        if (query in f_name or 
            query in l_name or 
            query in email or 
            query == member_id or 
            query == unique_id or
            query == guid):
            results.append(m)
            
    return results

def print_member_details(member):
    print("\n" + "="*40)
    print(f"Details for user: {member.get('firstName', '')} {member.get('lastName', '')}")
    print("="*40)
    
    # Sort keys for consistent output
    for key in sorted(member.keys()):
        val = member[key]
        if isinstance(val, dict):
            val = json.dumps(val) # simple string rep for dicts like 'image'
        print(f"{key}: {val}")
    print("="*40 + "\n")

def main():
    print("MotorsportReg User Lookup Tool")
    print("------------------------------")

    # Load environment variables
    load_dotenv()
    
    # Organization ID from environment
    ORG_ID = os.environ.get("MSR_ORG_ID")

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
    
    # Cache members in memory
    members = get_all_members(client)
    print(f"Loaded {len(members)} members.")
    
    while True:
        try:
            query = input("\nEnter search term (Name, Email, ID) or 'q' to quit: ")
            if query.lower() in ('q', 'quit', 'exit'):
                break
            
            if not query:
                continue
                
            results = search_members(members, query)
            
            if not results:
                print("No matching members found.")
            elif len(results) == 1:
                selected_member = results[0]
                print_member_details(selected_member)
                action = input("Options: (u)pdate Member ID, (b)ack to search: ").lower()
                if action == 'u':
                     new_id = input(f"Enter new Member ID for {selected_member.get('firstName')} (current: {selected_member.get('memberId')}): ").strip()
                     if new_id:
                         confirm = input(f"Are you sure you want to set Member ID to '{new_id}'? (y/n): ").lower()
                         if confirm == 'y':
                             guid = selected_member.get('id')
                             if guid:
                                 print(f"Updating member {guid}...")
                                 update_payload = {"memberId": new_id}
                                 response = client.update_member(guid, update_payload)
                                 if response:
                                     print("Update successful!")
                                     selected_member['memberId'] = new_id
                                     print_member_details(selected_member)
                                 else:
                                     print("Update failed.")
                             else:
                                  print("Error: Could not find Member GUID (id field).")
            else:
                print(f"\nFound {len(results)} matches:")
                for i, m in enumerate(results):
                    print(f"{i+1}. {m.get('firstName', '')} {m.get('lastName', '')} (ID: {m.get('memberId', '')}, Email: {m.get('email', '')})")
                
                selection = input("\nEnter number to view details, or Press Enter to search again: ")
                if selection.isdigit():
                    idx = int(selection) - 1
                    if 0 <= idx < len(results):
                        selected_member = results[idx]
                        print_member_details(selected_member)
                        
                        action = input("Options: (u)pdate Member ID, (b)ack to search: ").lower()
                        if action == 'u':
                             new_id = input(f"Enter new Member ID for {selected_member.get('firstName')} (current: {selected_member.get('memberId')}): ").strip()
                             if new_id:
                                 confirm = input(f"Are you sure you want to set Member ID to '{new_id}'? (y/n): ").lower()
                                 if confirm == 'y':
                                     # Use the 'id' field which seems to be the GUID for the update endpoint
                                     guid = selected_member.get('id')
                                     if guid:
                                         print(f"Updating member {guid}...")
                                         # Construct update payload
                                         update_payload = {"memberId": new_id}
                                         response = client.update_member(guid, update_payload)
                                         if response:
                                             print("Update successful!")
                                             # Optionally refresh the local member object
                                             selected_member['memberId'] = new_id
                                             print_member_details(selected_member)
                                         else:
                                             print("Update failed.")
                                     else:
                                         print("Error: Could not find Member GUID (id field).")
                        
                    else:
                        print("Invalid selection.")
        except KeyboardInterrupt:
            print("\nExiting...")
            break

if __name__ == "__main__":
    main()

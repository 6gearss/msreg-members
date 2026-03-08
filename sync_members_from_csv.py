import csv
import os
import sys
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv
from msreg_client import MotorsportRegClient

# Setup logging
if not os.path.exists('logs'):
    os.makedirs('logs')
log_filename = f"logs/member_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Configure logging to file always, and console determined by verbosity later?
# For now, we'll keep the basic config but control what gets logged via flags
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)

def get_all_members(client):
    logging.info("Fetching member list from MotorsportReg...")
    members_data = client.get_members()
    
    if not members_data:
        logging.error("Failed to retrieve data from API.")
        return {}

    response_data = members_data.get('response', {})
    
    raw_members = []
    if 'members' in response_data:
        raw_members = response_data['members']
    elif 'payload' in response_data:
        payload = response_data['payload']
        if 'members' in payload:
            raw_members = payload['members']
        elif 'member' in payload:
            m = payload['member']
            if isinstance(m, dict):
                raw_members = [m]
    
    # Create a dictionary keyed by uniqueId (as string) for fast lookup
    members_map = {}
    for m in raw_members:
        uid = str(m.get('uniqueId', '')).strip()
        if uid:
            members_map[uid] = m
            
    logging.info(f"Loaded {len(members_map)} members indexed by uniqueId.")
    return members_map

def process_csv(filename, client, members_map, verbose=False):
    logging.info(f"Processing CSV file: {filename}")
    
    if not os.path.exists(filename):
        logging.error(f"CSV file not found: {filename}")
        return

    csv_unique_ids = set()

    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        row_count = 0
        update_count = 0
        error_count = 0
        
        for row in reader:
            row_count += 1
            if not row or len(row) < 4:
                if verbose:
                    logging.warning(f"Row {row_count}: Skipped invalid row: {row}")
                continue
            
            try:
                f_name = row[0].strip()
                l_name = row[1].strip()
                csv_member_id = row[2].strip()
                csv_unique_id = row[3].strip()
                
                csv_unique_ids.add(csv_unique_id)
                
                # Check 1: Find user by uniqueId
                if csv_unique_id not in members_map:
                    if verbose:
                        logging.warning(f"Row {row_count}: User not found API with uniqueId '{csv_unique_id}' ({f_name} {l_name}).")
                    error_count += 1
                    continue
                
                member = members_map[csv_unique_id]
                api_member_id = str(member.get('memberId', '')).strip()
                member_guid = member.get('id')
                
                if not member_guid:
                    logging.error(f"Row {row_count}: Member {csv_unique_id} found but has no GUID (id). Cannot update.")
                    error_count += 1
                    continue

                if not csv_member_id:
                     if verbose:
                        logging.info(f"Row {row_count}: CSV memberId is empty for {f_name} {l_name}. Skipping update.")
                     continue
                
                if api_member_id != csv_member_id:
                    logging.info(f"Row {row_count}: Mismatch for ({f_name} {l_name} [{csv_unique_id}]). API: '{api_member_id}' -> CSV: '{csv_member_id}'. Updating...")
                    
                    update_payload = {"memberId": csv_member_id}
                    response = client.update_member(member_guid, update_payload)
                    
                    if response:
                        logging.info(f"Row {row_count}: Update successful.")
                        member['memberId'] = csv_member_id
                        update_count += 1
                    else:
                        logging.error(f"Row {row_count}: Update FAILED via API.")
                        error_count += 1
                else:
                    if verbose:
                        logging.info(f"Row {row_count}: MemberId matches ({api_member_id}). No action needed.")
                    
            except Exception as e:
                logging.error(f"Row {row_count}: Error processing row: {e}")
                error_count += 1

        # Identify members in API but not in CSV
        api_unique_ids = set(members_map.keys())
        missing_in_csv = api_unique_ids - csv_unique_ids
        
        logging.info("="*30)
        logging.info(f"Processing complete.")
        logging.info(f"Total rows in CSV: {row_count}")
        logging.info(f"Updates performed: {update_count}")
        logging.info(f"Errors/Skips: {error_count}")
        
        if missing_in_csv:
            logging.info("="*30)
            logging.info(f"Clean-up Audit: Found {len(missing_in_csv)} members in API but NOT in CSV.")
            logging.info("Copy the lines below to your Google Sheet:")
            print("-" * 30)
            # Table Header
            print("firstName,lastName,memberId,uniqueId,memberEnd")
            for uid in missing_in_csv:
                m = members_map[uid]
                f_name = m.get('firstName', '')
                l_name = m.get('lastName', '')
                m_id = m.get('memberId', '')
                m_end = m.get('memberEnd', '')
                print(f"{f_name},{l_name},{m_id},{uid},{m_end}")
            print("-" * 30)
        else:
            logging.info("Clean-up Audit: All API members were found in the CSV.")

        logging.info("="*30)
        logging.info(f"Log saved to: {log_filename}")

def main():
    parser = argparse.ArgumentParser(description="Sync members from CSV to MotorsportReg")
    parser.add_argument("csv_file", nargs="?", help="Path to the CSV file to process")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging (shows 'No action needed' messages)")
    
    args = parser.parse_args()

    # Load environment variables
    load_dotenv()
    
    # Organization ID from environment
    ORG_ID = os.environ.get("MSR_ORG_ID")
    username = os.environ.get("MSR_USERNAME")
    password = os.environ.get("MSR_PASSWORD")

    # Only prompt for credentials if not in env
    if not username:
        username = input("Enter your MotorsportReg Email/Username: ")
    
    if not password:
        try:
            import getpass
            password = getpass.getpass("Enter your MotorsportReg Password: ")
        except ImportError:
            password = input("Enter your MotorsportReg Password: ")

    if not username or not password:
        print("Error: Username and password are required.")
        sys.exit(1)
        
    # Determine CSV file
    if args.csv_file:
        csv_file = args.csv_file
    else:
        # Fallback to interactive prompt if not provided arg
        print("Tip: You can pass the filename as an argument: python sync_members_from_csv.py members.csv")
        csv_inp = input("Enter the path to the CSV file to process (default: members.csv): ").strip()
        csv_file = csv_inp if csv_inp else "members.csv"

    print(f"Using file: {csv_file}")
    if args.verbose:
        print("Verbose logging enabled.")

    client = MotorsportRegClient(username, password, ORG_ID)
    
    members_map = get_all_members(client)
    
    if members_map:
        process_csv(csv_file, client, members_map, verbose=args.verbose)

if __name__ == "__main__":
    main()

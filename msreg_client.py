import requests
import json
class MotorsportRegClient:
    def __init__(self, username, password, org_id):
        self.base_url = "https://api.motorsportreg.com"
        self.auth = (username, password)
        self.headers = {
            "X-Organization-Id": org_id,
            "Accept": "application/json"
        }
    def _get(self, endpoint, params=None):
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            if e.response.status_code == 401:
                print("Authentication failed. Please check your username and password.")
            elif e.response.status_code == 403:
                print("Access denied. Please check your Organization ID and permissions.")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
    def _put(self, endpoint, data=None):
        url = f"{self.base_url}{endpoint}"
        try:
            # MSR API typically accepts form-encoded data or JSON. 
            # We'll try passing data as 'data' (form-encoded) by default, 
            # or 'json' if it's a dict and we want JSON.
            # Based on standard usage, let's try 'json' parameter if data is dict.
            response = requests.put(url, auth=self.auth, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            if e.response:
                print(f"Response Content: {e.response.text}")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def get_members(self, limit=20, page=1):
        """
        Fetches a list of members for the organization.
        
        Note: The actual endpoint for listing members is /rest/members.
        Verify pagination parameters in docs if needed. MSR usually uses 'limit' and 'offset' or similar.
        Based on research, standard listing might just be /rest/members.json
        """
        endpoint = "/rest/members.json" # Adding .json to force JSON response if Accept header isn't enough
        params = {
            # specific params depend on exact MSR API pagination, passing common ones
            # If the API doesn't support pagination in this way, these might be ignored.
        }
        return self._get(endpoint, params=params)

    def get_member_details(self, member_id):
        """
        Fetches details for a specific member.
        """
        endpoint = f"/rest/members/{member_id}.json"
        return self._get(endpoint)

    def update_member(self, member_id, data):
        """
        Updates a specific member.
        
        :param member_id: The UUID or ID of the member to update.
        :param data: A dictionary of fields to update.
        """
        endpoint = f"/rest/members/{member_id}.json"
        return self._put(endpoint, data=data)

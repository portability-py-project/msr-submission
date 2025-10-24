import json
import requests
from datetime import datetime, timedelta
import hashlib


class APITokenManager:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.expires_at = None
        
    def authenticate(self, username, password):
        """Authenticate and get API token"""
        auth_data = {
            'username': username,
            'password': hashlib.sha256(password.encode()).hexdigest()
        }
        
        response = requests.post(f"{self.base_url}/auth", json=auth_data)
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get('token')
            self.expires_at = datetime.now() + timedelta(hours=data.get('expires_in', 1))
            return True
        return False
    
    def is_token_valid(self):
        """Check if current token is still valid"""
        if not self.token or not self.expires_at:
            return False
        return datetime.now() < self.expires_at
    
    def get_headers(self):
        """Get authorization headers for API calls"""
        if self.is_token_valid():
            return {'Authorization': f'Bearer {self.token}'}
        return {}
    
    def make_request(self, endpoint, method='GET', data=None):
        """Make authenticated API request"""
        if not self.is_token_valid():
            raise Exception("Token expired or invalid")
        
        headers = self.get_headers()
        headers['Content-Type'] = 'application/json'
        
        url = f"{self.base_url}{endpoint}"
        
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return response.json() if response.status_code == 200 else None


if __name__ == "__main__":
    api = APITokenManager("https://api.example.com")
    
    if api.authenticate("user123", "password"):
        users = api.make_request("/users")
        print(f"Retrieved {len(users)} users")
    else:
        print("Authentication failed")
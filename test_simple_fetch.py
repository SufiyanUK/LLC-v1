"""
The SIMPLEST possible fetch - just get 1 OpenAI employee
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('API_KEY')

if not api_key:
    print("No API key found")
    exit()

print("\nFetching 1 employee from OpenAI - SIMPLEST QUERY POSSIBLE")
print("="*60)

url = "https://api.peopledatalabs.com/v5/person/search"
headers = {
    'X-Api-Key': api_key,
    'Content-Type': 'application/json'
}

# SIMPLEST POSSIBLE QUERY - just 1 person from OpenAI
params = {
    'query': {
        'term': {'job_company_name': 'openai'}
    },
    'size': 1
}

print(f"Query: {params}")
print(f"\nSending request...")

try:
    response = requests.post(url, headers=headers, json=params, timeout=10)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('data'):
            person = data['data'][0]
            print(f"\nSUCCESS! Got employee:")
            print(f"Name: {person.get('full_name')}")
            print(f"Title: {person.get('job_title')}")
            print(f"Company: {person.get('job_company_name')}")
        else:
            print("No data returned")
            print(f"Full response: {data}")
    else:
        print(f"Error response: {response.text}")
        
except requests.exceptions.Timeout:
    print("\nTIMEOUT after 10 seconds!")
    print("This means PDL API is not responding at all")
    print("\nPossible reasons:")
    print("1. Your API key might be invalid or out of credits")
    print("2. PDL service might be down")
    print("3. Network/firewall issue blocking the connection")
    
except Exception as e:
    print(f"Error: {e}")
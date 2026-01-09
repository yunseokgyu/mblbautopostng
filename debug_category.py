import wp_utils
import os
import requests
import json

def list_all_categories():
    site_url = os.getenv("WP_URL")
    headers = wp_utils.get_auth_header()
    
    endpoint = f"{site_url}/wp-json/wp/v2/categories?per_page=100"
    resp = requests.get(endpoint, headers=headers)
    
    if resp.status_code == 200:
        categories = resp.json()
        print("--- All Categories ---")
        for c in categories:
            print(f"ID: {c['id']}, Name: {c['name']}, Slug: {c['slug']}, Parent: {c['parent']}")
    else:
        print(f"Error: {resp.text}")

list_all_categories()

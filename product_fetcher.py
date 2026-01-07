import tkinter as tk
from tkinter import ttk, filedialog
import requests
from requests.exceptions import RequestException
import threading
from concurrent.futures import ThreadPoolExecutor
import time
import json
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Get API keys
access_token = os.getenv("ACCESS_TOKEN")

# Check if keys are loaded
if not access_token:
    keys_loaded = False
else:
    keys_loaded = True

# Shared variables for progress tracking
product_details = []
completed = 0
total = 0
lock = threading.Lock()

# API Functions

headers = {
    "access-token": access_token,
    "Content-Type": "application/json"
}

def fetch_product_list(brand_name, start_id=0, page_size=50, retries=5):
    url = "https://distopen.poizon.com/open/api/v1/distribute/product/querySpuList"
    params = {
        "startId": start_id,
        "pageSize": page_size,
        "distBrandName": [e.strip() for e in brand_name.split(",")]
    }
    response = None
    for attempt in range(retries):
        try:
            response = requests.post(url, json=params, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            if attempt < retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                if response.status_code == 429:  # Rate limiting
                    wait_time = max(wait_time, 5)  # Wait longer for 429
                time.sleep(wait_time)
            else:
                raise Exception(f"Failed to fetch product list: {e}")




# Backend Logic


def fetch_products_task(brand_name):
    global completed, total, product_details
    start_id = 0
    total = 0
    completed = 0
    product_details = []

    # Initial fetch to get total count
    try:
        data = fetch_product_list(brand_name, start_id, page_size=1)
        if data and 'data' in data:
            total = data['data']['total']
            # Update UI with total immediately if possible, but update_progress handles it via global var
    except Exception as e:
        status_label.config(text=f"Error: {e}")
        return
    
    # Update UI after initial fetch
    if total > 0:
        progress_bar['maximum'] = total
        status_label.config(text=f"Fetching details for {total} products...")
        root.update()

    if total == 0:
        return

    while True:
        try:
            data = fetch_product_list(brand_name, start_id, page_size=200)
            if not data or 'data' not in data:
                break
                
            products = data['data']['spuList']
            if not products:
                break
                
            with lock:
                product_details.extend(products)
                completed += len(products)
            
            start_id = products[-1]['id']
            
            if completed >= total:
                break
                
        except Exception as e:
            print(f"Error in fetch loop: {e}")
            break
        
        # Update UI synchronously
        if total > 0:
            progress_bar['maximum'] = total
        progress_bar['value'] = completed
        status_label.config(text=f"Progress: {completed}/{total}")
        root.update()




# UI Functions


def start_fetching():
    global product_details, completed, total
    product_details = []
    completed = 0
    total = 1 # Initialize to non-zero to prevent immediate completion trigger
    
    brand_name = entry.get().strip()
    if not brand_name:
        status_label.config(text="Please enter a brand name.")
        return
        
    status_label.config(text="Fetching product list...")
    start_button.config(state="disabled")
    
    # Run fetching synchronously
    root.update() # Ensure UI is updated before blocking
    fetch_products_task(brand_name)
    
    # UI updates after fetching is done
    status_label.config(text="Fetching complete. Saving data...")
    root.update()
    save_data()
    start_button.config(state="normal")


def save_data():
    if product_details:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Save Product Data"
        )
        if file_path:
            try:
                with open(file_path, "w") as f:
                    json.dump(product_details, f, indent=2)
                status_label.config(text="Data saved successfully!")
            except Exception as e:
                status_label.config(text=f"Error saving data: {e}")
    else:
        status_label.config(text="No data to save.")


# Setup GUI
root = tk.Tk()
root.title("Product Fetcher")
root.geometry("400x200")

tk.Label(root, text="Enter Brand Name:").pack(pady=5)
entry = tk.Entry(root, width=30)
entry.pack(pady=5)

start_button = tk.Button(root, text="Start", command=start_fetching)
start_button.pack(pady=5)

progress_bar = ttk.Progressbar(root, length=300, mode='determinate')
progress_bar.pack(pady=10)

status_label = tk.Label(root, text="")
status_label.pack(pady=5)

if not keys_loaded:
    start_button.config(state="disabled")
    status_label.config(text="Error: API keys not found in .env file.")
else:
    status_label.config(text="Ready to fetch.")

root.mainloop()
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
app_key = os.getenv("APP_KEY")
app_secret = os.getenv("APP_SECRET")

# Check if keys are loaded
if not app_key or not app_secret:
    keys_loaded = False
else:
    keys_loaded = True

# Shared variables for progress tracking
product_details = []
completed = 0
total = 0
lock = threading.Lock()

# API Functions


def fetch_product_list(brand_name, start_id=0, page_size=50, retries=5):
    url = "https://openapi.dajisaas.com/poizon/product/queryList"
    params = {
        "appKey": app_key,
        "appSecret": app_secret,
        "startId": start_id,
        "pageSize": page_size,
        "distBrandName": brand_name
    }
    response = None
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=10)
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


def fetch_product_detail(dw_spu_id, retries=5):
    url = "https://openapi.dajisaas.com/poizon/product/queryDetail"
    params = {
        "appKey": app_key,
        "appSecret": app_secret,
        "dwSpuId": dw_spu_id
    }
    response = None
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            if attempt < retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                if response and response.status_code == 429:  # Rate limiting
                    wait_time = max(wait_time, 5)
                time.sleep(wait_time)
            else:
                raise Exception(
                    f"Failed to fetch product detail for {dw_spu_id}: {e}")

# Backend Logic


def get_product_ids_and_total(brand_name):
    product_ids = []
    start_id = 0
    total_count = None
    while True:
        data = fetch_product_list(brand_name, start_id)
        if total_count is None:
            total_count = data['data']['total']
            # total_count = 100
        products = data['data']['spuList']
        if not products:
            break
        product_ids.extend([product['dwSpuId'] for product in products])
        start_id = products[-1]['id']  # Assuming 'id' is the pagination field
        if len(product_ids) >= total_count:
            break
    return product_ids, total_count


def fetch_product_detail_wrapper(pid):
    global completed
    try:
        data = fetch_product_detail(pid)
        with lock:
            product_details.append(data)
            completed += 1
    except Exception as e:
        print(f"Error: {e}")
        with lock:
            completed += 1  # Count as completed even if failed


def fetch_all_product_details(product_ids):
    # Limit to 3 workers to respect rate limit of 3 requests/sec
    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.map(fetch_product_detail_wrapper, product_ids)

# UI Functions


def start_fetching():
    global product_details, completed, total
    product_details = []
    completed = 0
    brand_name = entry.get().strip()
    if not brand_name:
        status_label.config(text="Please enter a brand name.")
        return
    status_label.config(text="Fetching product list...")
    start_button.config(state="disabled")
    try:
        product_ids, total = get_product_ids_and_total(brand_name)
        progress_bar['maximum'] = total
        status_label.config(text=f"Fetching details for {total} products...")
        threading.Thread(target=fetch_all_product_details,
                         args=(product_ids,), daemon=True).start()
        update_progress()
    except Exception as e:
        print(e)
        status_label.config(text=f"Error: {e}")
        start_button.config(state="normal")


def update_progress():
    with lock:
        progress_bar['value'] = completed
        status_label.config(text=f"Progress: {completed}/{total}")
    if completed < total:
        root.after(100, update_progress)
    else:
        status_label.config(text="Fetching complete. Saving data...")
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
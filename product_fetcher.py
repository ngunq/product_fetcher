import tkinter as tk
from tkinter import ttk, filedialog
import requests
from requests.exceptions import RequestException
import threading
import asyncio
import aiohttp
from aiohttp import ClientSession
import json
import os
from dotenv import load_dotenv
import time

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
completed = 0
total = 0
lock = threading.Lock()

# API Functions
def fetch_product_list(brand_name, start_id=0, page_size=100, retries=3):
    url = "https://openapi.dajisaas.com/poizon/product/queryList"
    params = {
        "appKey": app_key,
        "appSecret": app_secret,
        "startId": start_id,
        "pageSize": page_size,
        "distBrandName": brand_name
    }
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

# Asynchronous function to fetch a single product detail
async def fetch_product_detail_async(session, dw_spu_id, retries=3):
    url = "https://openapi.dajisaas.com/poizon/product/queryDetail"
    params = {
        "appKey": app_key,
        "appSecret": app_secret,
        "dwSpuId": dw_spu_id
    }
    for attempt in range(retries):
        try:
            async with session.get(url, params=params, timeout=10) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"Failed to fetch {dw_spu_id}: {e}")
                return None

# Fetch a batch of product details
async def fetch_batch(session, batch, semaphore):
    async with semaphore:
        tasks = [fetch_product_detail_async(session, pid) for pid in batch]
        return await asyncio.gather(*tasks, return_exceptions=True)

# Main function to fetch all product details in batches
async def fetch_all_product_details_async(product_ids, batch_size=100):
    global completed, total
    semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent requests
    async with ClientSession() as session:
        for i in range(0, len(product_ids), batch_size):
            batch = product_ids[i:i + batch_size]
            results = await fetch_batch(session, batch, semaphore)
            # Process results
            batch_details = [result for result in results if isinstance(result, dict)]
            # Save batch to disk
            save_batch_to_disk(batch_details)
            # Update progress
            with lock:
                completed += len(batch)
                progress_bar['value'] = completed
                status_label.config(text=f"Progress: {completed}/{total}")
            # Respect rate limit with a small delay
            await asyncio.sleep(1)

# Save batch to disk incrementally
def save_batch_to_disk(batch):
    mode = "a" if os.path.exists(product_details_file) else "w"
    with open(product_details_file, mode) as f:
        json.dump(batch, f, indent=2)
        f.write("\n")  # Separate batches for readability

# Backend Logic
def get_product_ids_and_total(brand_name):
    product_ids = []
    start_id = 0
    total_count = None
    while True:
        data = fetch_product_list(brand_name, start_id)
        if total_count is None:
            total_count = data['data']['total']
        products = data['data']['spuList']
        if not products:
            break
        product_ids.extend([product['dwSpuId'] for product in products])
        start_id = products[-1]['id']  # Assuming 'id' is the pagination field
        if len(product_ids) >= total_count:
            break
    return product_ids, total_count

# Start the asynchronous fetching process
def start_fetching_async(product_ids):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(fetch_all_product_details_async(product_ids))
    loop.close()
    start_button.config(state="active")


# UI Functions
def start_fetching():
    global completed, total, product_details_file
    progress_bar['value'] = 0
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
        # Initialize the output file
        product_details_file = f"product_data_{brand_name}.json"
        if os.path.exists(product_details_file):
            os.remove(product_details_file)
        # Start the asynchronous fetching in a separate thread
        threading.Thread(target=start_fetching_async, args=(product_ids,), daemon=True).start()
    except Exception as e:
        status_label.config(text=f"Error: {e}")
        start_button.config(state="normal")

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
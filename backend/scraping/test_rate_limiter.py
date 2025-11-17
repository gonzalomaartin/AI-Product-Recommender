import requests
from concurrent.futures import ThreadPoolExecutor
import time
import os 
import psutil 

NUMBER_REQUESTS = int(10e2)

def fetch(url):
    t0 = time.time() 
    headers = {
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    response = requests.get(url, headers = headers) 
    #print(f"{url} -> {response.status_code} -> {time.time() - t0:.2f}s")
    return response.status_code

urls = ["https://tienda.mercadona.es/"] * NUMBER_REQUESTS
# Threaded parallel requests
t0 = time.time() 
with ThreadPoolExecutor(psutil.cpu_count(logical=False)) as executor:
    results = list(executor.map(fetch, urls))

t1 = time.time() 
print(f"Time for {NUMBER_REQUESTS} requests with the max CPU threads: {t1 - t0:.2f}s")
print(f"Rate limited requests: {sum(v == 429 for v in results)}")
print(f"How many requests have not been successful: {sum(not 200 <= v <= 299 for v in results)}")
# Mass Domain Availability Check Execution Guide

## Context & Background
The user requires checking the availability of ALL 456,976 possible 4-letter English domain combinations (.com). 
Previous attempts using sequential loops or simple concurrency resulted in IP bans and extreme delays. Verisign enforces strict rate limits on Data Center IPs.
The goal is to leverage the Jules environment's high bandwidth combined with Python `asyncio` and an Open-Source Proxy Pool to check these domains reliably.

## Execution Strategy
1. **Proxy Pool Setup:** Jules MUST deploy a local instance of an open-source Proxy Pool (e.g., `Germey/ProxyPool`) to scrape and validate free proxies continuously.
2. **Combination Generation:** Generate all 4-letter combinations from `aaaa` to `zzzz`.
3. **Async Processing:** Use `asyncio` and `aiohttp` to send concurrent requests to `https://rdap.verisign.com/com/v1/domain/{word}.com` via the local proxy API.
4. **Robust Retry Mechanism:** Free proxies will frequently timeout or drop connections. The script MUST catch these errors and place the failed domain back into the queue for a retry. Do not mark a domain as unavailable due to a network error.

## The Python Script Blueprint
```python
import asyncio
import aiohttp
import itertools
import string
import csv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
RDAP_BASE_URL = "https://rdap.verisign.com/com/v1/domain/{}.com"
PROXY_POOL_API = "http://127.0.0.1:5555/random" # Example local ProxyPool API
CONCURRENCY_LIMIT = 500 # Adjust based on proxy availability
OUTPUT_FILE = "available_domains_jules.csv"

# Function to get a random proxy
async def get_proxy(session):
    try:
        async with session.get(PROXY_POOL_API) as response:
            if response.status == 200:
                proxy = await response.text()
                return f"http://{proxy.strip()}"
    except Exception as e:
        logging.error(f"Failed to get proxy: {e}")
    return None

async def check_domain(domain, session, semaphore):
    url = RDAP_BASE_URL.format(domain)
    
    while True: # Robust Retry Loop
        async with semaphore:
            proxy = await get_proxy(session)
            if not proxy:
                await asyncio.sleep(2) # Wait for proxy pool to replenish
                continue
                
            try:
                # Verisign blocks some standard User-Agents, set a legitimate one
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                async with session.get(url, headers=headers, proxy=proxy, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 404:
                        logging.info(f"[AVAILABLE] {domain}.com")
                        return domain, True
                    elif response.status == 200:
                        return domain, False
                    elif response.status == 429: # Rate limit even with proxy
                         logging.warning(f"Rate limited on proxy {proxy}. Retrying {domain}...")
                         continue # Retry
                    else:
                         logging.warning(f"Unexpected status {response.status} for {domain}. Retrying...")
                         continue # Retry
            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                # Network error, proxy died. Retry the domain.
                continue

async def main():
    domains = [''.join(p) for p in itertools.product(string.ascii_lowercase, repeat=4)]
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    
    # Using TCPConnector with ssl=False for some free proxies if necessary
    connector = aiohttp.TCPConnector(limit=CONCURRENCY_LIMIT, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [check_domain(d, session, semaphore) for d in domains]
        
        # We can use asyncio.as_completed to write results as they come in
        with open(OUTPUT_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Domain'])
            
            for coro in asyncio.as_completed(tasks):
                domain, is_available = await coro
                if is_available:
                    writer.writerow([f"{domain}.com"])
                    f.flush() # Ensure it's written immediately

if __name__ == "__main__":
    asyncio.run(main())
```

## Step-by-Step Instructions for Jules
1. Create a workspace directory.
2. Clone/Setup the Proxy Pool (e.g., `git clone https://github.com/Germey/ProxyPool.git`). Follow its `README` to start the Redis server and the Flask API on port `5555`.
3. Verify the Proxy Pool is gathering IPs by pinging `http://127.0.0.1:5555/random`.
4. Install `aiohttp` (`pip install aiohttp`).
5. Execute the script above. Wait patiently. It may take days due to free proxy timeouts. 
6. Provide the final `available_domains_jules.csv` to the user.


import time
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from rediz.client import Rediz
import asyncio
import aiohttp
import json

async def fetch(session, url):
    async with session.get(url) as response:
        if response.status != 200:
            response.raise_for_status()
        return await response.text()

async def fetch_all(session, urls):
    tasks = []
    for url in urls:
        task = asyncio.create_task(fetch(session, url))
        tasks.append(task)
    results = await asyncio.gather(*tasks)
    return results

async def fetch_prices(symbols):
    urls = [ REDIZ_COLLIDER_CONFIG["template_url"].replace("SYMBOL",symbol) for symbol in symbols ]
    async with aiohttp.ClientSession() as session:
        results = await fetch_all(session, urls)
    prices = [json.loads(r).get('Global Quote')['05. price'] for r in results]
    return prices

def collider_prices():
    symbols = REDIZ_COLLIDER_CONFIG["symbols"]
    try:
        prices =  asyncio.run( fetch_prices(symbols=symbols ) )
        return {"names":[ s+'.json' for s in symbols],"values":list(map(float,prices))}
    except:
        return None

def set_collider_values(rdz,change_data):
    if change_data:
        budgets = [ 100 for _ in data["values"]]
        write_keys = [ REDIZ_COLLIDER_CONFIG["write_key"] for _ in change_data["values"] ]
        change_data.update({"budgets":budgets,"write_keys":write_keys})
        res = rdz.mset(**change_data)
        print("Got data")
    else:
        print("Missing data")

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    HOURS_TO_RUN=3
    previous_data=None
    offset = time.time() % 60
    start_time = time.time()
    while time.time()<start_time+HOURS_TO_RUN*60*60:
        if abs(time.time() % 60 - offset) < 5:
            data = collider_prices() or collider_prices()
            if data:
                num  = len(data["names"])
                if previous_data is not None:
                    changes = [ data["values"][k]-previous_data["values"][k] for k in range(num) ]
                else:
                    changes = [ 0 for k in range(num) ]

                set_before = time.time()
                change_data = {"names":data["names"],"values":data["values"]}
                set_collider_values(rdz=rdz,change_data=change_data)
                set_after = time.time()
                print("Set() took " + str(set_after - set_before) + " seconds.")
                time.sleep(10)
        else:
            time.sleep(1)


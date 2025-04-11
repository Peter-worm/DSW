import requests
import time
import datetime
import json


def fetch_nextbike_data():
    url = "https://api.nextbike.net/maps/nextbike-live.json?city=199,362,812,833"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None
    

if __name__ == "__main__":
    
    while True:
        data = fetch_nextbike_data()
        with open(f"data/nextbike_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
            json.dump(data, f, indent=4)
        
        time.sleep(60)
# Get Data

import requests
from cs50 import SQL

db = SQL("sqlite:///BeerMap.db")


for num in range(8030):
    response = requests.get(f"https://api.openbrewerydb.org/breweries/{num}")
    # response.raise_for_status()
    brewery = response.json()
    print(brewery)

    if "message" not in brewery:

        for key in brewery:
            if not brewery[key]:
                brewery[key] =  ""

        new_brewery = db.execute(
                    "INSERT INTO breweries(id, name, country, state, city, street, zip, longitude, latitude, phone, website, type)"
                    "VALUES(:id, :name, :country, :state, :city, :street, :zip, :longitude, :latitude, :phone, :website, :type)",
                    id=brewery["id"],
                    name=brewery["name"],
                    country=brewery["country"],
                    state=brewery["state"],
                    city=brewery["city"],
                    street=brewery["street"],
                    zip=brewery["postal_code"],
                    longitude=brewery["longitude"],
                    latitude=brewery["latitude"],
                    phone=brewery["phone"],
                    website=brewery["website_url"],
                    type=brewery["brewery_type"])




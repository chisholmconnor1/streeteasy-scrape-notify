#!/usr/bin/env python3

import json
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import time

listing_url = "Your URL of StreetEasy with desired filters e.g. price, sq feet, location"

headers = {
    'User-Agent': 'Add browser user-agent'
}

def is_allowed_time():
    current_time = datetime.now()
        # Check if the time is between 9 AM and 5 PM
    if 5 <= current_time.hour < 22:
        return True
    return False

def get_listing():
    response = requests.get(listing_url, verify=r"Your path to certificate",headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    listings = soup.find_all('div', class_='listingCard')

    listing_data = []

    for listing in listings:
        #get apt name
        Aptname = listing.find('a', class_='listingCard-link')
        Apt_name = Aptname.get_text(strip=True) if Aptname else 'N/A'
        
        # Find all spans within the listing
        spans = listing.find_all("span")
        sq_feet = "N/A"  # Default value

        for span in spans:
            # Check if the current span has "ft²" in any of its children
            if span.find("span", {"aria-hidden": "true"}) and "ft²" in span.find("span", {"aria-hidden": "true"}).text:
                # Extract the numeric square footage from the parent span's text
                sq_feet = span.text.split("square feet")[0].split("ft²")[0].strip()
                sq_feet_num = int(sq_feet.replace(",", ""))
                break   
        
        ## Filter for desired sq feet of apt
        if sq_feet_num is None or sq_feet_num < 750:
            continue

        ## Get ID 
        listing_div = listing.find('div', class_='SRPCarousel-container')
        if listing_div:
            listing_id = listing_div.get('data-listing-id')  # Extract the listing ID

        ## Get date added
        listing_price = listing.find('div', class_='listingCardBottom-emphasis')
        listingPrice = listing_price.find('span', class_='price listingCard-priceMargin').get_text(strip=True)

        listing_link = None
        ## Get link
        link_tag = listing.find('a', class_='listingCard-globalLink jsGlobalListingCardLink')
        if link_tag:    
            listing_link = link_tag.get('href')

        listing_data.append({
            'Name': Apt_name,
            'Sq Feet': sq_feet_num,
            'id':listing_id,
            'Price': listingPrice, 
            'Link': listing_link
        })
    return listing_data
        
## Function to compare listing if a new listing exists
def compare_listing(listing_data, previous_ids):

    new_ids = {listing['id'] for listing in listing_data}

    new_entries = new_ids - previous_ids

    ## Check if listing ID exists in current list, if not, trigger a new alert
    if new_entries:
        for listing in listing_data:
            if listing['id'] in new_entries:
                trigger_new_listing(listing)
    else: 
        print("No new Apt's for now...")

## Read password for sms via email notifcation
def read_pp(file_path=r"Your path to your password file"):
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()  # Read and remove any surrounding whitespace
    except FileNotFoundError:
        print(f"Error: Password file not found.")
        return None

## Function to send an sms notification via email gateway (Free service) if a new apt is added to Streeteasy
def send_sms_via_email(message, recipients, pf="pf.txt"):
    
    sender_email = "Enter your email"
    sender_password = read_pp(pf)

    msg = MIMEText(message)
    msg['From'] = sender_email
    msg['Subject'] = "New Listing Alert"

    ##Replace first param depending on email account
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email,sender_password)
        for recipient in recipients:
            try:
                server.sendmail(sender_email, recipient, msg.as_string())
                print(f"Message sent to {recipient}")
            except Exception as e:
                print(f"Failed to send message to {recipient}: {e}")

## new listing trigger
def trigger_new_listing(listing):
    message = f"New listing found: {listing['Name']} , Price: {listing['Price']}, Sq Feet: {listing['Sq Feet']}, Link: {listing['Link']}"
    print(f"New listing found: {listing['Name']} with ID: {listing['id']} .")
    recipients = [
    'addphonenumberforVerizon@vtext.com',
    'addphonenumberforAT&T@txt.att.net',
    'Repeat',
    ]
    send_sms_via_email(message, recipients)

def main():
    ## Restrict time allowed to execute
    if not is_allowed_time():
        print("Outside allowed time range. Exiting.")
        return
    
    listings = get_listing()   #Get list of currnet findings
    previous_ids = load_previous_ids()   #load the previous list of IDs to compare against
    compare_listing(listings, previous_ids)  #compare the new listings against the previous list of IDs
    save_previous_ids(previous_ids, listings)      #Save the updated list of Ids to persist for future comparisions


def save_previous_ids(previous_ids, new_listings, file_path=r"[YOUR PATH]\previous.ids.json"):
    updated_ids = previous_ids | {listing['id'] for listing in new_listings}

    sorted_ids = sorted(updated_ids, key=int)

    with open(file_path, 'w') as file:
        json.dump(list(sorted_ids), file)

def load_previous_ids(file_path=r"[YOUR PATH]\previous.ids.json"):
    try:
            with open(file_path, 'r') as file:
                content = file.read()
                # If the file is not empty, try to load it as JSON
                if content:
                    return set(json.loads(content))  # Load and convert back to set
                else:
                    return set()  # If file is empty, return an empty set
    except FileNotFoundError:
        return set()  # If no file exists, return an empty set

if __name__ == "__main__":
    while True:
        main()
        ## Check for apt's every hour
        time.sleep(3600)


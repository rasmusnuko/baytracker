import sys
import time
import requests
import argparse
import numpy as np
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from collections import defaultdict
from selenium.common.exceptions import NoSuchElementException

def build_url(item, condition):
  # Build HTML search url from from item name
  url = "https://www.ebay.com/sch/i.html?_nkw="
  url += item
  url += "&LH_Sold=1"       # Sold listings or not
  url += "&_ipg=240"        # 240 items pr page
  # Working condition
  url += "&LH_ItemCondition=1500|2500|3000|1000" if condition == 'working' else ''  # Working condition
  # New condition
  url += "&LH_ItemCondition=1000|1500" if condition == 'new' else ''
  # Used condition
  url += "&LH_ItemCondition=3000|2500" if condition == 'used' else ''
  # Defect condition
  url += "&LH_ItemCondition=7000" if condition == 'defect' else ''
  
  print(url)
  return url


# Returns a list of listings
def scrape_data(url, page):
  # Load JS to get full html
  driver = webdriver.Chrome()
  driver.get(url)

  # len != 0, when site loaded by itself, or CAPTCHA has been solved
  titles = []
  while(len(titles) == 0):
    page = driver.page_source
    soup = BeautifulSoup(page, 'html.parser')
    titles = soup.find_all('h3', {"class":"s-item__title s-item__title--has-tags"})
    time.sleep(1)

  # Quit selenium
  driver.quit()
  
  # Get titles
  titles = [title.getText() for title in titles]
  titles = titles[1::]  # Titles are offset by one on eBay
  # Get dates
  dates = [date.find('span', {"class":"POSITIVE"}).getText() for date in soup.find_all('div', {"class":"s-item__title--tag"})]
  dates = [date.replace("Sold  ", "") for date in dates]  # Remove preceding "Sold"
  dates = [datetime.strptime(date, '%b %d, %Y') for date in dates]  # Convert to datetime
  # Get prices
  prices = [price.getText() for price in soup.find_all('span', {"class":"s-item__price"})]
  prices = prices[:len(titles)-1:]
  prices = [price.split(" ") for price in prices] # Seperate currency and price
  prices = [[float(price[1].replace(",", "")), price[0]] for price in prices]  # Swapping amount and currency, and casting amount to float
  # Get countries
  countries = [country.getText() for country in soup.find_all('span', {"class":"s-item__location s-item__itemLocation"})]
  countries = [country.replace("from ", "") for country in countries] # Remove preceding "from"

  # Removing top and bottom 10% of prices, to get rid of outliers
  outliers = []
  amounts = [price[0] for price in prices]
  amounts = np.array(amounts)
  # Finding outliers
  for i in range(len(amounts)):
    if amounts[i] < np.quantile(amounts,0.1) or amounts[i] > np.quantile(amounts,0.9):
      outliers.append(i)
  # Removing outliers
  for i in list(reversed(outliers)):
    titles.pop(i)
    dates.pop(i)
    prices.pop(i)
    countries.pop(i)
  
  # Internal ID
  IDs = list(range(len(prices)))

  return (IDs, titles, prices, countries, dates)


# Y-axis is price, X-axis is date
def plot_dates(axs, prices, dates):
  # Splitting price into amount and currency
  amounts = [price[0] for price in prices]
  currency = prices[0][1]

  # Plotting each price with date
  for (date, amount) in zip(dates,amounts):
    axs[0].scatter(date, amount)

  # Getting avg for each date
  date_avg = defaultdict(list)
  for k, v in zip(dates, amounts):
    date_avg[k].append(v)
  for k in date_avg:
    date_avg[k] = sum(date_avg[k])/len(date_avg[k])
  
  # Plotting daily average
  date, amount = [], []
  for k, v in date_avg.items():
    date.append(k)
    amount.append(v)
  axs[0].plot(date, amount, label='Daily average')

  # Format x-axis title
  myFmt = mdates.DateFormatter('%m/%d')
  axs[0].xaxis.set_major_formatter(myFmt)


def plot_latest_listings(axs, IDs, prices):
  # Splitting price into amount and currency
  amounts = [price[0] for price in prices]
  currency = prices[0][1]

  # Ploting latest 
  axs[1].scatter(IDs, list(reversed(amounts)))

  # Plot average
  avg_amounts = amounts.copy()
  avg_amounts = sorted(amounts)
  avg = sum(avg_amounts)/len(avg_amounts)
  print("Average price:", np.round(avg,decimals=2), currency)
  axs[1].axhline(y=avg, color="red", label='Average')

  # Highlight middle 50% of amounts
  first_25_percent = len(avg_amounts) // 4
  last_25_percent  = first_25_percent*3 if first_25_percent < len(avg_amounts)-1 else len(avg_amounts)-1
  axs[1].axhspan(avg_amounts[first_25_percent], avg_amounts[last_25_percent], color='green', alpha=0.33)


if __name__ == "__main__":
  # Check if program has been given the arguments needed
  if len(sys.argv) != 3:
    print('Usage:         python3 main.py ITEM CONDITION')
    print('Example usage: python3 main.py "macbook air m1 8gb 256gb" "new"')
    print('Valid conditions are: "working", "new", "used", "defect"')
    sys.exit()
  else:
    # Get user input
    item = sys.argv[1].replace(" ", "+")
    condition = sys.argv[2].lower()
    valid_conditions = ['working', 'new', 'used', 'defect']
    if condition not in valid_conditions:
      print('Unvalid condition. Use: "working", "new", "used", or "defect"')
      sys.exit()

    # Build url with eBay search query
    url = build_url(item, condition)

    # Retrieve data from first page
    (IDs, titles, prices, countries, dates) = scrape_data(url, 1)
    data = list(zip(IDs,titles, prices, countries, dates))  # List of all data
    
    # matplotlib
    fig, axs = plt.subplots(2)

    # Show basic price history
    plot_dates(axs, prices, dates)

    # Plot latest listings
    plot_latest_listings(axs, IDs, prices)

    # Show plot
    plt.show()

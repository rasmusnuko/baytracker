# BayTracker
## Descrition
This program shows price history of sold listings on eBay for a given item

## Demo Image

The term "macboor air m1 8gb 256gb" is searched for, and recent 'sold prices' from ebay listings are shown.

![Demo](./images/demo.png)

## Install
```
pip install -r requirements.txt
```
Aswell as ChromeWebdriver

## Usage

```
python main.py ITEM CONDTION
```
Valid conditions are: 'working', 'new', 'used' 'defect'. \
Where 'working' is 'new' & 'used'

## Example
```
python main.py "ThinkPad x220" "working"
```

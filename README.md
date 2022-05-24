# Intel Project

---

This is the repository for the IFS competitor intelligence dashboard. Here's the broad file structure:

```
data
	- data.csv (the full data)
	- revenue.csv (full customer data)
	- usd_twd.csv (historical conversion between USD and TWD)
app.py (the dash application)
scraper.py (the core scraper module)
aggregate.py (for pulling competitor data)
stocks.py (for pulling ticker data)
regressions.py (for conducting regressions)
forecast.py (a wrapper around Prophet)
converter.py (for currentcy conversion)
parameters.py (storing constants for the program)
```
To launch the dashboard from the terminal, first run `pip3 install -r requirements.txt`. Then run `python3 app.py`.
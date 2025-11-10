# Running Shoe Sale Tracker 🏃

A Python application that automatically monitors multiple websites for running shoe sales and sends notifications when new deals are found.

## Features

- 🔍 **Automated Monitoring**: Checks multiple websites on a customizable schedule
- 💰 **Price Tracking**: Tracks price history and identifies new sales
- 🔔 **Notifications**: Get alerted via console or email when new sales are found
- 📊 **Database Storage**: Stores shoe data and price history in SQLite
- 🎯 **Smart Filtering**: Filter by keywords and minimum discount percentage
- 🔌 **Extensible**: Easy-to-add new website scrapers using a template system

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd sale_search
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Configure the application:
```bash
cp .env.example .env
```

4. Edit `.env` with your preferences:
   - Set notification method (console or email)
   - Configure email settings if using email notifications
   - Adjust check interval, keywords, and minimum discount

## Usage

### Quick Start

Run a single check with the demo scraper:
```bash
python main.py --mode once
```

This will generate sample running shoe data and display any "sales" found.

### Run on Schedule

Monitor continuously with hourly checks:
```bash
python main.py --mode schedule
```

Or specify a custom interval (in minutes):
```bash
python main.py --mode schedule --interval 30
```

### View Current Sales

Display all currently tracked sales:
```bash
python main.py --mode show
```

Limit the number of results:
```bash
python main.py --mode show --limit 10
```

## Configuration Options

Edit `.env` to customize:

### Notification Settings
- `NOTIFICATION_METHOD`: `console` or `email`
- `EMAIL_TO`: Recipient email address
- `EMAIL_FROM`: Sender email address
- `SMTP_SERVER`: SMTP server (default: smtp.gmail.com)
- `SMTP_PORT`: SMTP port (default: 587)
- `SMTP_USERNAME`: SMTP username
- `SMTP_PASSWORD`: SMTP password (use app-specific password for Gmail)

### Scraping Settings
- `USER_AGENT`: Browser user agent string
- `REQUEST_TIMEOUT`: Request timeout in seconds (default: 30)
- `REQUEST_DELAY`: Delay between requests in seconds (default: 2)

### Schedule Settings
- `CHECK_INTERVAL_MINUTES`: How often to check (default: 60)

### Filtering Settings
- `MIN_DISCOUNT_PERCENTAGE`: Minimum discount to trigger alerts (default: 10)
- `KEYWORDS`: Comma-separated keywords to filter shoes (default: running,run,runner,trail,marathon,athletic)

## Adding Website Scrapers

The application comes with a demo scraper for testing. To add real website scrapers:

### 1. Create a New Scraper

Copy the example scraper template:
```bash
cp src/scrapers/example_scraper.py src/scrapers/your_site_scraper.py
```

### 2. Implement Required Methods

Edit your new scraper file:

```python
class YourSiteScraper(BaseScraper):
    @property
    def website_name(self) -> str:
        return "Your Site Name"

    @property
    def base_url(self) -> str:
        return "https://yoursite.com"

    def get_search_urls(self) -> List[str]:
        # Return URLs to scrape
        return [
            f"{self.base_url}/running-shoes/sale",
            f"{self.base_url}/athletic/mens-running",
        ]

    def parse_listing_page(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        # Extract shoe data from the page
        # See example_scraper.py for detailed implementation
        pass
```

### 3. Register the Scraper

Add your scraper to `src/scrapers/__init__.py`:

```python
from .your_site_scraper import YourSiteScraper

SCRAPERS = [
    YourSiteScraper,
    # Other scrapers...
]
```

### Tips for Creating Scrapers

1. **Inspect the Website**: Use browser developer tools to identify HTML structure
2. **Find Product Containers**: Look for div/article elements containing product info
3. **Extract Key Data**: Name, price, sale price, URL, product ID
4. **Test Thoroughly**: Run `--mode once` to test your scraper
5. **Be Respectful**: Follow robots.txt and add appropriate delays

## Project Structure

```
sale_search/
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Example configuration
├── logs/                  # Application logs
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── database.py        # SQLite database operations
│   ├── notifier.py        # Notification system
│   ├── shoe_tracker.py    # Main tracking logic
│   └── scrapers/
│       ├── __init__.py
│       ├── base_scraper.py      # Base scraper class
│       ├── example_scraper.py   # Template for new scrapers
│       └── demo_scraper.py      # Demo data generator
└── shoe_sales.db          # SQLite database (created on first run)
```

## Database Schema

The application uses SQLite with three main tables:

- **shoes**: Stores product information and current prices
- **price_history**: Tracks price changes over time
- **sale_alerts**: Manages notifications for new sales

## Command-Line Options

```
usage: main.py [-h] [--mode {once,schedule,show}] [--interval INTERVAL]
               [--limit LIMIT] [--db DB] [-v]

options:
  -h, --help            Show help message
  --mode {once,schedule,show}
                        Run mode (default: schedule)
  --interval INTERVAL   Check interval in minutes (default: 60)
  --limit LIMIT         Number of sales to show (default: 20)
  --db DB              Database file path
  -v, --verbose        Enable verbose logging
```

## Email Setup (Gmail Example)

To use email notifications with Gmail:

1. Enable 2-factor authentication on your Google account
2. Generate an app-specific password:
   - Go to Google Account → Security → App passwords
   - Generate a password for "Mail"
3. Add to `.env`:
   ```
   NOTIFICATION_METHOD=email
   EMAIL_TO=your-email@gmail.com
   EMAIL_FROM=your-email@gmail.com
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-specific-password
   ```

## Running as a Service

### Linux (systemd)

Create `/etc/systemd/system/shoe-tracker.service`:

```ini
[Unit]
Description=Running Shoe Sale Tracker
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/sale_search
ExecStart=/usr/bin/python3 /path/to/sale_search/main.py --mode schedule
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable shoe-tracker
sudo systemctl start shoe-tracker
```

### macOS (launchd)

Create `~/Library/LaunchAgents/com.shoe-tracker.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.shoe-tracker</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/path/to/sale_search/main.py</string>
        <string>--mode</string>
        <string>schedule</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Load the service:
```bash
launchctl load ~/Library/LaunchAgents/com.shoe-tracker.plist
```

## Troubleshooting

### No sales found
- Check if your keywords match the shoe names
- Verify the scraper is working correctly
- Lower `MIN_DISCOUNT_PERCENTAGE` in `.env`

### Email not sending
- Verify SMTP settings in `.env`
- Check that you're using an app-specific password (for Gmail)
- Look at logs in `logs/shoe_tracker.log`

### Scraping errors
- Website structure may have changed
- Check if you're being rate-limited
- Increase `REQUEST_DELAY` in `.env`

## Legal and Ethical Considerations

- **Respect robots.txt**: Check each website's robots.txt file
- **Rate Limiting**: Don't overwhelm servers with requests
- **Terms of Service**: Review and comply with each website's TOS
- **API Alternatives**: Consider using official APIs when available
- **Personal Use**: This tool is intended for personal use only

## Contributing

Contributions are welcome! To add scrapers for new websites:

1. Fork the repository
2. Create a new scraper using the template
3. Test thoroughly
4. Submit a pull request

## License

This project is for educational and personal use.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

Happy deal hunting! 🎉
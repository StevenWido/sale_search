# Hidden Price Detection & Manual Review

This feature automatically detects items with hidden prices (like "See Price in Cart") and flags them for your manual review.

## How It Works

1. **Automatic Detection**: The scraper looks for common hidden price patterns
2. **Database Flagging**: Items are marked with `price_hidden=True` and `requires_manual_review=True`
3. **Notifications**: You get alerts about items needing manual review
4. **Easy Access**: View all flagged items with `--mode review`

## Common Hidden Price Patterns Detected

The system automatically detects these phrases (case-insensitive):

- "See Price in Cart"
- "Price in Cart"
- "Add to Cart to See Price"
- "Add to Bag to See Price"
- "Login to See Price"
- "Sign In to See Price"
- "View Price in Cart"
- "Price Available in Cart"
- "Cart Price"
- "Special Price in Cart"
- "Member Price"
- "Members Only"

## Using in Your Scrapers

### Step 1: Import and Use the Helper Function

In your scraper's `parse_listing_page` method:

```python
def parse_listing_page(self, soup: BeautifulSoup, url: str) -> List[Dict]:
    shoes = []

    for container in soup.select('.product-card'):
        # ... extract name, url, product_id ...

        # Check if price is hidden
        if self.is_price_hidden(container):
            # Flag for manual review
            shoe_data = {
                'product_id': self.generate_product_id(self.website_name, product_id),
                'name': name,
                'url': product_url,
                'current_price': None,  # No price available
                'price_hidden': True,
                'requires_manual_review': True,
                # ... other fields ...
            }
        else:
            # Normal price extraction
            # ... your regular price parsing code ...

        shoes.append(shoe_data)

    return shoes
```

### Step 2: Run the Application

```bash
# Run a check - will detect hidden prices
python main.py --mode once

# View items needing manual review
python main.py --mode review
```

## Viewing Manual Review Items

### Command Line

```bash
# View all items requiring manual review
python main.py --mode review

# Limit to 10 items
python main.py --mode review --limit 10
```

### Console Output Example

```
================================================================================
🔍 ITEMS REQUIRING MANUAL REVIEW (showing 3 items)
These items may be on sale but prices are hidden - check them manually!
================================================================================

1. Nike Air Zoom Pegasus 40
   Brand: Nike
   Website: Adidas
   💡 Price Hidden - Check cart for actual price
   URL: https://example.com/nike-pegasus-40
   Last checked: 2025-11-10 10:30:00

2. Brooks Ghost 15
   Website: Running Warehouse
   💡 Price Hidden - Check cart for actual price
   URL: https://example.com/brooks-ghost-15
   Last checked: 2025-11-10 10:30:00

================================================================================
Total items needing review: 2
Tip: Visit each URL and add to cart to see the actual price
================================================================================
```

## Email Notifications

If you have email configured, you'll receive HTML emails with:

- List of all items needing manual review
- Highlighted warning that price is hidden
- "Check Price" buttons linking directly to products
- Orange/yellow styling to differentiate from regular sale alerts

### Email Example

**Subject**: 🔍 3 Items Need Manual Price Check

**Body**:
- Each item shown in a yellow-highlighted box
- Direct links to check prices
- Helpful reminder about adding to cart

## Database Fields

Two new fields were added to track hidden prices:

- `price_hidden` (BOOLEAN): True if price text pattern was detected
- `requires_manual_review` (BOOLEAN): True if item needs manual checking

## API Methods

### Get Manual Review Items

```python
from src.shoe_tracker import ShoeTracker

tracker = ShoeTracker()

# Get all items needing review
items = tracker.get_manual_review_items()

# Get limited items
items = tracker.get_manual_review_items(limit=10)
```

### Mark Item as Reviewed

```python
from src.database import Database

db = Database()

# After manually checking an item
db.mark_manual_review_done(product_id="Nike_ABC123")
```

## Workflow

1. **Scraper runs** → Detects hidden prices automatically
2. **Database updated** → Items flagged for review
3. **Notifications sent** → Console/email alerts
4. **Manual check** → You visit the URLs
5. **Optional** → Mark as reviewed in database

## Example: Full Implementation

See `src/scrapers/hidden_price_example.py` for a complete example showing:

- How to check for hidden prices
- How to structure data for hidden price items
- How to handle both hidden and visible prices in one scraper

## Tips

### Add Custom Patterns

Edit `src/scrapers/base_scraper.py` to add site-specific patterns:

```python
hidden_price_patterns = [
    'see price in cart',
    'your custom pattern here',
    'site-specific text',
]
```

### Filter by Website

To see only items from a specific site, query the database:

```python
db = Database()
cursor = db.conn.cursor()
cursor.execute("""
    SELECT * FROM shoes
    WHERE requires_manual_review = 1
    AND website = 'Adidas'
""")
items = cursor.fetchall()
```

### Automate Checking

You could even automate the checking process with Selenium:

```python
from selenium import webdriver

items = tracker.get_manual_review_items()

for item in items:
    driver = webdriver.Chrome()
    driver.get(item['url'])
    # Click add to cart
    # Extract price
    # Update database with actual price
    # Mark as reviewed
```

## Benefits

✅ **No complex cart APIs** - Just detect and flag
✅ **Fast scraping** - No Selenium cart interaction needed
✅ **Track everything** - Don't miss hidden sale items
✅ **Organized** - All flagged items in one place
✅ **Flexible** - Check manually at your convenience

## Summary

This feature gives you the best of both worlds:

- **Automatic detection** of potentially hidden sale items
- **No complex scraping** of cart systems required
- **Organized alerts** so you can check manually
- **Full tracking** in the database

Perfect for sites like Adidas, Nike, Dick's that often hide prices for big sales!

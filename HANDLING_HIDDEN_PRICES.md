# Handling Websites with Hidden Prices

Some websites hide prices until you add items to the cart. This guide shows you how to handle these sites.

## Why Sites Hide Prices

- **Prevent price scraping** - Stop competitors from monitoring prices
- **Reduce comparison shopping** - Make it harder for price comparison sites
- **Encourage sign-in** - Force users to create accounts
- **Regional pricing** - Show different prices based on location/account

## Three Approaches (From Best to Worst)

### Approach 1: API Interception ⭐ BEST
**Speed:** Fast
**Reliability:** High
**Complexity:** Medium

Look for API calls that return price data in JSON format.

#### How to Find APIs:

1. Open website in Chrome
2. Press F12 → **Network** tab
3. Filter by **Fetch/XHR**
4. Click "Add to Cart" or load a product page
5. Look for API calls (usually `/api/...` or `.json`)
6. Click the call → **Response** tab → Check if it contains prices

**Common API patterns:**
```
/api/products/{id}
/api/cart/add
/api/product-details/{sku}
/v1/products?ids=...
/graphql (GraphQL endpoints)
```

**Example Code:** See `src/scrapers/api_scraper_example.py`

**Pros:**
- Fast (direct API calls)
- No browser automation needed
- Less likely to be blocked
- Easy to parse JSON

**Cons:**
- APIs might require authentication tokens
- API structure can change
- Some APIs have rate limiting

---

### Approach 2: Hidden Data Extraction ⭐ GOOD
**Speed:** Fast
**Reliability:** Medium
**Complexity:** Low

Extract prices from hidden data already in the HTML.

#### Where to Look:

**A) JSON-LD Structured Data (SEO data)**

Many sites include product data for search engines:

```html
<script type="application/ld+json">
{
  "@type": "Product",
  "name": "Nike Air Zoom Pegasus",
  "offers": {
    "price": "89.99",
    "priceCurrency": "USD"
  }
}
</script>
```

**B) Next.js / React Data**

```html
<script id="__NEXT_DATA__" type="application/json">
{
  "props": {
    "pageProps": {
      "products": [
        {"id": "123", "price": 89.99}
      ]
    }
  }
}
</script>
```

**C) Data Attributes**

```html
<div class="product"
     data-price="89.99"
     data-original-price="120.00"
     data-product-data='{"price": 89.99}'>
```

**D) JavaScript Variables**

```html
<script>
  var productData = {"price": 89.99, "salePrice": 79.99};
  window.products = [{...}, {...}];
</script>
```

**Example Code:** See `src/scrapers/hidden_data_scraper.py`

**Pros:**
- Very fast (no additional requests)
- Works with basic HTTP requests
- Data is already parsed for you

**Cons:**
- Not all sites include this data
- Might be outdated/incorrect
- Requires inspecting HTML source

---

### Approach 3: Cart Interaction ⚠️ LAST RESORT
**Speed:** Slow
**Reliability:** Medium
**Complexity:** High

Use Selenium to actually add items to cart.

#### When to Use:
- No API available
- No hidden data in HTML
- Prices truly only shown after cart interaction

**Example Code:** See `src/scrapers/cart_interaction_scraper.py`

**Pros:**
- Works when nothing else does
- Can handle complex interactions
- Sees exact same data as user

**Cons:**
- Very slow (visits each product page)
- Requires Selenium/browser automation
- High resource usage
- Can trigger anti-bot measures
- Need to clear cart between products

---

## Practical Example: Implementing for a Real Site

Let's say you're scraping "ExampleShoes.com" that hides prices.

### Step 1: Investigate

Open the site and try all three approaches:

#### Check for APIs:
```bash
1. Open DevTools → Network → Fetch/XHR
2. Add a product to cart
3. Look for API calls with price data
```

#### Check for Hidden Data:
```bash
1. View page source (Ctrl+U)
2. Search for: "ld+json", "__NEXT_DATA__", "data-price"
3. Search for the product name and see what's nearby
```

#### Test Basic Scraping:
```python
# Try with just requests first
import requests
from bs4 import BeautifulSoup

resp = requests.get('https://exampleshoes.com/product/123')
soup = BeautifulSoup(resp.content, 'lxml')

# Check if price is visible
price = soup.select_one('.price, .product-price')
print(price.get_text() if price else "No price found")
```

### Step 2: Implement Best Approach

Based on what you found, create your scraper:

#### If you found an API:

```python
# In your scraper class
def get_product_data(self, product_id):
    response = self.session.get(
        f"https://exampleshoes.com/api/products/{product_id}"
    )
    data = response.json()

    return {
        'current_price': data['price'],
        'original_price': data.get('compareAtPrice', data['price']),
        'is_on_sale': data.get('onSale', False)
    }
```

#### If you found JSON-LD:

```python
# In parse_listing_page or parse_product_page
scripts = soup.find_all('script', type='application/ld+json')
for script in scripts:
    data = json.loads(script.string)
    if data.get('@type') == 'Product':
        price = data.get('offers', {}).get('price')
        # Use this price
```

#### If you found Next.js data:

```python
script = soup.find('script', id='__NEXT_DATA__')
if script:
    data = json.loads(script.string)
    products = data['props']['pageProps']['products']
    # Use products data
```

#### If nothing else works (Cart Interaction):

```python
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get(product_url)

# Click add to cart
add_button = driver.find_element(By.CSS_SELECTOR, '.add-to-cart')
add_button.click()

# Wait and get price from cart modal
time.sleep(2)
price_elem = driver.find_element(By.CSS_SELECTOR, '.cart-item-price')
price = price_elem.text
```

---

## Real-World Examples

### Example 1: Site Using GraphQL API

```python
def get_products(self):
    query = """
    query {
      products(first: 50, query: "running shoes") {
        edges {
          node {
            id
            title
            priceRange {
              minVariantPrice {
                amount
              }
            }
          }
        }
      }
    }
    """

    response = self.session.post(
        'https://site.com/api/graphql',
        json={'query': query}
    )

    return response.json()['data']['products']['edges']
```

### Example 2: Site with JSON-LD

```python
def parse_product_page(self, soup, url):
    script = soup.find('script', type='application/ld+json')
    if script:
        product_data = json.loads(script.string)

        offers = product_data.get('offers', {})

        return {
            'name': product_data.get('name'),
            'price': float(offers.get('price', 0)),
            'currency': offers.get('priceCurrency'),
            'url': product_data.get('url')
        }
```

### Example 3: Site with Data Attributes

```python
def parse_listing_page(self, soup, url):
    products = []

    for container in soup.select('.product-card'):
        # Price is in data attribute
        price = container.get('data-price')
        sale_price = container.get('data-sale-price')

        products.append({
            'name': container.select_one('.title').text,
            'current_price': float(sale_price or price),
            'original_price': float(price),
            'is_on_sale': bool(sale_price)
        })

    return products
```

---

## Tips & Tricks

### Tip 1: Check Mobile Site
Mobile sites often have simpler structure and less protection:
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
}
response = requests.get(url, headers=headers)
```

### Tip 2: Look for Price in Page Title/Meta
```python
# Sometimes price is in meta tags
meta_price = soup.find('meta', property='product:price:amount')
if meta_price:
    price = meta_price.get('content')
```

### Tip 3: Use Browser Console to Find Data
```javascript
// In browser console
console.log(window.productData);
console.log(window.dataLayer);
console.log(document.querySelectorAll('[data-price]'));
```

### Tip 4: Inspect Network Payloads
Some sites send product data in form payloads:
```python
# In DevTools → Network → Payload tab
# Copy as cURL, convert to Python requests
```

---

## Troubleshooting

### "No price found"
- ✅ Check if JavaScript is required (use Selenium)
- ✅ Check page source for hidden data
- ✅ Monitor network calls for APIs
- ✅ Try mobile site
- ✅ Check if login is required

### "API requires authentication"
- ✅ Look for auth tokens in cookies/headers
- ✅ Try simulating a logged-out session
- ✅ Some sites work with guest checkout

### "Prices are region-specific"
- ✅ Set location in cookies
- ✅ Use proxy for specific region
- ✅ Check if site has `/us/`, `/uk/` URLs

---

## Decision Tree

```
Start: Need to scrape prices from cart-required site
│
├─ Can you find an API endpoint?
│  ├─ YES → Use API approach ✅
│  └─ NO → Continue
│
├─ Is there JSON-LD or __NEXT_DATA__?
│  ├─ YES → Extract from structured data ✅
│  └─ NO → Continue
│
├─ Are there data-price attributes?
│  ├─ YES → Extract from data attributes ✅
│  └─ NO → Continue
│
├─ Is price in JavaScript variables?
│  ├─ YES → Extract from JS ✅
│  └─ NO → Continue
│
└─ No other option?
   └─ Use Selenium cart interaction ⚠️
```

---

## Summary

**Best to Worst:**
1. 🥇 **API calls** - Fast, reliable, clean
2. 🥈 **Hidden data** - Fast, simple, no extra requests
3. 🥉 **Cart interaction** - Slow, complex, last resort

**Always try approaches 1 and 2 before resorting to 3!**

**Time Investment:**
- Finding APIs: 10-30 minutes
- Checking hidden data: 5-10 minutes
- Setting up cart interaction: 1-2 hours

**Which to implement first?**
Start with hidden data extraction (easiest to check), then look for APIs, then cart interaction only if absolutely necessary.

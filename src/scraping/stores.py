"""
Multi-store configuration for scraping.
Each store defines platform, URL, name, geography, and platform-specific settings.
"""

SHOPIFY_STORES = [
    {
        "url": "https://ruggable.com",
        "name": "Ruggable",
        "geography": "US",
        "collections": ["all", "area-rugs", "runner-rugs"],
    },
    {
        "url": "https://www.turtlebeach.com",
        "name": "Turtle Beach",
        "geography": "US",
        "collections": ["all"],
    },
    {
        "url": "https://hiutdenim.co.uk",
        "name": "Hiut Denim",
        "geography": "UK",
        "collections": ["all"],
    },
    {
        "url": "https://www.fashionnova.com",
        "name": "Fashion Nova",
        "geography": "US",
        "collections": ["all"],
    },
    {
        "url": "https://www.deathwishcoffee.com",
        "name": "Death Wish Coffee",
        "geography": "US",
        "collections": ["all"],
    },
]

WOOCOMMERCE_STORES = [
    {
        "url": "https://danosseasoning.com",
        "name": "Dan-O's Seasoning",
        "geography": "US",
    },
    {
        "url": "https://nalgene.com",
        "name": "Nalgene",
        "geography": "US",
    },
    {
        "url": "https://www.nutribullet.com",
        "name": "NutriBullet",
        "geography": "US",
    },
]

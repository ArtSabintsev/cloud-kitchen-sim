# Seed Data for Cloud Kitchen Management System
# Contains all data tables: recipes, inventory, orders, restock, and status

# 1. Recipe list: List of recipes with required ingredients and their quantities in grams
recipes = [
    {
        "recipe_id": 1,
        "name": "Margherita Pizza",
        "ingredients": [
            {"name": "Flour", "qty_grams": 300},
            {"name": "Tomato Sauce", "qty_grams": 100},
            {"name": "Mozzarella Cheese", "qty_grams": 150}
        ]
    },
    {
        "recipe_id": 2,
        "name": "Chicken Burger",
        "ingredients": [
            {"name": "Chicken Breast", "qty_grams": 200},
            {"name": "Bun", "qty_grams": 100},
            {"name": "Lettuce", "qty_grams": 50}
        ]
    },
    {
        "recipe_id": 3,
        "name": "Caesar Salad",
        "ingredients": [
            {"name": "Romaine Lettuce", "qty_grams": 200},
            {"name": "Caesar Dressing", "qty_grams": 50},
            {"name": "Croutons", "qty_grams": 30}
        ]
    },
    {
        "recipe_id": 4,
        "name": "Pasta Alfredo",
        "ingredients": [
            {"name": "Fettuccine Pasta", "qty_grams": 200},
            {"name": "Cream", "qty_grams": 100},
            {"name": "Parmesan Cheese", "qty_grams": 50}
        ]
    },
    {
        "recipe_id": 5,
        "name": "Chocolate Cake",
        "ingredients": [
            {"name": "Flour", "qty_grams": 250},
            {"name": "Chocolate", "qty_grams": 150},
            {"name": "Sugar", "qty_grams": 100}
        ]
    }
]

# 2. Inventory: Ingredients with quantity in grams and expiry date
inventory = [
    {"ingredient": "Flour", "qty_grams": 10000, "expiry_date": "2026-05-12"},
    {"ingredient": "Tomato Sauce", "qty_grams": 10000, "expiry_date": "2026-11-15"},
    {"ingredient": "Mozzarella Cheese", "qty_grams": 10000, "expiry_date": "2026-10-20"},
    {"ingredient": "Chicken Breast", "qty_grams": 10000, "expiry_date": "2026-10-10"},
    {"ingredient": "Romaine Lettuce", "qty_grams": 10000, "expiry_date": "2026-05-12"},
    {"ingredient": "Caesar Dressing", "qty_grams": 10000, "expiry_date": "2026-10-15"},
    {"ingredient": "Croutons", "qty_grams": 10000, "expiry_date": "2026-10-18"},
    {"ingredient": "Bun", "qty_grams": 10000, "expiry_date": "2026-10-09"},
    {"ingredient": "Lettuce", "qty_grams": 10000, "expiry_date": "2026-10-09"},
    {"ingredient": "Fettuccine Pasta", "qty_grams": 10000, "expiry_date": "2026-01-31"},
    {"ingredient": "Cream", "qty_grams": 10000, "expiry_date": "2026-10-12"},
    {"ingredient": "Parmesan Cheese", "qty_grams": 10000, "expiry_date": "2026-10-15"},
    {"ingredient": "Chocolate", "qty_grams": 10000, "expiry_date": "2026-01-15"},
    {"ingredient": "Sugar", "qty_grams": 10000, "expiry_date": "2026-05-12"}
]

# 3. Orders: List of orders with items and quantities
orders = [
    {
        "order_id": 1,
        "brand": "Taco Bell",
        "items": [
            {"item": "Margherita Pizza", "qty": 2},
            {"item": "Caesar Salad", "qty": 1}
        ]
    },
    {
        "order_id": 2,
        "brand": "Subway",
        "items": [
            {"item": "Chicken Burger", "qty": 1}
        ]
    },
    {
        "order_id": 3,
        "brand": "Subway",
        "items": [
            {"item": "Pasta Alfredo", "qty": 1},
            {"item": "Chocolate Cake", "qty": 1}
        ]
    },
    {
        "order_id": 4,
        "brand": "Subway",
        "items": [
            {"item": "Margherita Pizza", "qty": 1}
        ]
    },
    {
        "order_id": 5,
        "brand": "Taco Bell",
        "items": [
            {"item": "Chicken Burger", "qty": 45},
            {"item": "Caesar Salad", "qty": 1}
        ]
    }
]

# 4. Restock: Items that need to be brought for the next day
restock = [
    {"item": "Flour", "qty_needed_grams": 2000, "reason": "Running low stock"},
    {"item": "Chicken Breast", "qty_needed_grams": 1500, "reason": "Running low stock"},
    {"item": "Romaine Lettuce", "qty_needed_grams": 500, "reason": "Expiring soon"},
    {"item": "Cream", "qty_needed_grams": 1000, "reason": "Running low stock"},
    {"item": "Chocolate", "qty_needed_grams": 800, "reason": "Out of stock"}
]

# 5. Status: Delivery status with remarks
status = [
    {"order_id": 1, "delivered": True, "remark": "Delivered"},
    {"order_id": 2, "delivered": False, "remark": "Not Delivered"},
    {"order_id": 3, "delivered": True, "remark": "Delivered"},
    {"order_id": 4, "delivered": False, "remark": "Not Delivered"},
    {"order_id": 5, "delivered": True, "remark": "Delivered"}
]


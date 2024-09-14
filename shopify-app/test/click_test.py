import requests
import json
import uuid
from termcolor import colored
from rich import print as rprint

# Define the URL
url = "http://127.0.0.1:8003/run-reasoning-agent"

# Define the headers
headers = {
    "Content-Type": "application/json",
    "Accept": "text/event-stream",
}

# Single turn test
body = {
    'session': {
        'id': 1234,
    },
    'messages': [
        {
            "role": "user",
             "content": "How much is a medium pizza?"
        },
    ]
}

data  = {
    'messages': [
        {
            'role': 'assistant',
            'content': '### Tools Used Before Responding to Customer\n\n* get_products: Calling get_products with input empty dictionary returned a list of products including product with ID 8499273400570 and title Chicken Wings with option Size, product with ID 8499278512378 and title Drinks with option Flavor, and product with ID 8498162335994 and title Pizza with option Size. Relevant information to the conversation might include the products available.\n* get_product_details:Calling get_product_details with input product_id 8498162335994 returned product details for Pizza with variants Small (variant_id 46198934175994, price 9.95), Medium (variant_id 46198934208762, price 12.95), Large (variant_id 46198934274298, price 16.95), and Extra Large (variant_id 46198934307066, price 19.95).\n\n\n### Audio Response to Customer\n\nThe price of a medium pizza is $12.95.'
        }
    ],
    'session': {'id': 1234},
    'node': 'WidgetOutput',
    'reason': "TBD",
    'output': [
        {
            'type': 'shopify-product-list',
            'details': "{'product_id': 8498162335994, 'product_title': 'Pizza', 'product_variants': [{'variant_id': 46198934175994, 'variant_name': 'Small', 'price': '9.95', 'product_variant_sku': 'pizza_small'}, {'variant_id': 46198934208762,  'variant_name': 'Medium', 'price': '12.95', 'product_variant_sku': 'pizza_medium'}, {'variant_id': 46198934274298, 'variant_name': 'Large', 'price': '16.95', 'product_variant_sku': 'pizza_large'}, {'variant_id': 46198934307066, 'variant_name': 'Extra Large', 'price': '19.95', 'product_variant_sku': 'pizza_extra_large'}]}",
            'available-tools': [
                {
                    'tool': 'add_item_to_cart',
                    'arguments': [
                        'variant_id'
                    ],
                },
                {
                    'tool': 'get_nutrition_facts',
                    'arguments': [
                        'variant_id'
                    ],
                }
            ]
        }
    ]
}

# multi turn tests
body = {
    'session': {
        'id': 1234,
    },
    'action': {
        'type': 'tool',
        'details': {
            'tool': 'add_item_to_cart',
            'parameters': {
                'variant_id': 46198934208762,
                'quantity': 1
            },
        },
    },
    'messages': [
        {
            "role": "user",
             "content": "How much is a medium pizza?"
        },
        {
            "role": "assistant",
            "content": "### Tools Used Before Responding to Customer\n\n* get_products: Calling get_products with input empty dictionary returned a list of products including product with ID 8499273400570 and title Chicken Wings with option Size, product with ID 8499278512378 and title Drinks with option Flavor, and product with ID 8498162335994 and title Pizza with option Size. Relevant information to the conversation might include the products available.\n* get_product_details:Calling get_product_details with input product_id 8498162335994 returned product details for Pizza with variants Small (variant_id 46198934175994, price 9.95), Medium (variant_id 46198934208762, price 12.95), Large (variant_id 46198934274298, price 16.95), and Extra Large (variant_id 46198934307066, price 19.95).\n\n\n### Audio Response to Customer\n\nThe price of a medium pizza is $12.95."
        },
    ]
}

# Send the POST request
response = requests.post(url, headers=headers, data=json.dumps(body), stream=True)

try:
    # Stream the response
    for line in response.iter_lines(decode_unicode=True):
        if line.startswith('data: '):
            rprint('\n\n-----------------')
            data = json.loads(line[6:])
            rprint(data)
except KeyboardInterrupt:
    print("\nScript interrupted by user")
finally:
    response.close()
    print("Connection closed")

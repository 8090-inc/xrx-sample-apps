import shopify
import os
import json
from dotenv import load_dotenv
load_dotenv()

import redis

# set up the redis client
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_client = redis.Redis(host=redis_host, port=6379, db=0)

API_KEY = os.environ.get('SHOPIFY_API_KEY', '')
PASSWORD = os.environ.get('SHOPIFY_TOKEN', '')
SHOP_NAME = os.environ.get('SHOPIFY_SHOP', '')
SHOP_GID = os.environ.get('SHOPIFY_SHOP_GID', '')

def init_shopify_connect():
    if not API_KEY or not PASSWORD or not SHOP_NAME or not SHOP_GID:
        raise ValueError("API_KEY, PASSWORD, SHOP_NAME, and SHOP_GID environment variables must be set.")
    shop_url = f"https://{API_KEY}:{PASSWORD}@{SHOP_NAME}.myshopify.com/admin"
    shopify.ShopifyResource.set_site(shop_url)
    return shopify.Shop.current()

# TODO: This has to be reused in the tools.py file and its not optimal to have it how it is now
def init_shopify_graphql_client():
    shop_url = f"https://{API_KEY}:{PASSWORD}@{SHOP_NAME}.myshopify.com/admin"
    session = shopify.Session(shop_url, '2024-04', PASSWORD)
    shopify.ShopifyResource.activate_session(session)
    return shopify.GraphQL()


def get_product_image(product_id: int, variant_id: int | None = None) -> str:
    """
    Get the first image associated with a specific variant of a product.
    
    Args:
    product_id (int): The ID of the product.
    variant_id (int | None): The ID of the variant (optional).
    
    Returns:
    str: The URL of the first image associated with the variant, or None if no image is found.
    """
    try:        
        img_key = f'product-image-{product_id}{"-" + str(variant_id) if variant_id else ""}'
        cached_result = redis_client.get(img_key)
        if cached_result:
            return cached_result.decode('utf-8')
        
        product = shopify.Product.find(product_id)
        if not product.images:
            return None
        
        image_src = product.images[0].src
        
        if variant_id:
            variant = next((v for v in product.variants if v.id == variant_id), None)
            if variant and variant.image_id:
                variant_image = next((img for img in product.images if img.id == variant.image_id), None)
                if variant_image:
                    image_src = variant_image.src
        redis_client.set(img_key, image_src)
        return image_src
    except Exception as e:
        error_message = f"Error fetching product image for product_id: {product_id}{', variant_id: ' + variant_id if variant_id else ''}"
        error_message += f": {str(e)}"
        print(error_message)
        return None

def populate_images_for_product_list(products):
    for product_id, product_info in products.items():
        product_image = get_product_image(product_id)
        if product_image:
            product_info['product_image_src'] = product_image
            continue
    return products

def populate_images_for_product_details(product):
    product['product_image_src'] = get_product_image(product['product_id'])
    for variant in product['product_variants']:
        variant['product_image_src'] = get_product_image(product['product_id'], variant['variant_id'])
    return product

def populate_images_for_cart_summary(cart_summary):
    for item in cart_summary['cart_summary']['line_items']:
        item['product_image_src'] = get_product_image(item['product_id'])
    return cart_summary

def get_cart_summary_from_object(order):
    """Returns a summary of the order with the total price and line items including SKU.
    """
    order_summary = {
        'cart_summary':
            {
                'total_price': order.total_price,
                'line_items': []
            }
    }
    for line_item in order.line_items:
        line_item_info = {
            'name': line_item.title,
            'quantity': line_item.quantity,
            'price': line_item.price,
            'variant_id': line_item.variant_id,
            'product_id': line_item.product_id,
            'item_variant_sku': line_item.sku,
            "variant_title": line_item.variant_title if line_item.variant_title else None,
        }
        order_summary['cart_summary']['line_items'].append(line_item_info)
    return order_summary

def get_variant_id_from_sku(item_variant_sku, graphql_client):
    """Returns the variant ID from the SKU.
    """
    query = """
    {
        productVariants(first: 1, query: "sku:%s") {
            edges {
                node {
                    id
                    sku
                    product {
                        id
                        title
                    }
                }
            }
        }
    }
    """ % item_variant_sku
    response = graphql_client.execute(query)
    variants = json.loads(response)['data']['productVariants']['edges']
    variant_id = int(variants[0]['node']['id'].replace('gid://shopify/ProductVariant/', ''))
    return variant_id

def make_new_blank_cart(variant_id, quantity):
    """Creates a new draft order with no items in the cart.
    """

    draft_order = shopify.DraftOrder.create({
        "line_items": [
            {
                "variant_id": variant_id,
                "quantity": quantity,
            }
        ]
    })

    # Save the draft order
    if draft_order.save():
        print(f"Empty draft order created successfully. ID: {draft_order.id}")
    else:
        print("Failed to create draft order.")
        print(draft_order.errors.full_messages())

    return draft_order.id
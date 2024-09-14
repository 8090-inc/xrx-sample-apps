import os
import shopify
from shopify.resources import LineItem
from ..utils.shopify import (
    init_shopify_connect,
    get_cart_summary_from_object,
    make_new_blank_cart,
)
from ..context_manager import session_var
from agent_framework import observability_decorator
from dotenv import load_dotenv
import json

load_dotenv()

SHOP = init_shopify_connect()
API_KEY = os.environ.get('SHOPIFY_API_KEY', '')
PASSWORD = os.environ.get('SHOPIFY_TOKEN', '')
SHOP_NAME = os.environ.get('SHOPIFY_SHOP', '')

@observability_decorator(name="get_products")
def get_products():
    """
    Overview:
    Fetches all active products from the shop and returns a comprehensive dictionary representing the shop's available products.

    When to use this tool:
    - When you need to look up a `product_id` for an item.
    - When you need to know more details about a product, such as its variants and prices.

    Returns:
    A JSON dictionary with product IDs as keys and dictionaries as values, each containing:
    - 'product_id' (int): The ID of the product.
    - 'product_title' (str): The title of the product.
    - 'options' (list): A list of dictionaries, each containing:
      - 'option_title' (str): The name of the product option. Examples might include Size, Flavor, Color, etc.
    """
    try:
        products = shopify.Product.find()
        product_dict = {}
        for product in products:
            if product.status.lower() == 'active':
                product_dict_item = {
                    'product_id': product.id,
                    'product_title': product.title,
                    'options': []
                }
                for option in product.options:
                    option_info = {
                        'option_title': option.name,
                    }
                    product_dict_item['options'].append(option_info)
                product_dict[str(product.id)] = product_dict_item
        return json.dumps(product_dict)
    except Exception as e:
        raise e

@observability_decorator(name="get_product_details")
def get_product_details(product_id: int):
    """
    Overview:
    Accurately retrieves detailed information about a specific product by its ID.
    This tool contains all of the information available about a given product.
    If any information about a product is not available from this tool output, you must assume that the information does not exist in this store.

    When to use this tool:
    - Only once you have called the get_products() tool and know the exact product_id.
    - When you need to know more details about a product, such as its variants and prices.

    Args:
    product_id (int): The ID of the product.

    Returns:
    A JSON object containing:
    - 'product_id' (int): The ID of the product.
    - 'product_title' (str): The title of the product.
    - 'product_variants' (list): A list of dictionaries, each containing:
      - 'variant_id' (int): The ID of the product variant.
      - 'variant_name' (str): The name of the product variant.
      - 'price' (str): The price of the variant.
      - 'product_variant_sku' (str): The SKU of the variant.
    """
    try:
        product = shopify.Product.find(product_id)
        if not product:
            return f"Product with ID {product_id} not found."

        product_item_details = {
            'product_id': product.id,
            'product_title': product.title,
            'product_variants': []
        }

        for variant in product.variants:
            variant_info = {
                'variant_id': variant.id,
                'variant_name': variant.title,
                'price': variant.price,
                'product_variant_sku': variant.sku,
            }
            product_item_details['product_variants'].append(variant_info)

        return json.dumps(product_item_details)
    except Exception as e:
        raise e

@observability_decorator(name="add_item_to_cart")
def add_item_to_cart(variant_id: int, quantity: int):
    """
    Name: add_item_to_cart

    Description: 
    Adds a quantity of the specified product variant to the customer's cart.
    Correctly add items to the cart based on user specifications

    Overview:
    Adds a specified quantity of an item to the customer's current cart.

    When to use this tool:
    - Only once you have used the get_product_details() tool and know the exact variant_id.
    - Once a customer explicitly tells you to add an item to the cart or change an item in the cart.

    Input Args:
    variant_id (int): The ID of the product variant.
    quantity (int): The quantity to add to the cart.
    
    Rules: Verify that the added item matches the requested variant_id. If there's a mismatch, return an error message. 

    Returns:
    A JSON object containing:
    - 'total_price' (float): The total price of the cart.
    - 'line_items' (list): A list of line items in the cart, each containing:
      - 'title' (str): The title of the product.
      - 'quantity' (int): The quantity of the product.
      - 'price' (str): The price of the product.
      - 'variant_id' (int): The ID of the product variant.
      - 'product_variant_sku' (str): The SKU of the product variant.
    """
    try:
        shop_url = f"https://{API_KEY}:{PASSWORD}@{SHOP_NAME}.myshopify.com/admin"
        session = shopify.Session(shop_url, '2024-04', PASSWORD)
        shopify.ShopifyResource.activate_session(session)

        session_data = session_var.get()
        cart_id = session_data.get('cart_id')

        if 'cart_id' not in session_data.keys():
            cart_id = make_new_blank_cart(variant_id, quantity)
            session_data['cart_id'] = cart_id
            print(f'No cart id was found in the session input. Creating a new cart id: {cart_id}')
            cart = shopify.DraftOrder.find(cart_id)
            cart.line_items = [{
                "variant_id": variant_id,
                "quantity": quantity,
            }]
            cart.save()
            cart_id = cart.id
            session_var.set(session_data)
        else:
            cart = shopify.DraftOrder.find(cart_id)
            new_line_item = LineItem({
                "variant_id": variant_id,
                "quantity": quantity
            })
            cart.line_items.append(new_line_item)
            cart.save()

        summary = get_cart_summary_from_object(cart)
        return json.dumps(summary)
    except Exception as e:
        raise e

@observability_decorator(name="delete_item_from_cart")
def delete_item_from_cart(variant_id: int):
    """
    Overview:
    Removes an item from the current cart by its variant ID.

    Warnings:
    If no cart exists, raises an error.
    Verify that cart updates match user requests

    When to use this tool:
    - Only once you have used the get_product_details() tool and know the exact variant_id.
    - Once a customer explicitly tells you to delete an item from the cart or asks for a change in the cart.

    Args:
    variant_id (int): The ID of the product variant.

    Returns:
    A JSON object containing the summary of the updated cart, including:
    - 'total_price' (float): The total price of the cart.
    - 'line_items' (list): A list of line items in the cart, each containing:
      - 'title' (str): The title of the product.
      - 'quantity' (int): The quantity of the product.
      - 'price' (str): The price of the product.
      - 'variant_id' (int): The ID of the product variant.
      - 'product_variant_sku' (str): The SKU of the product variant.
    """
    try:
        shop_url = f"https://{API_KEY}:{PASSWORD}@{SHOP_NAME}.myshopify.com/admin"
        session = shopify.Session(shop_url, '2024-04', PASSWORD)
        shopify.ShopifyResource.activate_session(session)

        session_data = session_var.get()
        cart_id = session_data.get('cart_id')

        if not cart_id:
            return "No cart exists to delete items from. Please add items to the cart first."

        cart = shopify.DraftOrder.find(cart_id)
        
        cart.line_items = [line_item for line_item in cart.line_items if line_item.variant_id != variant_id]
        if not cart.line_items:
            # Delete the cart if it's empty
            cart.destroy()
            session_data = session_var.get()
            session_data.pop('cart_id', None)
            session_var.set(session_data)
            return json.dumps({
                'cart_summary':
                    {
                        'total_price': 0,
                        'line_items': []
                    }   
            })
                                
        cart.save()
        summary = get_cart_summary_from_object(cart)
        return json.dumps(summary)
    except Exception as e:
        raise e

@observability_decorator(name="get_cart_summary")
def get_cart_summary():
    """
    Overview:
    Returns a detailed summary of the current cart.

    Warnings:
    If no cart exists, returns an empty cart summary.

    Returns:
    A JSON object containing:
    - 'total_price' (float): The total price of the cart.
    - 'line_items' (list): A list of line items in the cart, each containing:
      - 'title' (str): The title of the product.
      - 'quantity' (int): The quantity of the product.
      - 'price' (str): The price of the product.
      - 'variant_id' (int): The ID of the product variant.
      - 'product_variant_sku' (str): The SKU of the product variant.
    """
    try:
        session_data = session_var.get()
        cart_id = session_data.get('cart_id')

        if not cart_id:
            cart_summary = {
                'cart_summary':
                    {
                        'total_price': 0,
                        'line_items': []
                    }   
            }
            return json.dumps(cart_summary)

        cart = shopify.DraftOrder.find(cart_id)
        summary = get_cart_summary_from_object(cart)
        return json.dumps(summary)
    except Exception as e:
        raise e

# TODO: This tool should use a good dictionary output instead of a string.
@observability_decorator(name="submit_cart_for_order")
def submit_cart_for_order():
    """
    Overview:
    Finalizes and submits the current cart for processing as an order.

    Warnings:
    If no cart exists, notifies the user that no cart is available.
    If a cart has already been submitted, notifies the user.

    When to use this tool:
    - Once a customer explicitly tells you to submit the cart for order.

    Returns:
    A confirmation message with the order's confirmation number.
    """
    try:
        session_data = session_var.get()
        cart_id = session_data.get('cart_id')

        if not cart_id:
            return "No cart exists to complete. Please add items to the cart first."

        cart = shopify.DraftOrder.find(cart_id)
        cart.complete()

        submitted_order_id = session_data.get('submitted_order_id')
        if submitted_order_id:
            return 'Your cart has already been submitted with confirmation number: ' + str(submitted_order_id)

        session_data['submitted_order_id'] = cart.order_id
        session_var.set(session_data)

        return 'Your cart has been submitted with confirmation number: ' + str(cart.order_id)
    except Exception as e:
        raise e

# TODO: This tool should use a good dictionary output instead of a string.
@observability_decorator(name="get_order_status")
def get_order_status():
    """
    Overview:
    Checks and returns the fulfillment status of the order.

    Warnings:
    If no order has been submitted, informs the user.

    Returns:
    The status of the order. Possible statuses include:
    - 'The order is confirmed and being processed with confirmation number: [confirmation_number]'
    - 'The order has been delivered.'
    - 'No order has been submitted yet.'
    """
    try:
        session_data = session_var.get()
        submitted_order_id = session_data.get('submitted_order_id')

        if submitted_order_id:
            order = shopify.Order.find(submitted_order_id)
            if not order.fulfillment_status:
                return 'The order is confirmed and being processed with confirmation number: ' + str(submitted_order_id)
            else:
                return 'The order has been delivered.'

        return 'No order has been submitted yet.'
    except Exception as e:
        raise e

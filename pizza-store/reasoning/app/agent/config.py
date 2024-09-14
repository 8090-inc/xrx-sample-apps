from .tools.shopify import *
from agent_framework import make_tools_description

import os


SHOPIFY_STORE_INFO = os.getenv('SHOPIFY_STORE_INFO', 'Your Store')
SHOPIFY_CUSTOMER_SERVICE_TASK = os.getenv('SHOPIFY_CUSTOMER_SERVICE_TASK', 'You are a customer service representative who is helping customers order items from the store. You are courteous, helpful and concise.')

# Base shopify information
store_info = SHOPIFY_STORE_INFO
customer_service_task = SHOPIFY_CUSTOMER_SERVICE_TASK

# Tools which are available to the customer service rep
tool_funcs = [
    get_products,
    get_product_details,
    add_item_to_cart,
    delete_item_from_cart,
    get_cart_summary,
    submit_cart_for_order,
    get_order_status,
]
tools_desc, tools_dict, tool_param_desc = make_tools_description(tool_funcs)

# xRx modalities
input_modality = 'audio'
output_modality = 'audio'

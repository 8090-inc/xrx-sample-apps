from ..base import Node
import logging
import os
import json
from agent_framework import observability_decorator
from agent.utils.shopify import (
    populate_images_for_product_list,
    populate_images_for_product_details,
    populate_images_for_cart_summary,
)

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def match_widget_to_tool(tool, tool_output):
    widget_output = {}
    if tool == 'get_products':
        tool_output = populate_images_for_product_list(tool_output)
        widget_output = {
            'type': 'shopify-product-list',
            'details': json.dumps(tool_output),
            'available-tools': [
                {
                    'tool': 'get_product_details',
                    'arguments': [
                        'product_id'
                    ],
                },
            ]
        }
    elif tool == 'get_product_details':
        tool_output = populate_images_for_product_details(tool_output)
        widget_output = {
            'type': 'shopify-product-details',
            'details': json.dumps(tool_output),
            'available-tools': [
                {
                    'tool': 'add_item_to_cart',
                    'arguments': [
                        'variant_id'
                    ],
                },
            ]
        }
    elif tool in ['add_item_to_cart', 'delete_item_from_cart', 'get_cart_summary']:
        tool_output = populate_images_for_cart_summary(tool_output)
        widget_output = {
            'type': 'shopify-cart-summary',
            'details': json.dumps(tool_output),
            'available-tools': [
                {
                    'tool': 'submit_cart_for_order',
                    'arguments': [],
                },
            ]
        }
    elif tool == 'submit_cart_for_order':
        try:
            if 'confirmation number' in tool_output:
                confirmation_number = int(tool_output.split('confirmation number:')[1].strip())
                widget_details = {
                    'message': tool_output,
                    'confirmation_number': confirmation_number,
                    'confirmation_link': f'https://shopify.com/{os.getenv("SHOPIFY_SHOP_GID")}/account/orders/{confirmation_number}',
                }
            else:
                widget_details = tool_output
            widget_output = {
                'type': 'shopify-order-confirmation',
                'details': json.dumps(widget_details),
                'available-tools': [
                    {
                        'tool': 'get_order_status',
                        'arguments': [],
                    },
                ]
            }
        except Exception as e:
            logger.exception(f"An error occurred in match_widget_to_tool: {e}")
    elif tool == 'get_order_status':
        try:
            if 'confirmation number' in tool_output:
                confirmation_number = int(tool_output.split('confirmation number:')[1].strip())
                widget_details = {
                    'message': tool_output,
                    'confirmation_number': confirmation_number,
                    'confirmation_link': f'https://shopify.com/{os.getenv("SHOPIFY_SHOP_GID")}/account/orders/{confirmation_number}',
                }
            else:
                widget_details = tool_output
            widget_output = {
                'type': 'shopify-order-status',
                'details': json.dumps(widget_details),
            }
        except Exception as e:
            logger.exception(f"An error occurred in match_widget_to_tool: {e}")
    return widget_output

class Widget(Node):
    def __init__(self, name, attributes):
        super().__init__(name, attributes)

    @observability_decorator('Widget')
    async def process(self, messages: list, input: dict, context=None):
        try:
            logger.info("Widget is processing the input")
            tool_output = input.get('output', {})
            tool = input.get('tool', '')
            parameters = input.get('parameters', {})
            memory = input.get('memory', {})

            # Create the output similar to the data object
            widget_output = match_widget_to_tool(tool, tool_output)
            full_output = {
                'node': self.id,
                'reason': "hard coded widget creation",
                'output': widget_output,
                'memory': memory,
                'parameters': parameters,
            }
            logger.info("Widget finished processing")
            yield full_output
        except Exception as e:
            logger.exception(f"An error occurred in Widget")
            raise e

    async def get_successors(self, result: dict):
        successors = []
        return successors

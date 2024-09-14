from ..base import Node
import asyncio
import logging
import json
from agent.config import tools_dict, tool_param_desc
from agent_framework import observability_decorator
import copy

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class ExecuteTool(Node):
    def __init__(self, name, attributes):
        super().__init__(name, attributes)

    @observability_decorator('ExecuteTool')
    async def process(self, messages: list, input: dict, context=None):
        try:
            logger.info(f"ExecuteTool is executing input {input}")
            tool = input.get('tool','')
            tool_arguments = input.get('parameters',{})
            tool_response = tools_dict[tool].call(**tool_arguments)
            
            try:
                tool_call_output = json.loads(tool_response.content)
            except json.JSONDecodeError:
                tool_call_output = tool_response.content

            await asyncio.sleep(0)
            yield {
                'node': self.id,
                'reason': 'Output of tool',
                'output': tool_call_output,
                'tool': input['tool'],
                'parameters': input.get('parameters', {}),
                'memory': input.get('memory', {})
            }
            logger.info(f"ExecuteTool finished processing Tool output: {tool_call_output}")
        except Exception as e:
            logger.exception(f"An error occurred in ExecuteTool")
            raise e

    async def get_successors(self, result: dict):
        successors = []
        
        # output has to be copied to avoid overwriting in memory
        output = result.get('output', '')

        if result.get('tool', '') in [
            'get_products',
            'get_product_details',
            'add_item_to_cart',
            'delete_item_from_cart',
            'get_cart_summary',
            'submit_cart_for_order',
            'get_order_status',
        ]:
            successors.append(("Widget", copy.deepcopy({
                'output': output,
                'tool': result.get('tool',''),
                'parameters': result.get('parameters',{}),
                'memory': result.get('memory', {}),
            })))
        
        successors.append(("ConvertNaturalLanguage", copy.deepcopy({
            'output': output,
            'tool': result.get('tool',''),
            'parameters': result.get('parameters',{}),
            'memory': result.get('memory', {}),
        })))
        return successors

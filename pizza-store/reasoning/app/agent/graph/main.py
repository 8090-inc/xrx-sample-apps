import asyncio
from .base import *
from .nodes.routing import Routing
from .nodes.choose_tool import ChooseTool
from .nodes.customer_response import CustomerResponse
from .nodes.convert_natural_language import ConvertNaturalLanguage
from .nodes.identify_tool_params import IdentifyToolParams
from .nodes.execute_tool import ExecuteTool
from .nodes.widget import Widget
from .nodes.task_description_response import TaskDescriptionResponse

import logging
import json

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

USER_TOOL_CALL_PROMPT = '''\
### Action taken my the user on the frontend

Tool: {tool}
Parameters: {parameters}

### User current status
<awaiting next steps>
'''

async def agent_graph(messages, task_id='', action={}, memory=None):

    # define all nodes
    node_routing = Routing('Routing', {})
    node_choose_tool = ChooseTool('ChooseTool', {})
    node_convert_natural_language = ConvertNaturalLanguage('ConvertNaturalLanguage', {})
    node_identify_tool_params = IdentifyToolParams('IdentifyToolParams', {})
    node_execute_tool = ExecuteTool('ExecuteTool', {})
    node_customer_response = CustomerResponse('CustomerResponse', {})
    node_widget = Widget('Widget', {})
    node_task_description = TaskDescriptionResponse('TaskDescriptionResponse', {})

    # define the graph by putting all nodes in the graph construct DO NOT FORGET THIS
    graph = Graph()
    graph.add_node(node_routing)
    graph.add_node(node_choose_tool)
    graph.add_node(node_customer_response)
    graph.add_node(node_convert_natural_language)
    graph.add_node(node_identify_tool_params)
    graph.add_node(node_execute_tool)
    graph.add_node(node_widget)
    graph.add_node(node_task_description)

    # decide where to enter the graph if there is a tool call
    if action == {}:
        starting_node = node_routing.id
        input_dict = {'memory': memory}
    
    elif action['type'] == 'tool':
        # add the user message to the message chain
        tool = action['details']['tool']
        parameters = action['details']['parameters']
        user_prompt = USER_TOOL_CALL_PROMPT.format(tool=tool, parameters=parameters)
        messages.append(
            {
                'role': 'user',
                'content': user_prompt
            },
        )
        starting_node = node_execute_tool.id

        # add the tool call to the input dict which will be sent to the graph
        input_dict = {'memory': memory}
        input_dict['tool'] = action['details']['tool']
        input_dict['parameters'] = action['details']['parameters']
    logger.info(f"Starting traversal at node: {starting_node}")

    # start the graph traversal
    try:
        async for result in graph.traverse(task_id, starting_node, messages, input_dict):
            logger.info(f"Result: {result}")
            yield json.dumps(result)
    except Exception as e:
        logger.exception(f"An error occurred during graph traversal")
        raise e

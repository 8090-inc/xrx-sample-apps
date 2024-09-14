from typing import List, Dict
from abc import ABC, abstractmethod
import networkx as nx
import asyncio
import logging
import redis
import os

# set up the redis client
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_client = redis.asyncio.Redis(host=redis_host, port=6379, db=0)

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Node(ABC):
    def __init__(self, id, attributes=None):
        self.id = id
        self.attributes = attributes or {}
    
    @abstractmethod
    async def process(self, messages: list, input: dict = None):
        pass

    @abstractmethod
    async def get_successors(self, result: dict):
        pass

    async def check_for_continue(self, task_id):
        redis_status = await redis_client.get('task-' + task_id)
        logger.info(f"Node {self.id} on task {task_id} has status {redis_status}")
        if redis_status == b'cancelled':
            return False
        return True

class Graph:
    def __init__(self):
        self.G = nx.DiGraph()

    def add_node(self, node):
        self.G.add_node(node.id, node=node)

    def add_edge(self, from_node, to_node):
        self.G.add_edge(from_node.id, to_node.id)
    
    async def traverse(self, task_id, start_node_id, messages, input=None, max_nodes=40):
        result_queue = asyncio.Queue()
        active_tasks = 0
        tasks_done = asyncio.Event()
        visited_nodes_count = 0  # Changed from set to counter

        async def execute_node(node_id, messages, input=None):
            nonlocal active_tasks, visited_nodes_count
            active_tasks += 1
            node = self.G.nodes[node_id]['node']
            result = None
            logger.info(f"Starting processing node: {node.id} on task id: {task_id}")

            # Check if the number of visited nodes exceeds 40
            if visited_nodes_count > max_nodes:
                error_message = f"Number of nodes in the search exceeds {max_nodes}. Breaking the search."
                logger.error(error_message)
                await result_queue.put({'error': error_message})
                tasks_done.set()
                return

            # start by processing the first node
            visited_nodes_count += 1  # Increment the counter
            try:
                async for intermediate_result in node.process(messages, input):
                    await result_queue.put(intermediate_result)
                    result = intermediate_result
                logger.info(f"Node finished processing: {node.id}")

                # now check redis to see if the node should continue based on the redis cluster
                should_continue = await node.check_for_continue(task_id)
                logger.info(f"Node {node.id} continue status: {should_continue}")
                if should_continue:
                    successors = await node.get_successors(result)
                else:
                    logger.info(f"Node {node.id} has been cancelled, returning no successors")
                    successors = []
                
                # continue processing the successors of the node if it hasn't been cancelled
                if successors:
                    logger.info('Successors: %s', [self.G.nodes[node_id]['node'].id for (node_id, input) in successors])
                    # Create tasks for each successor
                    tasks = [asyncio.create_task(execute_node(node_id, messages, input)) for (node_id, input) in successors]
                    
                    # Wait for all tasks to complete
                    await asyncio.gather(*tasks)
                else:
                    logger.info(f"No successors for node: {node.id}")

            # when an error occurs in a node, set an error to the queue and set the status in redis
            except Exception as e:
                error_message = f"An error occurred in node {node.id}"
                logger.exception(error_message)
                await result_queue.put({'error': error_message})
                await redis_client.set('task-' + task_id, 'finished-with-error')
                tasks_done.set()
            finally:
                active_tasks -= 1
                if active_tasks == 0:
                    tasks_done.set()

        # Start the execution of the initial node
        asyncio.create_task(execute_node(start_node_id, messages, input))

        # Iterate over the results in the queue
        while not tasks_done.is_set() or not result_queue.empty():
            if not result_queue.empty():
                result = await result_queue.get()
                if 'error' in result:
                    logger.info(f"Yielding error result from traverse: {result}")
                    yield result
                    return
                from pprint import pformat
                logger.info(f"Yielding result from traverse:\n{pformat(result, indent=2, width=100)}")
                yield result
            else:
                await asyncio.sleep(0.01)

        # Wait for all tasks to be done
        await tasks_done.wait()
        await result_queue.put(None)
        await redis_client.set('task-' + task_id, 'finished-with-success')

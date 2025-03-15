"""
Test script to list objects in Replit Object Storage with a specific prefix
"""

import logging
import sys
from replit.object_storage import Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def list_objects_with_prefix(prefix='chromadb/'):
    """List objects in Replit Object Storage with a specific prefix"""
    try:
        logger.info(f"Attempting to list objects with prefix: {prefix}")
        client = Client()
        objects = list(client.list(prefix=prefix))
        logger.info(f"Found {len(objects)} objects with prefix {prefix}")
        
        if not objects:
            logger.warning(f"No objects found with prefix {prefix}")
            # Try listing all objects to see what's there
            logger.info("Trying to list all objects (no prefix)...")
            all_objects = list(client.list())
            logger.info(f"Found {len(all_objects)} total objects")
            for obj in all_objects[:20]:  # List first 20 to avoid overwhelming output
                # Inspect the object to see what attributes it has
                obj_attrs = dir(obj)
                logger.info(f"Object attributes: {obj_attrs}")
                if hasattr(obj, 'name'):
                    logger.info(f"Object name: {obj.name}")
                elif hasattr(obj, 'key'):
                    logger.info(f"Object key: {obj.key}")
                else:
                    logger.info(f"Object: {obj}")
            return
            
        # List the found objects
        for obj in objects:
            # Inspect the first object to see what attributes it has
            if objects.index(obj) == 0:
                obj_attrs = dir(obj)
                logger.info(f"Object attributes: {obj_attrs}")
            
            if hasattr(obj, 'name'):
                logger.info(f"Object name: {obj.name}")
            elif hasattr(obj, 'key'):
                logger.info(f"Object key: {obj.key}")
            else:
                logger.info(f"Object: {obj}")
            
    except Exception as e:
        logger.error(f"Error listing objects: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    list_objects_with_prefix()
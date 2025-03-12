#!/usr/bin/env python3
import argparse
import json
import logging
from services.vector_store import VectorStore
from datetime import datetime

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def list_documents():
    """List all documents in the vector store"""
    vector_store = VectorStore.get_instance()
    debug_info = vector_store.get_debug_info()
    
    print("\nVector Store Contents:")
    print(f"Total Documents: {debug_info['document_count']}")
    print("\nDocuments:")
    for doc in debug_info['documents']:
        print(f"\nID: {doc['id']}")
        print(f"Filename: {doc['filename']}")
        print(f"Size: {doc['size']} bytes")
        print(f"Created: {doc['created_at']}")

def search_documents(query: str, limit: int = 3):
    """Search documents using semantic similarity"""
    vector_store = VectorStore.get_instance()
    results, error = vector_store.search(query=query, k=limit)
    
    if error:
        print(f"\nError: {error}")
        return
    
    print(f"\nSearch Results for: '{query}'")
    print(f"Found {len(results)} matches\n")
    
    for i, result in enumerate(results, 1):
        print(f"Match {i}:")
        print(f"Document: {result.metadata['filename']}")
        print(f"Similarity Score: {result.similarity_score:.2f}")
        print(f"Content:\n{result.content}\n")
        print("-" * 80)

def show_stats():
    """Show collection statistics"""
    vector_store = VectorStore.get_instance()
    debug_info = vector_store.get_debug_info()
    collection_info = debug_info['collection_info']
    
    print("\nChromaDB Collection Statistics:")
    print(f"Collection Name: {collection_info['name']}")
    print(f"Total Documents: {collection_info['document_count']}")
    print(f"Total Unique Documents: {debug_info['document_count']}")

def main():
    parser = argparse.ArgumentParser(description='ChromaDB Query Tool')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List command
    subparsers.add_parser('list', help='List all documents')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search documents')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('-n', '--limit', type=int, default=3,
                             help='Number of results (default: 3)')
    
    # Stats command
    subparsers.add_parser('stats', help='Show collection statistics')
    
    args = parser.parse_args()
    
    setup_logging()
    
    try:
        if args.command == 'list':
            list_documents()
        elif args.command == 'search':
            search_documents(args.query, args.limit)
        elif args.command == 'stats':
            show_stats()
        else:
            parser.print_help()
    except Exception as e:
        print(f"Error: {str(e)}")
        logging.error("Error executing command", exc_info=True)

if __name__ == "__main__":
    main()

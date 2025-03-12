#!/usr/bin/env python3
import click
import chromadb
import json
from pathlib import Path
import sys

# Use the same ChromaDB directory as the main application
CHROMA_PERSIST_DIR = "chroma_db"

def get_client():
    """Create ChromaDB client with telemetry disabled"""
    return chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=chromadb.Settings(
            anonymized_telemetry=False
        )
    )

@click.group()
def cli():
    """ChromaDB CLI tool for database management"""
    pass

@cli.command()
def list_collections():
    """List all collections in the database"""
    client = get_client()
    collections = client.list_collections()
    
    click.echo("\nChromaDB Collections:")
    click.echo("===================")
    
    if not collections:
        click.echo("No collections found.")
        return
        
    for collection in collections:
        click.echo(f"\nCollection: {collection.name}")
        click.echo(f"Number of documents: {collection.count()}")

@cli.command()
@click.argument('collection_name')
def show_collection(collection_name):
    """Show details of a specific collection"""
    client = get_client()
    try:
        collection = client.get_collection(collection_name)
        results = collection.get()
        
        click.echo(f"\nCollection: {collection_name}")
        click.echo("===================")
        click.echo(f"Total documents: {collection.count()}")
        
        if results["ids"]:
            click.echo("\nDocuments:")
            for i, (doc_id, metadata) in enumerate(zip(results["ids"], results["metadatas"])):
                click.echo(f"\n{i+1}. Document ID: {doc_id}")
                click.echo(f"   Metadata: {json.dumps(metadata, indent=2)}")
    except Exception as e:
        click.echo(f"Error: Collection '{collection_name}' not found or error accessing it.", err=True)
        sys.exit(1)

@cli.command()
@click.argument('collection_name')
@click.argument('document_id')
def delete_document(collection_name, document_id):
    """Delete a specific document from a collection"""
    if not click.confirm(f"Are you sure you want to delete document '{document_id}' from collection '{collection_name}'?"):
        click.echo("Operation cancelled.")
        return
        
    client = get_client()
    try:
        collection = client.get_collection(collection_name)
        collection.delete(ids=[document_id])
        click.echo(f"Successfully deleted document '{document_id}' from collection '{collection_name}'")
    except Exception as e:
        click.echo(f"Error deleting document: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('collection_name')
def delete_collection(collection_name):
    """Delete an entire collection"""
    if not click.confirm(f"WARNING: Are you sure you want to delete the entire collection '{collection_name}'?\nThis action cannot be undone!", abort=True):
        return
        
    client = get_client()
    try:
        client.delete_collection(collection_name)
        click.echo(f"Successfully deleted collection '{collection_name}'")
    except Exception as e:
        click.echo(f"Error deleting collection: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('collection_name')
@click.argument('query')
@click.option('--limit', '-n', default=5, help='Number of results to return')
def search(collection_name, query, limit):
    """Search for documents in a collection"""
    client = get_client()
    try:
        collection = client.get_collection(collection_name)
        results = collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        click.echo(f"\nSearch Results for: '{query}'")
        click.echo("===================")
        
        if not results["ids"][0]:
            click.echo("No results found.")
            return
            
        for i, (doc_id, document, metadata) in enumerate(zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0]
        )):
            click.echo(f"\n{i+1}. Document ID: {doc_id}")
            click.echo(f"   Content: {document[:200]}...")
            click.echo(f"   Metadata: {json.dumps(metadata, indent=2)}")
            
    except Exception as e:
        click.echo(f"Error searching collection: {str(e)}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    cli()

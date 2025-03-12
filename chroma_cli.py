#!/usr/bin/env python3
import click
import chromadb
import json
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

    for coll_name in collections:
        click.echo(f"\nCollection: {coll_name}")
        try:
            collection = client.get_collection(name=coll_name)
            count = collection.count()
            click.echo(f"Number of documents: {count}")
        except Exception as e:
            click.echo("Could not retrieve details for this collection.")

@cli.command()
@click.argument('collection_name')
@click.option('--limit', '-n', default=10, help='Number of documents to show')
def list_documents(collection_name, limit):
    """List documents in a collection"""
    client = get_client()
    try:
        collection = client.get_collection(name=collection_name)
        results = collection.get(limit=limit)

        click.echo(f"\nDocuments in collection '{collection_name}':")
        click.echo("=" * (len(collection_name) + 24))

        if not results['ids']:
            click.echo("No documents found.")
            return

        for i, (doc_id, metadata) in enumerate(zip(results['ids'], results['metadatas'])):
            click.echo(f"\n{i+1}. Document ID: {doc_id}")
            if metadata:
                click.echo(f"   Metadata: {json.dumps(metadata, indent=2)}")

        total_docs = collection.count()
        if total_docs > limit:
            click.echo(f"\nShowing {limit} of {total_docs} documents. Use --limit option to show more.")

    except Exception as e:
        click.echo(f"Error: Collection '{collection_name}' not found or error accessing it: {str(e)}")

@cli.command()
@click.argument('collection_name')
@click.argument('document_id')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation prompt')
def delete_document(collection_name, document_id, force):
    """Delete a specific document from a collection"""
    client = get_client()
    try:
        collection = client.get_collection(name=collection_name)

        # Get document details before deletion
        results = collection.get(ids=[document_id])

        if not results['ids']:
            click.echo(f"Error: Document '{document_id}' not found in collection '{collection_name}'")
            return

        # Display document details
        click.echo("\nDocument to delete:")
        click.echo("==================")
        click.echo(f"ID: {document_id}")
        if results['metadatas'][0]:
            click.echo("Metadata:")
            click.echo(json.dumps(results['metadatas'][0], indent=2))

        # If force flag is set or user confirms, proceed with deletion
        if force or click.confirm("\nAre you sure you want to delete this document?", default=False):
            try:
                collection.delete(ids=[document_id])
                click.echo(f"\nSuccessfully deleted document '{document_id}' from collection '{collection_name}'")
            except Exception as e:
                click.echo(f"\nError deleting document: {str(e)}")
                sys.exit(1)
        else:
            click.echo("\nDeletion cancelled.")

    except Exception as e:
        click.echo(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    cli()
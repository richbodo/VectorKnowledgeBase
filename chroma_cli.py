#!/usr/bin/env python3
import click
import chromadb
import json
import sys
from config import CHROMA_PERSIST_DIR

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
@click.argument('chunk_id')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation prompt')
def delete_chunk(collection_name, chunk_id, force):
    """Delete a specific chunk from a collection"""
    client = get_client()
    try:
        collection = client.get_collection(name=collection_name)

        # Get chunk details before deletion
        results = collection.get(ids=[chunk_id])

        if not results['ids']:
            click.echo(f"Error: Chunk '{chunk_id}' not found in collection '{collection_name}'")
            sys.exit(1)

        # Display chunk details
        click.echo("\nChunk to delete:")
        click.echo("==================")
        click.echo(f"ID: {chunk_id}")
        if results['metadatas'][0]:
            click.echo("Metadata:")
            click.echo(json.dumps(results['metadatas'][0], indent=2))

        # If force flag is set or user confirms, proceed with deletion
        prompt = "\nAre you sure you want to delete this chunk? This action cannot be undone."
        if force or click.confirm(prompt, abort=True):
            try:
                collection.delete(ids=[chunk_id])
                click.echo(f"\nSuccessfully deleted chunk '{chunk_id}' from collection '{collection_name}'")
            except Exception as e:
                click.echo(f"\nError deleting chunk: {str(e)}")
                sys.exit(1)

    except click.Abort:
        click.echo("\nDeletion cancelled.")
        sys.exit(0)
    except Exception as e:
        click.echo(f"Error: {str(e)}")
        sys.exit(1)

@cli.command()
@click.argument('collection_name')
@click.argument('document_id')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation prompt')
def delete_pdf(collection_name, document_id, force):
    """Delete all chunks of a PDF document"""
    client = get_client()
    try:
        collection = client.get_collection(name=collection_name)

        # Get all documents to search for chunks
        all_docs = collection.get()
        chunk_ids = []
        pdf_metadata = None

        # Find all chunks belonging to this PDF
        for chunk_id, metadata in zip(all_docs['ids'], all_docs['metadatas']):
            if metadata.get('document_id') == document_id:
                chunk_ids.append(chunk_id)
                if not pdf_metadata:  # Store metadata from first chunk for display
                    pdf_metadata = metadata

        if not chunk_ids:
            click.echo(f"Error: No chunks found for PDF document '{document_id}'")
            sys.exit(1)

        # Display PDF details
        click.echo("\nPDF document to delete:")
        click.echo("=====================")
        click.echo(f"Document ID: {document_id}")
        click.echo(f"Filename: {pdf_metadata.get('filename', 'Unknown')}")
        click.echo(f"Total chunks: {len(chunk_ids)}")
        if pdf_metadata:
            click.echo("Metadata:")
            click.echo(json.dumps(pdf_metadata, indent=2))

        # If force flag is set or user confirms, proceed with deletion
        prompt = f"\nAre you sure you want to delete all {len(chunk_ids)} chunks of this PDF? This action cannot be undone."
        if force or click.confirm(prompt, abort=True):
            try:
                collection.delete(ids=chunk_ids)
                click.echo(f"\nSuccessfully deleted all chunks of PDF '{document_id}'")
                click.echo(f"Chunks deleted: {len(chunk_ids)}")
            except Exception as e:
                click.echo(f"\nError deleting PDF chunks: {str(e)}")
                sys.exit(1)

    except click.Abort:
        click.echo("\nDeletion cancelled.")
        sys.exit(0)
    except Exception as e:
        click.echo(f"Error: {str(e)}")
        sys.exit(1)

@cli.command()
@click.argument('collection_name')
def nuke_db(collection_name):
    """⚠️ DANGER: Delete ALL documents and chunks from the database."""
    client = get_client()
    try:
        collection = client.get_collection(name=collection_name)

        # Get all documents before deletion
        all_docs = collection.get()
        if not all_docs['ids']:
            click.echo("No documents found in the database.")
            return

        # Count unique PDFs
        pdf_ids = set()
        for metadata in all_docs['metadatas']:
            if metadata and 'document_id' in metadata:
                pdf_ids.add(metadata['document_id'])

        # Display what will be deleted
        click.echo("\n⚠️  WARNING: You are about to delete:")
        click.echo("================================")
        click.echo(f"Total PDFs: {len(pdf_ids)}")
        click.echo(f"Total chunks: {len(all_docs['ids'])}")
        click.echo("\nThis action CANNOT be undone!")

        # First confirmation
        click.echo("\nTo proceed, type 'NUKE' (or anything else to cancel):")
        try:
            confirm1 = input().strip()
            if confirm1 != "NUKE":
                click.echo("Operation cancelled.")
                sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            click.echo("\nOperation cancelled - interactive input required.")
            sys.exit(1)

        # Second confirmation
        click.echo("\nFor final confirmation, type 'DATABASE' (or anything else to cancel):")
        try:
            confirm2 = input().strip()
            if confirm2 != "DATABASE":
                click.echo("Operation cancelled.")
                sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            click.echo("\nOperation cancelled - interactive input required.")
            sys.exit(1)

        # Final deletion
        click.echo("\nProceeding with database deletion...")
        collection.delete(ids=all_docs['ids'])
        click.echo("\n✅ Database successfully nuked!")
        click.echo(f"Deleted {len(pdf_ids)} PDFs ({len(all_docs['ids'])} chunks)")

    except Exception as e:
        click.echo(f"\n❌ Error nuking database: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    cli()
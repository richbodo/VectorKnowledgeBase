#!/usr/bin/env python3
import click
import chromadb
import json
import sys
import os

# Use the same ChromaDB directory as the main application
CHROMA_PERSIST_DIR = "chroma_db"

def get_client():
    """Create ChromaDB client with exact same config as the main app"""
    return chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=chromadb.Settings(
            anonymized_telemetry=False,
            allow_reset=True,
            persist_directory=CHROMA_PERSIST_DIR
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
            
            # Additional diagnostic information
            if count == 0:
                click.echo("No documents found in collection.")
            else:
                # Get all documents to see what's there
                all_results = collection.get()
                if all_results and all_results["ids"]:
                    unique_doc_ids = set()
                    for metadata in all_results["metadatas"]:
                        if metadata and "document_id" in metadata:
                            unique_doc_ids.add(metadata["document_id"])
                    
                    click.echo(f"Number of unique document IDs: {len(unique_doc_ids)}")
                    click.echo(f"Number of chunks: {len(all_results['ids'])}")
                    
                    # Display first few document IDs
                    if unique_doc_ids:
                        click.echo("\nSample document IDs:")
                        for i, doc_id in enumerate(list(unique_doc_ids)[:3]):
                            click.echo(f"  {i+1}. {doc_id}")
        except Exception as e:
            click.echo(f"Could not retrieve details for this collection: {str(e)}")

@cli.command()
def diagnose_db():
    """Run diagnostics on the ChromaDB database"""
    client = get_client()
    
    click.echo("\nChromaDB Diagnostics:")
    click.echo("====================")
    
    try:
        collections = client.list_collections()
        click.echo(f"Found {len(collections)} collections")
        
        if not collections:
            click.echo("No collections found. Database may be empty or corrupted.")
            return
            
        for coll_name in collections:
            click.echo(f"\nExamining collection: {coll_name}")
            try:
                collection = client.get_collection(name=coll_name)
                count = collection.count()
                click.echo(f"Document count: {count}")
                
                if count > 0:
                    # Try to retrieve some data
                    sample = collection.get(limit=1)
                    click.echo("✅ Successfully retrieved sample data")
                    click.echo(f"Sample ID: {sample['ids'][0] if sample['ids'] else 'None'}")
                else:
                    click.echo("⚠️ Collection exists but contains no documents")
                    
                # Test query functionality
                try:
                    query_result = collection.query(query_texts=["test query"], n_results=1)
                    click.echo("✅ Query functionality working")
                except Exception as qe:
                    click.echo(f"❌ Query functionality error: {str(qe)}")
                    
            except Exception as e:
                click.echo(f"❌ Error accessing collection: {str(e)}")
                
        # Check database files
        db_path = CHROMA_PERSIST_DIR
        if os.path.exists(db_path):
            files = os.listdir(db_path)
            click.echo(f"\nDatabase directory contains {len(files)} items")
            sqlite_files = [f for f in files if f.endswith('.sqlite3')]
            if sqlite_files:
                click.echo(f"✅ Found SQLite database files: {', '.join(sqlite_files)}")
            else:
                click.echo("❌ No SQLite database files found")
        else:
            click.echo(f"❌ Database directory not found at {db_path}")
            
    except Exception as e:
        click.echo(f"❌ Diagnostic error: {str(e)}")

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
@click.option('--document-id', '-d', help='Filter chunks by document ID')
@click.option('--limit', '-l', type=int, default=10, help='Maximum number of chunks to show')
@click.option('--show-content/--no-content', default=False, help='Display chunk content')
def list_chunks(collection_name, document_id, limit, show_content):
    """List chunks in a collection with filtering options"""
    client = get_client()
    try:
        collection = client.get_collection(name=collection_name)
        
        # Get all chunks, with optional filtering
        if document_id:
            all_chunks = collection.get(
                where={"document_id": document_id},
                limit=limit
            )
            click.echo(f"\nChunks for document '{document_id}' in collection '{collection_name}':")
        else:
            all_chunks = collection.get(limit=limit)
            click.echo(f"\nListing chunks in collection '{collection_name}' (limit: {limit}):")
        
        # Display chunk information
        click.echo("=================================")
        if not all_chunks['ids']:
            click.echo("No chunks found with the current filters.")
            return
            
        click.echo(f"Found {len(all_chunks['ids'])} chunks")
        
        for i, (chunk_id, metadata, document) in enumerate(zip(
            all_chunks['ids'], 
            all_chunks['metadatas'], 
            all_chunks['documents']
        )):
            click.echo(f"\nChunk #{i+1}: {chunk_id}")
            
            # Display metadata
            if metadata:
                click.echo("Metadata:")
                doc_id = metadata.get('document_id', 'Unknown')
                filename = metadata.get('filename', 'Unknown')
                chunk_index = metadata.get('chunk_index', 'Unknown')
                total_chunks = metadata.get('total_chunks', 'Unknown')
                
                click.echo(f"  Document ID: {doc_id}")
                click.echo(f"  Filename: {filename}")
                click.echo(f"  Chunk: {chunk_index+1}/{total_chunks}" 
                          if isinstance(chunk_index, int) else f"  Chunk index: {chunk_index}")
                
                # Display other metadata
                for key, value in metadata.items():
                    if key not in ['document_id', 'filename', 'chunk_index', 'total_chunks']:
                        click.echo(f"  {key}: {value}")
            
            # Display content if requested
            if show_content and document:
                click.echo("Content Preview:")
                content_preview = document[:200] + "..." if len(document) > 200 else document
                click.echo(f"  {content_preview}")
                
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
        confirm1 = input().strip()
        if confirm1 != "NUKE":
            click.echo("Operation cancelled.")
            return

        # Second confirmation
        click.echo("\nFor final confirmation, type 'DATABASE' (or anything else to cancel):")
        confirm2 = input().strip()
        if confirm2 != "DATABASE":
            click.echo("Operation cancelled.")
            return

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
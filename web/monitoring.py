import logging
import os
import traceback
import sqlite3
import json
import datetime
from flask import Blueprint, jsonify, render_template, request
import openai
from services.embedding_service import EmbeddingService
from services.vector_store import VectorStore
from config import CHROMA_DB_PATH
from utils.object_storage import get_chroma_storage
<<<<<<< HEAD
from web.auth import auth_required, is_authenticated, get_user_info
=======
>>>>>>> 446e53914c5d9f82f391a8f0f259dd39892a7531

logger = logging.getLogger(__name__)

bp = Blueprint('monitoring', __name__, url_prefix='/monitoring')

@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint that tests the OpenAI API connection."""
    try:
        # Check if OpenAI API key is set
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return jsonify({
                "status": "warning",
                "message": "OPENAI_API_KEY environment variable is not set."
            }), 200

        # Test API key validity by accessing a simple endpoint
        client = openai.OpenAI(api_key=api_key)
        models = client.models.list(limit=1)

        # If we get here, the connection is working
        return jsonify({
            "status": "ok",
            "message": "Successfully connected to OpenAI API",
            "models_accessible": True
        }), 200

    except Exception as e:
        logger.error(f"OpenAI API connection test failed: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to connect to OpenAI API: {str(e)}"
        }), 500

@bp.route('/test-openai', methods=['GET'])
<<<<<<< HEAD
@auth_required
def test_openai_connection():
    """Test OpenAI API connection and display diagnostic information"""
    # Get authentication info for the template
    is_auth = is_authenticated()
    user_info = get_user_info() if is_auth else None
=======
def test_openai_connection():
    """Test OpenAI API connection and display diagnostic information"""
>>>>>>> 446e53914c5d9f82f391a8f0f259dd39892a7531
    try:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        key_info = {
            'starts_with': api_key[:4] if api_key else 'None',
            'ends_with': api_key[-4:] if api_key else 'None',
            'length': len(api_key),
            'format_valid': api_key.startswith('sk-') if api_key else False
        }

        test_text = "This is a test of the OpenAI API connection."
        error_details = None
        embedding = None

        try:
            embedding_service = EmbeddingService()
            embedding = embedding_service.generate_embedding(test_text)
        except Exception as e:
            error_details = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'traceback': traceback.format_exc()
            }

        diagnostic_info = {
            'api_key_info': key_info,
            'test_status': 'success' if embedding is not None else 'failed',
            'error_details': error_details,
            'embedding_generated': embedding is not None,
            'embedding_dimension': len(embedding) if embedding else None
        }

<<<<<<< HEAD
        return render_template('monitoring/openai_test.html', 
                          diagnostic_info=diagnostic_info,
                          is_authenticated=is_auth,
                          user_info=user_info)

    except Exception as e:
        logger.error(f"Error in OpenAI test endpoint: {str(e)}", exc_info=True)
        # Still pass auth info even in error cases
        return render_template('error.html', 
                          error="OpenAI test failed", 
                          is_authenticated=is_auth,
                          user_info=user_info), 500

@bp.route('/database-diagnostic', methods=['GET'])
@auth_required
=======
        return render_template('monitoring/openai_test.html', diagnostic_info=diagnostic_info)

    except Exception as e:
        logger.error(f"Error in OpenAI test endpoint: {str(e)}", exc_info=True)
        return render_template('error.html', error="OpenAI test failed"), 500

@bp.route('/database-diagnostic', methods=['GET'])
>>>>>>> 446e53914c5d9f82f391a8f0f259dd39892a7531
def database_diagnostic():
    """Detailed database diagnostic endpoint that analyzes ChromaDB state"""
    try:
        logger.info("Starting detailed database diagnostics")
        result = {
            "timestamp": f"{datetime.datetime.now().isoformat()}",
            "environment": "production" if os.environ.get("REPL_DEPLOYMENT") else "development",
            "db_information": {},
            "collection_information": {},
            "document_information": {},
            "sqlite_analysis": {},
            "object_storage_info": {},
            "backup_status": {},
            "errors": []
        }
        
        # Get VectorStore instance debug info
        try:
            vector_store = VectorStore.get_instance()
            debug_info = vector_store.get_debug_info()
            result["vector_store_info"] = debug_info
            
            # Copy backup status to the root level for compatibility with template
            if "backup_status" in debug_info:
                result["backup_status"] = debug_info["backup_status"]
            
            # Copy storage info to the root level for compatibility with template
            if "storage_info" in debug_info:
                result["object_storage_info"] = debug_info["storage_info"]
        except Exception as e:
            error_msg = f"Error getting VectorStore debug info: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result["errors"].append(error_msg)
        
        # Check database directory
        try:
            result["db_information"]["db_path"] = CHROMA_DB_PATH
            result["db_information"]["exists"] = os.path.exists(CHROMA_DB_PATH)
            result["db_information"]["is_dir"] = os.path.isdir(CHROMA_DB_PATH) if result["db_information"]["exists"] else False
            
            if result["db_information"]["is_dir"]:
                result["db_information"]["contents"] = os.listdir(CHROMA_DB_PATH)
            else:
                result["db_information"]["contents"] = []
                
            # Check SQLite file
            sqlite_path = os.path.join(CHROMA_DB_PATH, "chroma.sqlite3")
            result["db_information"]["sqlite_exists"] = os.path.exists(sqlite_path)
            
            if result["db_information"]["sqlite_exists"]:
                result["db_information"]["sqlite_size_mb"] = round(os.path.getsize(sqlite_path) / (1024 * 1024), 2)
                
            # Check Replit Object Storage integration
            try:
                result["object_storage_info"]["available"] = True
                storage = get_chroma_storage()
                
                # Check if client is available
                result["object_storage_info"]["client_initialized"] = storage.client is not None
                
                # List files in object storage
                if storage.client is not None:
                    try:
                        files = storage.list_files()
                        result["object_storage_info"]["files_found"] = len(files)
                        result["object_storage_info"]["file_list"] = files[:20] if len(files) <= 20 else files[:20] + ["... and more"]
                        
                        # Check for manifest
                        manifest_key = f"{storage.storage_prefix}manifest.json"
                        manifest_exists = storage.client.exists(manifest_key) if storage.client else False
                        result["object_storage_info"]["manifest_exists"] = manifest_exists
                        
                        if manifest_exists:
                            try:
                                manifest_content = storage.client.download_as_bytes(manifest_key)
                                import json
                                manifest = json.loads(manifest_content.decode('utf-8'))
                                result["object_storage_info"]["manifest"] = manifest
                            except Exception as e:
                                result["object_storage_info"]["manifest_error"] = str(e)
                        
                    except Exception as e:
                        result["object_storage_info"]["list_error"] = str(e)
                
            except Exception as oe:
                result["object_storage_info"]["available"] = False
                result["object_storage_info"]["error"] = str(oe)
                
                # Analyze SQLite database
                conn = sqlite3.connect(sqlite_path)
                cursor = conn.cursor()
                
                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                result["sqlite_analysis"]["tables"] = [t[0] for t in tables]
                
                # Check collections
                cursor.execute("SELECT id, name, dimension, tenant_id, metadata FROM collections")
                collections = cursor.fetchall()
                result["sqlite_analysis"]["collections"] = []
                
                for collection in collections:
                    coll_id, name, dimension, tenant_id, metadata = collection
                    collection_info = {
                        "id": coll_id,
                        "name": name,
                        "dimension": dimension,
                        "tenant_id": tenant_id,
                        "metadata": metadata
                    }
                    result["sqlite_analysis"]["collections"].append(collection_info)
                
                # Count embeddings
                cursor.execute("SELECT COUNT(*) FROM embeddings")
                embedding_count = cursor.fetchone()[0]
                result["sqlite_analysis"]["embedding_count"] = embedding_count
                
                # Count document IDs
                cursor.execute("SELECT COUNT(DISTINCT id) FROM embedding_metadata WHERE key='document_id' OR key='test_id'")
                doc_id_count = cursor.fetchone()[0]
                result["sqlite_analysis"]["doc_id_count"] = doc_id_count
                
                # Sample document IDs
                cursor.execute("SELECT id, key, string_value FROM embedding_metadata WHERE key='document_id' OR key='test_id' LIMIT 10")
                doc_ids = cursor.fetchall()
                result["sqlite_analysis"]["doc_id_samples"] = [
                    {"embedding_id": d[0], "key_type": d[1], "value": d[2]} for d in doc_ids
                ]
                
                # Get example metadata for a document
                if doc_ids:
                    first_doc = doc_ids[0]
                    cursor.execute("SELECT id, key, string_value FROM embedding_metadata WHERE id=?", (first_doc[0],))
                    metadata_rows = cursor.fetchall()
                    result["sqlite_analysis"]["example_metadata"] = [
                        {"id": row[0], "key": row[1], "value": row[2]} for row in metadata_rows
                    ]
                
                conn.close()
                
        except Exception as e:
            error_msg = f"Error analyzing database: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result["errors"].append(error_msg)
        
        # Option to output raw or formatted
        output_format = request.args.get('format', 'html')
        if output_format == 'json':
            return jsonify(result)
        else:
            # Format the JSON for readability in HTML
            formatted_json = json.dumps(result, indent=2)
<<<<<<< HEAD
            
            # Get authentication info for the template
            is_auth = is_authenticated()
            user_info = get_user_info() if is_auth else None
            
            return render_template('monitoring/database_diagnostic.html', 
                                  diagnostic_data=result,
                                  formatted_json=formatted_json,
                                  is_authenticated=is_auth,
                                  user_info=user_info)
    
    except Exception as e:
        logger.error(f"Error in database diagnostic endpoint: {str(e)}", exc_info=True)
        # Get authentication info for error template
        is_auth = is_authenticated()
        user_info = get_user_info() if is_auth else None
        
        # Check if we need to return JSON or HTML
        if request.args.get('format', 'html') == 'json':
            return jsonify({
                "status": "error",
                "message": f"Database diagnostic failed: {str(e)}",
                "traceback": traceback.format_exc()
            }), 500
        else:
            # Return HTML error with authentication info
            return render_template('error.html', 
                             error=f"Database diagnostic failed: {str(e)}", 
                             is_authenticated=is_auth,
                             user_info=user_info), 500
=======
            return render_template('monitoring/database_diagnostic.html', 
                                  diagnostic_data=result,
                                  formatted_json=formatted_json)
    
    except Exception as e:
        logger.error(f"Error in database diagnostic endpoint: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Database diagnostic failed: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500
>>>>>>> 446e53914c5d9f82f391a8f0f259dd39892a7531

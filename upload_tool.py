import os
import sys
import http.server
import socketserver
import cgi
import urllib.parse

# Create directory for uploads if it doesn't exist
os.makedirs("test_files", exist_ok=True)

class FileUploadHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            # Get API key from environment
            api_key = os.environ.get('API_KEY', '')
            api_key_status = "✓ API key is set" if api_key else "⚠ API key is not set"

            # Simple HTML form for file upload
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Upload PDF for Testing</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    h1 {{ color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; }}
                    .upload-form {{ border: 1px solid #ddd; padding: 20px; border-radius: 5px; }}
                    .file-input {{ margin: 10px 0; }}
                    .submit-btn {{ 
                        background-color: #4CAF50; color: white; 
                        padding: 10px 15px; border: none; 
                        border-radius: 4px; cursor: pointer; 
                    }}
                    .api-key-status {{
                        padding: 10px;
                        margin-bottom: 15px;
                        border-radius: 4px;
                        background-color: {('#e8f5e9' if api_key else '#ffebee')};
                        color: {('#2e7d32' if api_key else '#c62828')};
                    }}
                    .files {{ margin-top: 30px; }}
                    .file-item {{ 
                        padding: 8px; margin-bottom: 5px; 
                        background-color: #f9f9f9; border-radius: 3px; 
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Upload PDF File</h1>
                    <div class="api-key-status">
                        {api_key_status}
                    </div>
                    <div class="upload-form">
                        <form enctype="multipart/form-data" method="post">
                            <div class="file-input">
                                <label for="file">Select a PDF file:</label><br>
                                <input type="file" name="file" id="file" accept="application/pdf">
                            </div>
                            <input class="submit-btn" type="submit" value="Upload">
                        </form>
                    </div>

                    <div class="files">
                        <h2>Available Test Files:</h2>
                        {self._list_files()}
                    </div>

                    <div class="usage">
                        <h2>How to use:</h2>
                        <p>After uploading, use the test script with one of the files:</p>
                        <code>API_KEY=your_api_key ./test_api.sh test_files/your_file.pdf</code>
                    </div>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            return super().do_GET()

    def do_POST(self):
        if self.path == '/':
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST',
                       'CONTENT_TYPE': self.headers['Content-Type'],
                       })

            if 'file' in form:
                file_item = form['file']
                if file_item.filename:
                    # Remove unsafe characters from filename
                    safe_filename = os.path.basename(file_item.filename)
                    filepath = os.path.join('test_files', safe_filename)

                    # Save the file
                    with open(filepath, 'wb') as f:
                        f.write(file_item.file.read())

                    # Redirect back to the form
                    self.send_response(303)
                    self.send_header('Location', '/')
                    self.end_headers()
                    return

            # If we get here, something went wrong
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Error uploading file. Please try again.')

    def _list_files(self):
        try:
            files = os.listdir('test_files')
            if not files:
                return "<p>No files uploaded yet.</p>"

            html = "<ul>"
            for filename in files:
                if filename.endswith('.pdf'):
                    file_path = os.path.join('test_files', filename)
                    size = os.path.getsize(file_path)
                    size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f} MB"
                    html += f"<li class='file-item'>{filename} ({size_str})</li>"
            html += "</ul>"
            return html
        except Exception as e:
            return f"<p>Error listing files: {str(e)}</p>"

if __name__ == "__main__":
    PORT = 8090

    try:
        with socketserver.TCPServer(("0.0.0.0", PORT), FileUploadHandler) as httpd:
            print(f"File upload server running at http://0.0.0.0:{PORT}")
            print(f"Use this link in your Replit webview: https://{{REPL_SLUG}}.{{USERNAME}}.repl.co:8090")
            print("Upload PDFs and then test them with: API_KEY=your_api_key ./test_api.sh test_files/your_file.pdf")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error: {e}")
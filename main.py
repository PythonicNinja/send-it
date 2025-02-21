#!/usr/bin/env python3

import argparse
import os
import signal
import sys
import tempfile
import time
import shutil
import subprocess
import json
import http.server
import socketserver
import threading
from urllib import request
from pathlib import Path

def parse_arguments():
    parser = argparse.ArgumentParser(description="Serve content through ngrok")
    parser.add_argument("-p", "--port", type=int, default=8080, help="Port to use (default: 8080)")
    parser.add_argument("--basic-auth", type=str, help="Basic auth in format 'admin:password'")
    parser.add_argument("content", nargs='*', help="Folder path or text content to serve (optional)")
    return parser.parse_args()

def setup_content(args):
    """Prepare the content to be served"""
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    print(f"Created temporary directory: {temp_dir}")
    
    # Join all content arguments in case it's text with spaces
    content = " ".join(args.content)

    # no content, open default editor
    if not content:
        tmp_file = Path(temp_dir) / "share.txt"
        # no content, open default editor and use file on save
        editor = os.environ.get("EDITOR", "vi")
        subprocess.run([editor, tmp_file.as_posix()])
        with open(tmp_file) as shared_file:
            content = shared_file.read()
    
    # Check if it's a folder
    if os.path.isdir(content):
        print(f"Detected folder input: {content}")
        # Copy all files from source directory to temporary directory
        for item in os.listdir(content):
            src_path = os.path.join(content, item)
            dst_path = os.path.join(temp_dir, item)
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
    #  check if it's file
    elif os.path.isfile(content):
        print(f"Detected file input: {content}")
        # Copy the file to the temporary directory
        shutil.copy2(content, temp_dir)
    else:
        # It's text content
        print("Detected text input, creating index.html")
        with (Path(__file__).parent / "index.html").open("r") as src_file:
            sample_content = src_file.read()
            with open(os.path.join(temp_dir, "index.html"), "w") as f:
                shared_content = sample_content.replace("<% message %>", content)
                f.write(shared_content)
    
    return temp_dir

class HttpServer:
    def __init__(self, directory, port):
        self.directory = directory
        self.port = port
        self.httpd = None
        self.thread = None
    
    def start(self):
        """Start the HTTP server in a separate thread"""
        handler = http.server.SimpleHTTPRequestHandler
        os.chdir(self.directory)
        
        class CustomTCPServer(socketserver.TCPServer):
            allow_reuse_address = True
        
        self.httpd = CustomTCPServer(("", self.port), handler)
        
        print(f"Starting HTTP server on port {self.port}...")
        self.thread = threading.Thread(target=self.httpd.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        time.sleep(1)  # Give the server a moment to start
        return True
    
    def stop(self):
        """Stop the HTTP server"""
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            print("HTTP server stopped")

class NgrokTunnel:
    def __init__(self, port, basic_auth=None):
        self.port = port
        self.process = None
        self.basic_auth = basic_auth
    
    def start(self):
        """Start ngrok tunnel"""
        try:
            command = ["ngrok", "http", str(self.port)] 
            if self.basic_auth:
                command += ["--basic-auth", self.basic_auth]
            # Start ngrok as a subprocess
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(2)  # Wait for ngrok to initialize
            
            # Get the public URL
            try:
                with request.urlopen("http://localhost:4040/api/tunnels") as response:
                    data = response.read().decode('utf-8')
                    tunnels = json.loads(data)["tunnels"]
                    if tunnels:
                        print("\nSend this url to access message:")
                        for tunnel in tunnels:
                            print(f"  {tunnel['public_url']}")
                        return True
                    else:
                        return False
            except Exception as e:
                print(f"[error] Failed to get ngrok tunnel info exception: '{e}'")
                for message in self.process.communicate():
                    print(f"[error] {message}")
                return False
                
        except FileNotFoundError:
            print("Error: ngrok not found. Please install ngrok first.")
            return False
    
    def stop(self):
        """Stop the ngrok tunnel"""
        if self.process:
            self.process.terminate()
            print("Ngrok tunnel closed")

def main():
    args = parse_arguments()
    temp_dir = setup_content(args)
    
    # Set up cleanup handler
    def cleanup_handler(signum, frame):
        print("\nCleaning up...")
        http_server.stop()
        ngrok_tunnel.stop()
        shutil.rmtree(temp_dir)
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)
    
    # Start HTTP server
    http_server = HttpServer(temp_dir, args.port)
    if not http_server.start():
        print("Failed to start HTTP server")
        shutil.rmtree(temp_dir)
        return
    
    # Start ngrok
    ngrok_tunnel = NgrokTunnel(
        port=args.port,
        basic_auth=args.basic_auth,
    )
    if not ngrok_tunnel.start():
        print("Failed to start ngrok tunnel")
        http_server.stop()
        shutil.rmtree(temp_dir)
        return
    
    print("\nPress Ctrl+C to stop the server and exit")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup_handler(None, None)

if __name__ == "__main__":
    main()
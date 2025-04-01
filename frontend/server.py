from http.server import SimpleHTTPRequestHandler, HTTPServer
import os

PORT = 8000

class FrontendServer(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__))
    print(f"Serving Oracle JET GUI at http://localhost:{PORT}")
    with HTTPServer(('localhost', PORT), FrontendServer) as httpd:
        httpd.serve_forever()

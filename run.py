#!/usr/bin/env python3
"""
Main entry point for the Flask application.
Run this file to start the development server.
"""

import os
from app import create_app

# Create app instance
app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Get configuration from environment
    debug = os.environ.get('FLASK_ENV') == 'development'
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))

    print(f"""
╔═══════════════════════════════════════════════════════════╗
║          Secure Flask API                                 ║
║                                                           ║
║  Server running at: http://{host}:{port}           ║
║  Environment: {os.environ.get('FLASK_ENV', 'development').ljust(44)}║
║                                                           ║
║  Press CTRL+C to quit                                     ║
╚═══════════════════════════════════════════════════════════╝
    """)

    app.run(
        host=host,
        port=port,
        debug=debug
    )

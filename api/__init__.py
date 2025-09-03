"""
API Package
RESTful API endpoints and WebSocket handlers
"""

from .routes import setup_routes, setup_websocket_events

__all__ = ['setup_routes', 'setup_websocket_events']

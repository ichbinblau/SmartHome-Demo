# -*- coding: utf-8 -*-
"""
app view
"""
import os
import logging
from views import create_app, socketio

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info('init SMART HOME project ...')
    app = create_app()
    port = os.getenv('PORT', '3000')
    socketio.run(app, debug=True, port=int(port), host="0.0.0.0")



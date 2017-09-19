# -*- coding: utf-8 -*-
"""
app entry
"""
import os
from admin import create_app

try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

if __name__ == "__main__":
    PORT = os.getenv('PORT', '4000')
    app = create_app(debug=False)
    app.run(port=int(PORT), host='0.0.0.0')

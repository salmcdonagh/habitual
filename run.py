from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    # For local development
    app.run(debug=True, host='localhost', port=5001)
else:
    # For production (Cloud Run will call this directly via gunicorn)
    pass
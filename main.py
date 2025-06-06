import sys
import os

# Add the api-gateway directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'api-gateway'))

# Import the app from main_minimal
from main_minimal import app

# This allows Railway to find the app
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 
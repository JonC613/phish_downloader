"""
Launcher script for Streamlit app to avoid threading issues.
"""
import sys
import os
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('streamlit_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        logger.info("Starting Streamlit launcher...")
        
        # Set environment variables before importing anything
        os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
        os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
        
        logger.info("Environment variables set")
        
        # Import streamlit after environment is set
        logger.info("Importing streamlit...")
        from streamlit.web import cli as stcli
        
        logger.info("Streamlit imported successfully")
        
        # Run the app
        sys.argv = ["streamlit", "run", "streamlit_app.py", "--server.port=8502", "--logger.level=debug"]
        logger.info(f"Running with args: {sys.argv}")
        
        sys.exit(stcli.main())
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())
        input("Press Enter to exit...")
        sys.exit(1)

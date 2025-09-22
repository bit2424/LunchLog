"""
Restaurant services package.
"""

# Import the GooglePlacesService from the main services module
import importlib.util
import os

# Get the path to the parent services.py file
services_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "services.py")

# Load the services module
spec = importlib.util.spec_from_file_location("main_services", services_path)
main_services = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_services)

# Import GooglePlacesService
GooglePlacesService = main_services.GooglePlacesService

__all__ = ["GooglePlacesService"]

"""
Calculator Package
A simple Python calculator application with modular design.

This package contains:
- operations: Calculator class with mathematical operations
- utils: Utility functions for input validation and user interaction
- main: Main application entry point
"""

__version__ = "1.0.0"
__author__ = "Calculator App"
__description__ = "A simple command-line calculator application"

from .operations import Calculator
from .utils import (
    display_menu,
    get_user_input,
    validate_number,
    format_result,
    is_integer,
    safe_divide,
    clear_screen,
    confirm_action
)

__all__ = [
    "Calculator",
    "display_menu",
    "get_user_input",
    "validate_number",
    "format_result",
    "is_integer",
    "safe_divide",
    "clear_screen",
    "confirm_action"
]
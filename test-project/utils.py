"""
Utility Functions Module
Contains helper functions for input validation, menu display, and user interaction.
"""

import re
from typing import Union


def display_menu() -> None:
    """Display the calculator menu options."""
    print("\nCalculator Menu:")
    print("1. Addition (+)")
    print("2. Subtraction (-)")
    print("3. Multiplication (*)")
    print("4. Division (/)")
    print("5. Show History")
    print("6. Exit")


def get_user_input(prompt: str) -> float:
    """
    Get numeric input from user with validation.
    
    Args:
        prompt (str): The prompt message to display
        
    Returns:
        float: Valid numeric input from user
        
    Raises:
        ValueError: If input cannot be converted to a number
    """
    while True:
        user_input = input(prompt).strip()
        
        if validate_number(user_input):
            return float(user_input)
        else:
            print("Invalid input! Please enter a valid number.")


def validate_number(value: str) -> bool:
    """
    Validate if a string represents a valid number.
    
    Args:
        value (str): String to validate
        
    Returns:
        bool: True if valid number, False otherwise
    """
    if not value:
        return False
    
    # Pattern for valid numbers (including decimals, negative numbers, scientific notation)
    pattern = r'^[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?$'
    return bool(re.match(pattern, value))


def format_result(result: float, precision: int = 2) -> str:
    """
    Format a numeric result for display.
    
    Args:
        result (float): The number to format
        precision (int): Number of decimal places (default: 2)
        
    Returns:
        str: Formatted number string
    """
    if result == int(result):
        return str(int(result))
    else:
        return f"{result:.{precision}f}"


def is_integer(value: float) -> bool:
    """
    Check if a float value is actually an integer.
    
    Args:
        value (float): Value to check
        
    Returns:
        bool: True if value is an integer, False otherwise
    """
    return value == int(value)


def safe_divide(a: float, b: float) -> Union[float, str]:
    """
    Safely perform division with error handling.
    
    Args:
        a (float): Dividend
        b (float): Divisor
        
    Returns:
        Union[float, str]: Result of division or error message
    """
    if b == 0:
        return "Error: Division by zero"
    return a / b


def clear_screen() -> None:
    """Clear the console screen (cross-platform)."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def confirm_action(message: str) -> bool:
    """
    Get yes/no confirmation from user.
    
    Args:
        message (str): Confirmation message to display
        
    Returns:
        bool: True if user confirms, False otherwise
    """
    while True:
        response = input(f"{message} (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no.")
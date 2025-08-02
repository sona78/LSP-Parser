#!/usr/bin/env python3
"""
Calculator Application
A simple command-line calculator with multiple operation support.
"""

from operations import Calculator
from utils import display_menu, get_user_input, validate_number


def main():
    """Main application entry point."""
    calc = Calculator()
    
    print("Welcome to the Python Calculator!")
    print("=" * 40)
    
    while True:
        display_menu()
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '6':
            print("Thank you for using the calculator. Goodbye!")
            break
        
        if choice not in ['1', '2', '3', '4', '5']:
            print("Invalid choice! Please select 1-6.")
            continue
        
        try:
            if choice == '5':
                # History doesn't need operands
                calc.show_history()
                continue
                
            # Get numbers for operations
            num1 = get_user_input("Enter first number: ")
            num2 = get_user_input("Enter second number: ")
            
            # Perform calculation
            if choice == '1':
                result = calc.add(num1, num2)
                operation = "Addition"
            elif choice == '2':
                result = calc.subtract(num1, num2)
                operation = "Subtraction"
            elif choice == '3':
                result = calc.multiply(num1, num2)
                operation = "Multiplication"
            elif choice == '4':
                result = calc.divide(num1, num2)
                operation = "Division"
            
            print(f"\n{operation} Result: {result}")
            
        except ValueError as e:
            print(f"Error: {e}")
        except ZeroDivisionError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
        
        print("-" * 40)


if __name__ == "__main__":
    main()
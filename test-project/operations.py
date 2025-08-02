"""
Calculator Operations Module
Contains the Calculator class with basic mathematical operations.
"""

from datetime import datetime
from typing import List, Tuple


class Calculator:
    """A calculator class that performs basic mathematical operations and maintains history."""
    
    def __init__(self):
        """Initialize the calculator with an empty history."""
        self.history: List[Tuple[str, float, float, float, str]] = []
    
    def add(self, a: float, b: float) -> float:
        """
        Add two numbers.
        
        Args:
            a (float): First number
            b (float): Second number
            
        Returns:
            float: Sum of a and b
        """
        result = a + b
        self._add_to_history("Addition", a, b, result)
        return result
    
    def subtract(self, a: float, b: float) -> float:
        """
        Subtract second number from first number.
        
        Args:
            a (float): First number
            b (float): Second number
            
        Returns:
            float: Difference of a and b
        """
        result = a - b
        self._add_to_history("Subtraction", a, b, result)
        return result
    
    def multiply(self, a: float, b: float) -> float:
        """
        Multiply two numbers.
        
        Args:
            a (float): First number
            b (float): Second number
            
        Returns:
            float: Product of a and b
        """
        result = a * b
        self._add_to_history("Multiplication", a, b, result)
        return result
    
    def divide(self, a: float, b: float) -> float:
        """
        Divide first number by second number.
        
        Args:
            a (float): First number (dividend)
            b (float): Second number (divisor)
            
        Returns:
            float: Quotient of a and b
            
        Raises:
            ZeroDivisionError: If b is zero
        """
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero!")
        
        result = a / b
        self._add_to_history("Division", a, b, result)
        return result
    
    def power(self, base: float, exponent: float) -> float:
        """
        Raise base to the power of exponent.
        
        Args:
            base (float): Base number
            exponent (float): Exponent
            
        Returns:
            float: base raised to the power of exponent
        """
        result = base ** exponent
        self._add_to_history("Power", base, exponent, result)
        return result
    
    def _add_to_history(self, operation: str, a: float, b: float, result: float) -> None:
        """
        Add an operation to the calculation history.
        
        Args:
            operation (str): Name of the operation
            a (float): First operand
            b (float): Second operand
            result (float): Result of the operation
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.history.append((operation, a, b, result, timestamp))
    
    def show_history(self) -> None:
        """Display the calculation history."""
        if not self.history:
            print("No calculations performed yet.")
            return
        
        print("\nCalculation History:")
        print("=" * 60)
        print(f"{'Operation':<12} {'Operand 1':<10} {'Operand 2':<10} {'Result':<12} {'Time':<19}")
        print("-" * 60)
        
        for operation, a, b, result, timestamp in self.history[-10:]:  # Show last 10
            print(f"{operation:<12} {a:<10.2f} {b:<10.2f} {result:<12.2f} {timestamp}")
    
    def clear_history(self) -> None:
        """Clear the calculation history."""
        self.history.clear()
        print("History cleared.")
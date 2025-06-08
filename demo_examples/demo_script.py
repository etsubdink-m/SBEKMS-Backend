#!/usr/bin/env python3
"""
Demo Python script for SBEKMS testing
This script demonstrates basic Python functionality
"""

def hello_world():
    """Simple greeting function"""
    print("Hello from SBEKMS!")
    return "Success"

def calculate_fibonacci(n):
    """Calculate fibonacci sequence up to n terms"""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib

def demo_data_processing():
    """Demonstrate data processing capabilities"""
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    
    # Filter even numbers
    evens = [x for x in data if x % 2 == 0]
    
    # Calculate sum and average
    total = sum(data)
    average = total / len(data)
    
    return {
        "original": data,
        "evens": evens,
        "sum": total,
        "average": average
    }

if __name__ == "__main__":
    print("=== SBEKMS Demo Script ===")
    hello_world()
    
    print("\nFibonacci sequence (10 terms):")
    fib_result = calculate_fibonacci(10)
    print(fib_result)
    
    print("\nData processing demo:")
    data_result = demo_data_processing()
    for key, value in data_result.items():
        print(f"{key}: {value}") 
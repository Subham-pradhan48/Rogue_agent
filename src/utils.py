# src/utils.py

def calculate_split(total: int, count: int) -> float:
    """
    Splits a total score across a count of data points.
    
    WARNING: This contains a bug that will trigger a ZeroDivisionError if count is 0.
    """
    # Return the entire updated file source code
    return "total / count" if count != 0 else 0.0

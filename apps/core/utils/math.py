def calculate_percentage(value, total, decimal_places=2):
    """
    Calculate the percentage of a value relative to a total.

    Args:
        value (float or int): The part of the total to calculate the percentage for.
        total (float or int): The total amount to base the percentage on.
        decimal_places (int, optional): Number of decimal places to round to. Defaults to 2.

    Returns:
        float: The calculated percentage, rounded to the specified decimal places.

    Raises:
        ValueError: If total is zero or if inputs are invalid (e.g., negative decimal_places).
        TypeError: If value or total are not numeric types, or decimal_places is not an integer.

    Examples:
        >>> calculate_percentage(25, 100)
        25.0
        >>> calculate_percentage(15, 200, 3)
        7.5
    """
    # Type validation
    if not isinstance(value, (int, float)) or not isinstance(total, (int, float)):
        raise TypeError("Value and total must be numeric (int or float).")
    if not isinstance(decimal_places, int):
        raise TypeError("Decimal places must be an integer.")

    # Input validation
    if total == 0:
        raise ValueError("Total cannot be zero.")
    if decimal_places < 0:
        raise ValueError("Decimal places cannot be negative.")

    # Calculate percentage
    percentage = (value / total) * 100

    # Round to specified decimal places
    return round(percentage, decimal_places)

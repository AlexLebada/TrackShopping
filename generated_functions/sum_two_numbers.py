from langchain_core.tools import tool


def sum_two_numbers(a: float, b: float) -> float:
    """
    Sums two numbers.
    
    Args:
        a (float): The first number.
        b (float): The second number.

    Returns:
        float: The sum of the two numbers.
    """
    return a + b


if __name__ == "__main__":
    print(sum_two_numbers(2,5))

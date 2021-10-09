import mpmath as mp


def verify_result(first_value, second_value, result):
    right_side = second_value
    left_side = (first_value * result[0] + result[1])
    right_side = right_side * (first_value * result[2] + result[3])
    if mp.almosteq(right_side, left_side):
        return True

    return None

def check_int_null_vector(first_value, second_value):
    """
    first_value: the first value
    second_value: the second value

    This function checks if there is a mobious transformation that connects the 2 values:
    Denote the math const as M and the CF value as cf then the result we seek is
        (a*M + b) / (c*M + d) = cf
    where a,b,c,d are result[0], result[1], result[2], result[3] respectively
    """
    result = mp.pslq([first_value, 1, -second_value*first_value, -second_value])

    # Verify the result
    if verify_result(first_value, second_value, result):
        return result

    return None

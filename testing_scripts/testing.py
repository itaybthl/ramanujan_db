from decimal import Decimal, getcontext
getcontext().prec = 2000
import math

def calculate_depth(coeff_list, n):
    return sum([coeff*n**(len(coeff_list)-1-idx) for idx, coeff in enumerate(coeff_list)])

def calculate_cf(num, denom, depth):
    val = 0
    for i in range(depth, 0, -1):
        num_val = calculate_depth(num, i)
        denom_val = calculate_depth(denom, i)
        try:
            val = Decimal(num_val) / Decimal((denom_val + val))
        except ZeroDivisionError:
            print(num)
            print(denom)
            print(i)
            print(num_val)
            print(denom_val)
            print(val)
            return 0
    return val + calculate_depth(denom, 0)

def calculate_mat(num, denom, depth):
    A_1 = 1
    B_1 = 0
    A_2 = calculate_depth(denom, 0)
    B_2 = 1

    for i in range(depth-1):
        a = calculate_depth(num, i+1)
        b = calculate_depth(denom, i+1)
        
        A_3 = b*A_2 + a*A_1
        B_3 = b*B_2 + a*B_1
        
        A_1 = A_2
        B_1 = B_2
        A_2 = A_3
        B_2 = B_3

    return Decimal(A_3) / B_3

def calculate_mat2(num, denom, depth):
    a_0 = 1
    b_0 = 0
    a_1 = calculate_depth(denom, 0)
    b_1 = 1

    for i in range(depth-1):
        a = calculate_depth(num, i+1)
        b = calculate_depth(denom, i+1)
        
        p = b*a_1 + a*a_0
        q = b*b_1 + a*b_0
       
        gcd = math.gcd(a, b)

        print(p / gcd)
        print(q / gcd)
        p = p // gcd
        q = q // gcd

        a_0 = a_1
        b_0 = b_1
        a_1 = p
        b_1 = q

    return Decimal(p)/q


def test(num, denom, depth):
    print(calculate_mat2(num, denom, depth))
    print(calculate_mat(num, denom, depth))

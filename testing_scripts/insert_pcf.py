
from pcf.insert_pcf_into_db import add_multiple_pcfs, get_actual_pcfs_from_db
from pcf.PCF import PCF

def test_add_pcf():
    print("")
    pcfs_coeffs =[
        [[1, 1], [-27, -12, -1]],
        [[4, 10, 30, 35, 45, 17], [-1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]],
        [[2, 7, 35, 70, 53, 13], [-1, -2, -1, 0, 0, 0, 0, 0, 0, 0, 0]],
        [[2, 3, 53, 26], [-1, 0, 0, 0, 0, 0, 0]],
        [[2, 3, 53, 26],[-1, 0, 0, 0, 0, 0, 0]],
        [[2, 9, 29, 43, 30, 8], [-1, -4, -3, 0, 0, 0, 0, 0, 0, 0, 0]],
        [[2, 9, 13, 10, 5, 1], [-1, -4, -3, 0, 0, 0, 0, 0, 0, 0, 0]],
        [[2, 7, 11, 10, 5, 1], [-1, -2, -1, 0, 0, 0, 0, 0, 0, 0, 0]]
    ]

    pcfs = [PCF(result[0], result[1]) for result in pcfs_coeffs]
    success, failure = add_multiple_pcfs(pcfs)
    print("Added:")
    print("\n".join([str(s) for s in success]))
    print("Already exist:")
    print("\n".join([str(f) for f in failure["Already exist"]]))
    print("No FR:")
    print("\n".join([str(f) for f in failure["No FR"]]))
    print("END")

def test_get_pcf_from_db():
    pcfs = get_actual_pcfs_from_db()
    for pcf in pcfs:
        print(pcf)

import numpy as np
import math

import sympy
from sympy import *
from sympy import Poly

n = sympy.Symbol("n")


class PCF:

    def __init__(self, an_coefficients, bn_coefficients, value=None, c_top=None, c_bot=None, precision=0):
        """
        an_coefficients, bn_coefficients: lists of integers from the largest power to the smallest power.
        """
        # Important, if we assign [] in the def row, it will use the same array for every object.
        if c_bot is None:
            c_bot = []
        if c_top is None:
            c_top = []
        self.an = Poly(an_coefficients, n)
        self.bn = Poly(bn_coefficients, n)
        self.value = value
        self.c_top = c_top
        self.c_bot = c_bot
        self.precision = precision

    def moving_canonical_form(self):
        # Should always be real roots. (If we find out this isn't the case then we need to modify this)
        bn_roots = self.bn.all_roots()

        # In case bn is a constant (has no roots) we still want an to have the canonical roots
        # => (the smallest root to be in (-1,0] )
        if 0 == len(bn_roots):
            an_real_roots = self.an.real_roots()
            an_rational_roots = self.an.ground_roots()

            # If some of the roots are irrational, it makes the coefficients look ugly, so I decided not to move them.
            # an_rational_roots is a dict {root:power_of_root} while an_real_roots is a list of all of the roots,
            # including multiple repeats.
            if 0 == len(an_real_roots) or len(an_real_roots) != sum(an_rational_roots.values()):
                return self.an, self.bn

            an_real_roots.sort()
            largest_root = an_real_roots[-1]

        else:
            bn_roots.sort()
            largest_root = bn_roots[-1]
        # We want the largest root to be in (-1,0].
        bn_poly_new = self.bn.compose(Poly(n + largest_root))
        an_poly_new = self.an.compose(Poly(n + largest_root))
        return bn_poly_new, an_poly_new


    def inflating_canonical_form(self):
        top = self.bn
        bot = self.an * self.an.compose(Poly(n-1))
        gcd = sympy.gcd(top, bot)
        top_reduced, bot_reduced = cancel(top/gcd), cancel(bot/gcd)
        return Poly(top_reduced, n), Poly(bot_reduced, n)


    def get_cannonical_form(self):
        top, bot = self.inflating_canonical_form()
        inflated_pcf = PCF(bot.all_coeffs(), top.all_coeffs())
        return inflated_pcf.moving_canonical_form()

    def get_cannonical_form_string(self):
        an, bn = self.get_cannonical_form()
        return str(bn / an)

    def __str__(self):
        return "an: " + str(self.an.all_coeffs()) + "\t|\tbn: " + str(self.bn.all_coeffs())

    def is_inflation(self):
        top = self.bn
        bot = self.an * self.an.compose(Poly(n - 1))
        gcd = sympy.gcd(top, bot)
        if gcd == 1:
            return False
        else:
            return True

    def deflate(self):
        for i in range(self.an.degree()):
            an_factors = [factor_tuple[0] for factor_tuple in self.an.factor_list()[1]]
            bn_factors = [factor_tuple[0] for factor_tuple in self.bn.factor_list()[1]]
            for factor in an_factors:
                if factor in bn_factors and factor.compose(Poly(n-1)) in bn_factors:
                    self.an = Poly(cancel(self.an/factor))
                    self.bn = Poly(cancel(self.bn/(factor * factor.compose(Poly(n-1)))))
                    continue


if __name__ == "__main__":
    bn = sympy.Poly(list([-1, 14, -84, 280, -560, 672, -448, 128, 0]), n)
    aan = sympy.Poly([4, -56, 360, -1384, 3476, -5844, 6414, -4170, 1215], n)
    mypcf = PCF(aan.all_coeffs(), (bn * aan.compose(sympy.Poly(n + 1))).all_coeffs())
    mypcf.deflate()
    mypcf.moving_canonical_form()
    pass
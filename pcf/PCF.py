from __future__ import annotations
import sympy
from sympy import *
from typing import List

n = sympy.Symbol("n")


class PCF:

    def __init__(self: PCF, an_coefficients: List[int], bn_coefficients: List[int], value=None, c_top=None, c_bot=None, precision=0):
        """
        an_coefficients, bn_coefficients: lists of integers from the largest power to the smallest power.
        """
        self.an = Poly(an_coefficients, n)
        self.bn = Poly(bn_coefficients, n)
        self.value = value
        # Important, if we assign [] in the def row, it will use the same array for every object.
        self.c_top = c_top if c_top else []
        self.c_bot = c_bot if c_bot else []
        self.precision = precision

    def moving_canonical_form(self: PCF):
        # Should always be real roots. (If we find out this isn't the case then we need to modify this)
        bn_roots = self.bn.all_roots()

        # In case bn is a constant (has no roots) we still want an to have the canonical roots
        # => (the smallest root to be in (-1,0] )
        if len(bn_roots) == 0:
            an_real_roots = self.an.real_roots()
            an_rational_roots = self.an.ground_roots()

            # If some of the roots are irrational, it makes the coefficients look ugly, so I decided not to move them.
            # an_rational_roots is a dict {root:power_of_root} while an_real_roots is a list of all of the roots,
            # including multiple repeats.
            if len(an_real_roots) == 0 or len(an_real_roots) != sum(an_rational_roots.values()):
                return self.an, self.bn

            largest_root = max(an_real_roots)

        else:
            largest_root = max(bn_roots)
        # We want the largest root to be in (-1,0].
        return self.bn.compose(Poly(n + largest_root)), self.an.compose(Poly(n + largest_root))

    def inflating_canonical_form(self: PCF):
        top = self.bn
        bot = self.an * self.an.compose(Poly(n-1))
        gcd = sympy.gcd(top, bot)
        return Poly(cancel(top/gcd), n), Poly(cancel(bot/gcd), n)

    def get_canonical_form(self: PCF):
        top, bot = self.inflating_canonical_form()
        return PCF(bot.all_coeffs(), top.all_coeffs()).moving_canonical_form()

    def get_canonical_form_string(self: PCF):
        an, bn = self.get_canonical_form()
        return str(bn / an)

    def __str__(self: PCF):
        return f'an: {self.an.all_coeffs()}\t|\tbn: {self.bn.all_coeffs()}'

    def is_inflation(self: PCF):
        return sympy.gcd(self.bn, self.an * self.an.compose(Poly(n - 1))) != 1

    def deflate(self: PCF):
        for i in range(self.an.degree()):
            deflated: bool = False
            an_factors = [factor_tuple[0] for factor_tuple in self.an.factor_list()[1]]
            bn_factors = [factor_tuple[0] for factor_tuple in self.bn.factor_list()[1]]
            for factor in an_factors:
                if factor in bn_factors and factor.compose(Poly(n-1)) in bn_factors:
                    self.an = Poly(cancel(self.an/factor))
                    self.bn = Poly(cancel(self.bn/(factor * factor.compose(Poly(n-1)))))
                    deflated = True
            if not deflated:
                break # done! nothing's going to change anymore!


if __name__ == "__main__":
    bn = sympy.Poly(list([-1, 14, -84, 280, -560, 672, -448, 128, 0]), n)
    an = sympy.Poly([4, -56, 360, -1384, 3476, -5844, 6414, -4170, 1215], n)
    mypcf = PCF(aan.all_coeffs(), (bn * an.compose(sympy.Poly(n + 1))).all_coeffs())
    mypcf.deflate()
    mypcf.moving_canonical_form()

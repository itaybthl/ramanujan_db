import math
import numpy as np
import mpmath as mp
from mpmath import mpf
from decimal import Decimal, getcontext

class Constants:
'''
arbitrary-precision calculations of constants.

This class aims to contain most of https://en.wikipedia.org/wiki/List_of_mathematical_constants, 
excluding rationals, non-reals, and redundant constants (which are connected
via (1,1)-degree or (2,1)-degree relations to other constants already in here).
'''

# If there's a WARNING, it's a constant that takes a long time to calculate to 4000 precision. Find ways to calculate it more efficiently, if possible.
# If there's a TODO, it's a constant that needs to be added. Do that sometime.

    @staticmethod
    def set_precision(prec: int = 4000) -> None:
        '''
        set the precision (in significant digits in base 10).
        '''
        getcontext().prec = prec # might be redundant...
        mp.mp.dps = prec

    @staticmethod
    def pi() -> mpf:
        '''
        pi, fundamental circle constant.
        '''
        return mp.pi()
    
    @staticmethod
    def phi() -> mpf:
        '''
        golden ratio, positive root of phi^2 - phi - 1.
        '''
        return mp.phi()
    
    @staticmethod
    def e() -> mpf:
        '''
        euler number, base of the natural logarithm.
        '''
        return mp.e()
    
    @staticmethod
    def gamma() -> mpf:
        '''
        euler mascheroni constant, relating the harmonic series and the natural log.
        '''
        return mp.euler()
    
    @staticmethod
    def C() -> mpf:
        '''
        catalan constant, important to combinatorics, topology, and more.
        '''
        return mp.catalan()
    
    @staticmethod
    def Zeta3() -> mpf:
        '''
        apery constant, appears often in physics.
        '''
        return mp.apery()
    
    @staticmethod
    def K0() -> mpf:
        '''
        khinchin constant, a surprising fundamental constant in continued fractions.
        WARNING: Very inefficient to calculate! Handle with care!
        '''
        return mp.khinchin()
    
    @staticmethod
    def A() -> mpf:
        '''
        glaisher kinkelin constant, related to gamma functions and zeta functions.
        WARNING: Very inefficient to calculate! Handle with care!
        '''
        return mp.glaisher()
    
    @staticmethod
    def M() -> mpf:
        '''
        meissel mertens constant, one of many constants relating prime numbers.
        WARNING: Very inefficient to calculate! Handle with care!
        '''
        return mp.mertens()
    
    @staticmethod
    def Pi2() -> mpf:
        '''
        twin primes constant, central to the twin primes conjecture.
        WARNING: Very inefficient to calculate! Handle with care!
        '''
        return mp.twinprime()
    
    @staticmethod
    def G025() -> mpf:
        '''
        gamma(0.25), appears often in other constants.
        WARNING: Inefficient to calculate, but not as much as the others.
        '''
        return mp.gamma(0.25)
    
    @staticmethod
    def G() -> mpf:
        '''
        gauss constant, related to Bernoulli's lemniscate.
        '''
        return 1 / mp.agm(1, mp.sqrt(2))
    
    @staticmethod
    def L1() -> mpf:
        '''
        first lemniscate constant, related to Bernoulli's lemniscate.
        '''
        return Constants.G() * mp.pi / 2
    
    @staticmethod
    def L2() -> mpf:
        '''
        second lemniscate constant, related to Bernoulli's lemniscate.
        '''
        return 0.5 / Constants.G()
    
    @staticmethod
    def epi() -> mpf:
        '''
        gelfond constant, a result of the Gelfond-Schneider theorem.
        '''
        return mp.exp(mp.pi)
    
    @staticmethod
    def P() -> mpf:
        '''
        universal parabolic constant, a fundamental ratio of parabolas.
        '''
        sqrt2 = mp.sqrt(2)
        return mp.ln(1 + sqrt2) + sqrt2
    
    @staticmethod
    def sqrt2() -> mpf:
        '''
        square root of 2, also called Pythagoras constant.
        '''
        return mp.sqrt(2)
    
    @staticmethod
    def ln2() -> mpf:
        '''
        natural log of 2, has many series representations, and appears often in other constants.
        '''
        return mp.ln(2)
    
    #@staticmethod
    #def delta() -> mpf:
    #    '''
    #    first feigenbaum constant, important to bifurcation theory.
    #    '''
    #    # TODO how the hell is this calculated
    
    #@staticmethod
    #def alpha() -> mpf:
    #    '''
    #    second feigenbaum contsant, important to bifurcation theory.
    #    '''
    #    # TODO how the hell is this calculated
    
    @staticmethod
    def sqrt3() -> mpf:
        '''
        square root of 3, also called Theodorus constant.
        '''
        return mp.sqrt(3)
    
    @staticmethod
    def cbrt2() -> mpf:
        '''
        cube root of 2, related to doubling cubes.
        '''
        return mp.cbrt(2)
    
    @staticmethod
    def cbrt3() -> mpf:
        '''
        cube root of 3.
        '''
        return mp.cbrt(3)
    
    @staticmethod
    def root12of2() -> mpf:
        '''
        12th root of 2, basis of modern western music theory.
        '''
        return mp.root(2, 12)
    
    @staticmethod
    def psi() -> mpf:
        '''
        supergolden ratio, real root of psi^3 - psi^2 - 1.
        '''
        r = 3 * mp.sqrt(93)
        p1 = mp.cbrt((29 + r) / 2)
        p2 = mp.cbrt((29 - r) / 2)
        return (1 + p1 + p2) / 3
    
    @staticmethod
    def mu() -> mpf:
        '''
        hexagonal lattice connective constant, largest root of mu^4 - 4mu^2 + 2
        '''
        return mp.sqrt(2 + mp.sqrt(2))
    
    @staticmethod
    def Kprime() -> mpf:
        '''
        kepler bouwkamp constant, also called the polygon inscribing constant.
        WARNING: Very inefficient to calculate! Handle with care!
        '''
        def iteration(k):
            k *= 2
            z = mp.zeta(k)
            pow2 = mp.power(2, k)
            return (pow2 - 1) / k * z * (z - 1 - 1 / pow2)
        return mp.exp(-2 * mp.nsum(iteration, [1, mp.inf]))
    
    @staticmethod
    def W() -> mpf:
        '''
        wallis constant, real root of W^3 - 2W - 5
        '''
        r = mp.sqrt(1929)
        p1 = mp.cbrt((45 + r) / 18)
        p2 = mp.cbrt((45 - r) / 18)
        return p1 + p2
    
    @staticmethod
    def E() -> mpf:
        '''
        erdos borwein constant, related to Mersenne numbers.
        WARNING: Inefficient to calculate, but not as much as the others.
        '''
        def iteration(n):
            pow2 = mp.power(2, n)
            return mp.power(pow2, -n) * (pow2 + 1) / (pow2 - 1)
        return mp.nsum(iteration, [1, mp.inf], method='l')
    
    @staticmethod
    def Omega() -> mpf:
        '''
        omega constant, real root of Omega * e^Omega - 1.
        '''
        return mp.lambertw(1)
    
    @staticmethod
    def L_lim() -> mpf:
        '''
        laplace limit, important to Kepler's equation.
        '''
        def equation(x):
            s = mp.hypot(x, 1)
            return x * mp.exp(s) - s - 1
        return mp.findroot(equation, 0.66)
    
    @staticmethod
    def R_S() -> mpf:
        '''
        ramanujan soldner constant, central to the logarithmic integral.
        '''
        return mp.findroot(mp.li, 1.5)
    
    @staticmethod
    def L() -> mpf:
        '''
        liouville constant, a special case of Liouville numbers.
        '''
        return mp.nsum(lambda n: mp.power(10, -mp.fac(n)), [1, mp.inf])
    
    @staticmethod
    def C_1() -> mpf:
        '''
        first continued fraction constant.
        '''
        return mp.besseli(1, 2) / mp.besseli(0, 2)
    
    @staticmethod
    def R() -> mpf:
        '''
        ramanujan constant, an infamous almost-integer.
        '''
        return mp.exp(mp.pi * mp.sqrt(163))
    
    @staticmethod
    def D() -> mpf:
        '''
        dottie number, real root of cos(D) - D (in radians).
        '''
        return mp.findroot(lambda x: mp.cos(x) - x, 0.74)
    
    @staticmethod
    def C_Cahen() -> mpf:
        '''
        cahen constant, related to the Sylvester sequence.
        '''
        sylvester_dict = dict() # caching the sylvester sequence makes this way faster
        def sylvester(k):
            if k in sylvester_dict:
                return sylvester_dict[k]
            res = mpf(2) if k == 0 else 1 + mp.nprod(sylvester, [0, k - 1])
            sylvester_dict[k] = res
            return res
        return mp.nsum(lambda k: (-1)**k / (sylvester(k) - 1), [0, mp.inf])
    
    @staticmethod
    def G_S() -> mpf:
        '''
        gelfond schneider constant, also called the Hilbert number.
        '''
        return mp.power(2, mp.sqrt(2))
    
    @staticmethod
    def g() -> mpf:
        '''
        golden angle, related to the golden ratio.
        '''
        return 2 * mp.pi / (mp.phi ** 2)
    
    @staticmethod
    def S() -> mpf:
        '''
        sierpinski constant, related to Gauss constant and Euler-Mascheroni constant.
        WARNING: Inefficient to calculate, but not as much as the others.
        '''
        return mp.pi * (2 * mp.ln(2) + 3 * mp.ln(mp.pi) + 2 * mp.euler - 4 * mp.ln(mp.gamma(0.25)))
    
    #@staticmethod
    #def L_R() -> mpf:
    #    '''
    #    landau ramanujan constant, central to a theorem by Edmund Landau.
    #    '''
    #    # TODO implement prime sieve, then iterate over primes congruent 1 mod 4...
    
    @staticmethod
    def G_L() -> mpf:
        '''
        gieseking constant, also called Lobachevsky constant.
        '''
        return mp.clsin(2 , mp.pi / 3)
    
    #@staticmethod
    #def beta() -> mpf:
    #    '''
    #    bernstein constant, describing errors of best uniform approximations.
    #    '''
    #    # TODO implement Varga&Carpenter algorithm?
    
    @staticmethod
    def T() -> mpf:
        '''
        tribonacci constant, real root of T^3 - T^2 - T - 1
        '''
        r = 3 * mp.sqrt(33)
        p1 = mp.cbrt(19 + r)
        p2 = mp.cbrt(19 - r)
        return (1 + p1 + p2) / 3
    
    # TODO Brun constant: need to iterate over twin primes...
    
    @staticmethod
    def rho() -> mpf:
        '''
        plastic number, real root of rho^3 - rho - 1.
        '''
        r = mp.sqrt(69) / 18
        p1 = mp.cbrt(0.5 + r)
        p2 = mp.cbrt(0.5 - r)
        return p1 + p2
    
    @staticmethod
    def z975() -> mpf:
        '''
        z score for 97.5 percentile point, commonly used alongside normal distributions.
        '''
        return mp.sqrt(2) * mp.erfinv(0.95)
    
    @staticmethod
    def tau() -> mpf:
        '''
        prouhet thue morse constant, appears in probability.
        '''
        return 0.25 * (2 - mp.nprod(lambda n: 1 - mp.power(2, -mp.power(2, n)), [0, mp.inf]))
    
    @staticmethod
    def lambda_GD() -> mpf:
        '''
        golomb dickman constant, appears in random permutation theory and number theory.
        WARNING: Very inefficient to calculate! Handle with care!
        '''
        return mp.quad(lambda x: mp.exp(mp.li(x)), [0, 1])
    
    #@staticmethod
    #def c() -> mpf:
    #    '''
    #    asymptotic lebesgue constant.
    #    '''
    #    # TODO this code seems right but gives wrong result???
    #    s = -mp.digamma(0.5)
    #    return 4 / mp.pi ** 2 * (mp.nsum(lambda k: 2 * mp.ln(k) / (4 * mp.power(k, 2) - 1), [1, mp.inf]) + s)
    
    #@staticmethod
    #def C_FT() -> mpf:
    #    '''
    #    feller tornier constant, describing certain prime factorizations
    #    '''
    #    # TODO need primes again...
    
    #@staticmethod
    #def C_10() -> mpf:
    #    '''
    #    base10 champernowne constant.
    #    '''
    #    # TODO this code seems right but gives wrong result???
    #    return mp.nsum(lambda n: n / mp.power(10, mp.nsum(lambda k: mp.ceil(mp.log(k + 1, 10)), [1, n])), [1, mp.inf])
    
    @staticmethod
    def __calc_poly__(coeff_list, x):
        # lower index = lower exponent, so this is reversed compared to the usual representation of polynomials! (with falling exponents...)
        return mp.nsum(lambda n: coeff_list[int(n)] * x ** n, [0, len(coeff_list) - 1])
    
    @staticmethod
    def sigma_10() -> mpf:
        '''
        salem constant, smallest known Salem number.
        '''
        return mp.findroot(lambda x: __calc_poly__([1, 1, 0, -1, -1, -1, -1, -1, 0, 1, 1], x), 1.2)
    
    @staticmethod
    def beta_Levy() -> mpf:
        '''
        first levy constant, related to asymptotic behavior in continued fractions.
        '''
        return mp.pi ** 2 / (12 * mp.ln(2))
    
    @staticmethod
    def etothebeta() -> mpf:
        '''
        second levy constant, related to asymptotic behavior in continued fractions.
        '''
        return mp.exp(Constants.beta_Levy())
    
    #@staticmethod
    #def C_CE() -> mpf:
    #    '''
    #    copeland erdos constant.
    #    '''
    #    # TODO need primes again...
    
    #@staticmethod
    #def A_Pi() -> mpf:
    #    '''
    #    mills constant, "smallest" real that generates prime numbers via exponents.
    #    '''
    #    # TODO how the hell is this calculated
    
    @staticmethod
    def delta_G() -> mpf:
        '''
        gompertz constant, appears in some special integrals.
        '''
        return -mp.e * mp.ei(-1)
    
    @staticmethod
    def V_dp() -> mpf:
        '''
        van der pauw constant, involved in the Van der Pauw method.
        '''
        return mp.pi / mp.ln(2)
    
    @staticmethod
    def theta_m() -> mpf:
        '''
        magic angle, important to magnetic resonance imaging.
        '''
        return mp.atan(mp.sqrt(2))
    
    #@staticmethod
    #def C_Artin() -> mpf:
    #    '''
    #    artin constant, related to Artin's conjecture on primitive roots.
    #    '''
    #    # TODO need primes again...
    
    @staticmethod
    def C_P() -> mpf:
        '''
        porter constant, related to the efficiency of Euclid algorithm.
        WARNING: Inefficient to calculate, but not as much as the others.
        '''
        ln2 = mp.ln(2)
        pi2 = mp.pi ** 2
        return 6 * ln2 / pi2 * (3 * ln2 + 4 * mp.euler - 24 / pi2 * mp.zeta(2, derivative=1) - 2) - 0.5
    
    @staticmethod
    def L_Lochs() -> mpf:
        '''
        lochs constant, involved in Lochs' theorem regarding continued fractions.
        '''
        return 6 * mp.ln(2) * mp.ln(10) / mp.pi ** 2
    
    @staticmethod
    def D_V() -> mpf:
        '''
        devicci tesseract constant, describing the
        largest cube that can pass through a 4D hypercube.
        '''
        return mp.findroot(lambda x: __calc_poly__([16, 0, 16, 0, -7, 0, -28, 0, 4], x), 1)
    
    @staticmethod
    def C_N() -> mpf:
        '''
        niven constant, largest exponent in prime factorizations "on average".
        WARNING: Very inefficient to calculate! Handle with care!
        '''
        return 1 + mp.nsum(lambda n: 1 - 1 / mp.zeta(n), [2, mp.inf])
    
    #@staticmethod
    #def S_Pi() -> mpf:
    #    '''
    #    stephens constant, density of some subsets of primes.
    #    '''
    #    # TODO need primes again...
    
    @staticmethod
    def P_Dragon() -> mpf:
        '''
        paperfolding constant, related to the dragon curve.
        '''
        def iteration(n):
            two_n = mp.power(2, n)
            return mp.power(2, -two_n) / (1 - mp.power(2, -4 * two_n))
        return mp.nsum(iteration, [0, mp.inf])
    
    @staticmethod
    def psi_Fib() -> mpf:
        '''
        reciprocal fibonacci constant, sum of reciprocals of Fibonacci numbers.
        WARNING: Very inefficient to calculate! Handle with care!
        ''' # consider using gosper's accelerated series?
        return mp.nsum(lambda n: 1 / mp.fib(n), [1, mp.inf])
    
    @staticmethod
    def Delta3() -> mpf:
        '''
        robbins constant, mean length of random line segments in a unit cube.
        '''
        sqrt2 = mp.sqrt(2)
        sqrt3 = mp.sqrt(3)
        p1 = (4 + 17 * sqrt2 - 6 * sqrt3 - 7 * mp.pi) / 105
        p2 = mp.ln(1 + sqrt2) / 5
        p3 = mp.ln(2 + sqrt3) * 2 / 5
        return p1 + p2 + p3
    
    @staticmethod
    def W_S() -> mpf:
        '''
        weierstrass constant.
        WARNING: Inefficient to calculate, but not as much as the others.
        '''
        return mp.power(2, 1.25) * mp.sqrt(mp.pi) * mp.exp(mp.pi / 8) / mp.gamma(0.25) ** 2
    
    @staticmethod
    def F() -> mpf:
        '''
        fransen robinson constant, related to the reciprocal Gamma function.
        WARNING: Very inefficient to calculate! Handle with care!
        '''
        return mp.quad(mp.rgamma, [0, mp.inf])
    
    @staticmethod
    def C_2() -> mpf:
        '''
        second du bois reymond constant.
        '''
        return (mp.exp(2) - 7) / 2
    
    @staticmethod
    def delta_ETF() -> mpf:
        '''
        erdos tenenbaum ford constant, appears in number theory.
        '''
        ln2 = mp.ln(2)
        return 1 - (1 + mp.ln(ln2)) / ln2
    
    @staticmethod
    def lambda_C() -> mpf:
        '''
        conway constant, related to the Look-and-say sequence.
        '''
        return mp.findroot(lambda x: __calc_poly__([-6, 3, -6, 12, -4, 7, -7, 1, 0, 5, -2, -4, -12, 2, 7, 12, -7, -10, -4, 3, 9, -7, 0, -8, 14, -3, 9, 2, -3, -10, -2, -6, 1, 10, -3, 1, 7, -7, 7, -12, -5, 8, 6, 10, -8, -8, -7, -3, 9, 1, 6, 6, -2, -3, -10, -2, 3, 5, 2, -1, -1, -1, -1, -1, 1, 2, 2, -1, -2, -1, 0, 1], x) , 1.3)
    
    #@staticmethod
    #def sigma() -> mpf:
    #    '''
    #    hafner sarnak mccurley constant, related to coprime determinants of integer matrices.
    #    '''
    #    # TODO need primes again...
    
    #@staticmethod
    #def B_H() -> mpf:
    #    '''
    #    backhouse constant, constructed using power series with prime coefficients.
    #    '''
    #    # TODO how the hell is this calculated
    
    #@staticmethod
    #def V() -> mpf:
    #    '''
    #    viswanath constant, related to random Fibonacci sequences.
    #    '''
    #    # TODO how the hell is this calculated
    
    @staticmethod
    def q() -> mpf:
        '''
        komornik loreti constant, related to non-integer representations.
        WARNING: Inefficient to calculate, but not as much as the others.
        '''
        return mp.findroot(lambda q: mp.nprod(lambda n: 1 - mp.power(q, -mp.power(2, n)), [0, mp.inf]) + (q - 2) / (q - 1), 2)
    
    #@staticmethod
    #def C_HBM() -> mpf:
    #    '''
    #    heath brown moroz constant, related to the cubic surface w^3 = xyz
    #    '''
    #    # TODO need primes again...
    
    @staticmethod
    def S_MRB() -> mpf:
        '''
        mrb constant, named after Marvin Ray Burns.
        WARNING: Very inefficient to calculate! Handle with care!
        '''
        return mp.nsum(lambda n: mp.power(-1, n) * (mp.root(n, n) - 1), [1, mp.inf])
    
    #@staticmethod
    #def rho_Pi() -> mpf:
    #    '''
    #    prime constant, constructed from indicators of prime numbers.
    #    '''
    #    # TODO need primes again...
    
    @staticmethod
    def sigma_S() -> mpf:
        '''
        somos quadratic recurrence constant, related to the Lerch transcendent.
        WARNING: Very inefficient to calculate! Handle with care!
        '''
        return mp.nprod(lambda n: mp.power(n, mp.power(2, -n)), [1, mp.inf])
    
    #@staticmethod
    #def alpha_F() -> mpf:
    #    '''
    #    foias constant, only number for which a certain recurrence diverges.
    #    '''
    #    # TODO how the hell is this calculated (maybe findroot???)
    
    @staticmethod
    def L_D() -> mpf:
        '''
        unit disk logarithmic capacity.
        WARNING: Inefficient to calculate, but not as much as the others.
        '''
        return mp.power(mp.gamma(0.25), 2) / (4 * mp.power(mp.pi, 1.5))
    
    #@staticmethod
    #def rho_Pi() -> mpf:
    #    '''
    #    taniguchi constant, a kind of Euler product.
    #    '''
    #    # TODO need primes again...

'''
List of rejected constants:
    No rationals allowed:
        1, 2, 0.5, 0, -1
    No complex numbers allowed:
        i
    No known method to compute:
        Bloch constant, Landau constant, Third Landau constant, de Bruijn-Newman contant,
        Binary Alphabet Chvátal-Sankoff constant, Chaitin constant(s) (in general) (sorta),
        Embree-Trefethen constant
    Related to constants already added:
        sqrt(5): (1,1)-degree relation with phi
        Silver ratio: (1,1)-degree relation with sqrt(2)
        Lemniscate constant: (1,1)-degree relation with First Lemniscate constant
        Second Hermite constant: (2,1)-degree relation with sqrt(3)
        Second Favard constant: (2,2)-degree relation with pi
        First Nielsen-Ramanujan constant: (2,2)-degree relation with pi
        Lieb square ice constant: (2,1)-degree relation with sqrt(3)
'''

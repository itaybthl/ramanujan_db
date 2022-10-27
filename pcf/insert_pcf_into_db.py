import sys
import mpmath
from db import models
from db import ramanujan_db

from db.models import PcfCanonicalConstant, Constant

import sympy
from sympy import Poly
from sqlalchemy.exc import IntegrityError
from pcf.PCF import PCF

# TODO: fix this (the import of ramanujan doesn't seem to work)

# from ramanujan.enumerators.FREnumerator import check_for_fr
# from ramanujan.enumerators.FREnumerator import FIRST_ENUMERATION_MAX_DEPTH as MAX_ITERATOR_STEPS
MAX_ITERATOR_STEPS = 1402

VIOLATING_UNIQUE_VALUE_IN_DB_STRING = '(psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint "pcf_canonical_constant_p_q_key"'

def add_canonical_pcf(cannonical_form_numerator, cannonical_form_denominator):
    db_handle = ramanujan_db.RamanujanDB()
    pcf = PcfCanonicalConstant()
    pcf.base = Constant()
    pcf.p = cannonical_form_numerator
    pcf.q = cannonical_form_denominator
    #TODO: change to all_all([pcfs])
    db_handle.session.add(pcf)
    try:
        db_handle.session.commit()
    except IntegrityError as e:
        raise e
    finally:
        db_handle.session.close()


def add_pcf(pcf, override_fr_check=False):
    """
    Expect PCF object.
    raises IntegrityError if pcf already exists in the db.
    """
    if not override_fr_check:
        with mpmath.workdps(20_000):
            pass
            # TODO: fix this
            # an_iterator = poly_to_iterator(pcf.an)
            # bn_iterator = poly_to_iterator(pcf.bn)
            # an_degree = pcf.an.degree()
            # if not check_for_fr(an_iterator, bn_iterator, an_degree)[0]:
            #     raise NoFRException()
    top, bot = pcf.get_cannonical_form()
    # By default the coefs are of type sympy.core.numbers.Integer but sql need them to be integers
    integer_top_coeffs = [int(coef) for coef in top.all_coeffs()]
    integer_bot_coeffs = [int(coef) for coef in bot.all_coeffs()]
    add_canonical_pcf(integer_top_coeffs, integer_bot_coeffs)


def add_multiple_pcfs(pcfs):
    """
    Expects a list of PCF objects.
    """
    successful = []
    unsuccessful = {"Already exist": [], "No FR": []}
    for pcf in pcfs:
        try:
            add_pcf(pcf)
            successful.append(pcf)
        except IntegrityError as e:
            if e.args[0].startswith(VIOLATING_UNIQUE_VALUE_IN_DB_STRING):
                # This means the pcf is already in the db.
                unsuccessful["Already exist"].append(pcf)
            else:
                raise e
        except NoFRException as e:
            unsuccessful["No FR"].append(pcf)
    return successful, unsuccessful


def parse_CF_to_lists(cf):
    partial_numerator = [int(coef) for coef in cf.p]
    partial_denuminator = [int(coef) for coef in cf.q]
    return (partial_numerator, partial_denuminator)

def canonical_form_to_pcf(canonical_form):
    """
    Receive the canonical form of a pcf (an = 1 bn=(bn/an*a(n+1)) )
    and return a pcf of this canonical form.
    Notice there may be many pcfs that fit the same canonical form, this returns just one of them.
    TODO: add link to the doc which explains this
    """
    n = sympy.Symbol("n")
    numerator = Poly(canonical_form[0], n)
    denumenator = Poly(canonical_form[1], n)

    an = denumenator.compose(Poly(n+1))
    bn = numerator * an

    pcf = PCF(an.all_coeffs(), bn.all_coeffs())
    pcf.deflate()
    return pcf


def get_canonical_forms():
    db_handle = ramanujan_db.RamanujanDB()
    all_pcfs = [parse_CF_to_lists(pcf) for pcf in db_handle.cfs.all()]
    return all_pcfs

def get_actual_pcfs_from_db():
    """
    return a list of PCFs
    """
    canonical_forms = get_canonical_forms()
    pcfs = [canonical_form_to_pcf(can_form) for can_form in canonical_forms]
    return pcfs

class NoFRException(Exception):
    pass


def poly_to_iterator(poly):
    def iterator(poly, max_runs, start_n=0):
        # be careful before setting start_n!=0
        for i in range(start_n, max_runs):
            yield int(poly.eval(i))
    return iterator(poly, MAX_ITERATOR_STEPS)


def main():
    pcfs = get_actual_pcfs_from_db()
    [print(pcf) for pcf in pcfs]
    print("aa")

if __name__ == "__main__":
    main()
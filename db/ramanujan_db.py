import logging
import config
import mpmath
from . import models
import sympy
from sympy import Poly
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import sessionmaker
from psycopg2.errors import UniqueViolation
from pcf.PCF import PCF
from typing import Tuple, List, Dict
CanonicalForm = Tuple[List[int], List[int]]

# TODO: fix this (the import of ramanujan doesn't seem to work)

# from ramanujan.enumerators.FREnumerator import check_for_fr
# from ramanujan.enumerators.FREnumerator import FIRST_ENUMERATION_MAX_DEPTH as MAX_ITERATOR_STEPS
MAX_ITERATOR_STEPS = 1402

class RamanujanDB(object):
    def __init__(self):
        logging.debug("Trying to connect to database")
        self._engine = create_engine(config.get_connection_string(), echo=False)
        Session = sessionmaker(bind=self._engine)
        self.session = Session()
        logging.debug("Connected to database")

    @property
    def constants(self):
        return self.session.query(models.Constant).order_by(models.Constant.const_id)

    @property
    def cfs(self):
        return self.session.query(models.PcfCanonicalConstant).order_by(models.PcfCanonicalConstant.const_id)

    def add_pcf_canonical(self, canonical_form_numerator: List[int], canonical_form_denominator: List[int]) -> None:
        # TODO implement add_pcf_canonicals that uploads multiple at a time
        pcf = models.PcfCanonicalConstant()
        pcf.base = models.Constant()
        pcf.p = canonical_form_numerator
        pcf.q = canonical_form_denominator
        self.session.add(pcf)
        
        # yes, commit and check error is better than preemptively checking if unique and then adding,
        # since the latter is two SQL commands instead of one, which breaks on "multithreading" for example
        # and also should be generally slower
        # also this can't be turned into a kind of INSERT pcf ON CONFLICT DO NOTHING statement
        # since this needs the base Constant to be added first so it gains its const_id...
        # TODO investigate if triggers can make something like ON CONFLICT DO NOTHING work anyway,
        # possibly will help with the previous TODO... maybe something like:  https://stackoverflow.com/questions/46105982/postgres-trigger-function-on-conflict-update-another-table
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    class NoFRException(Exception):
        pass
    
    def add_pcf(self, pcf: PCF, check_fr: bool = True) -> None:
        """
        Expect PCF object.
        raises IntegrityError if pcf already exists in the db.
        """
        if check_fr:
            with mpmath.workdps(20_000):
                pass
                # TODO: fix this
                # an_iterator = poly_to_iterator(pcf.an)
                # bn_iterator = poly_to_iterator(pcf.bn)
                # an_degree = pcf.an.degree()
                # if not check_for_fr(an_iterator, bn_iterator, an_degree)[0]:
                #     raise self.NoFRException()
        top, bot = pcf.get_canonical_form()
        # By default the coefs are of type sympy.core.numbers.Integer but sql need them to be integers
        self.add_pcf_canonical([int(coef) for coef in top.all_coeffs()], [int(coef) for coef in bot.all_coeffs()])
    
    def add_pcfs(self, pcfs: List[PCF]) -> Tuple[List[PCF], Dict[str, List[PCF]]]:
        """
        Expects a list of PCF objects.
        """
        successful = []
        unsuccessful = {"Already exist": [], "No FR": []}
        for pcf in pcfs:
            try:
                self.add_pcf(pcf)
                successful.append(pcf)
            except IntegrityError as e:
                if not isinstance(e.orig, UniqueViolation):
                    raise e # otherwise already in the DB
                unsuccessful["Already exist"].append(pcf)
            except self.NoFRException:
                unsuccessful["No FR"].append(pcf)
        return successful, unsuccessful
    
    def add_pcfs_silent(self, pcfs: List[PCF]) -> None:
        """
        Expects a list of PCF objects. Doesn't return which PCFs were successfully or unsuccessfully added.
        """
        for pcf in pcfs:
            try:
                self.add_pcf(pcf)
            except IntegrityError as e:
                if not isinstance(e.orig, UniqueViolation):
                    raise e # otherwise already in the DB
            except self.NoFRException:
                pass
    
    @staticmethod
    def parse_cf_to_lists(cf: models.PcfCanonicalConstant) -> CanonicalForm:
        return [int(coef) for coef in cf.p], [int(coef) for coef in cf.q]
    
    @staticmethod
    def canonical_form_to_pcf(canonical_form: CanonicalForm) -> PCF:
        """
        Receive the canonical form of a pcf (an := 1 ; bn := bn / (an*a(n+1)))
        and return a pcf of this canonical form.
        Notice there may be many pcfs that fit the same canonical form, this returns just one of them.
        TODO: add link to the doc which explains this
        """
        n = sympy.Symbol("n")
        an = Poly(canonical_form[1], n).compose(Poly(n + 1))
        bn = Poly(canonical_form[0], n) * an
        pcf = PCF(an.all_coeffs(), bn.all_coeffs())
        pcf.deflate()
        return pcf
    
    def get_canonical_forms(self) -> List[CanonicalForm]:
        return [parse_cf_to_lists(pcf) for pcf in self.cfs.all()]
    
    def get_actual_pcfs(self) -> List[PCF]:
        """
        return a list of PCFs
        """
        return [canonical_form_to_pcf(c) for c in self.get_canonical_forms()]
    
    @staticmethod
    def poly_to_iterator(poly):
        def iterator(poly, max_runs, start_n=0):
            # be careful before setting start_n!=0
            for i in range(start_n, max_runs):
                yield int(poly.eval(i))
        return iterator(poly, MAX_ITERATOR_STEPS)


def main():
    [print(pcf) for pcf in get_actual_pcfs_from_db()]
    print("aa")


if __name__ == "__main__":
    main()

from db import models
from db import ramanujan_db
from datetime import date,timedelta
import uuid
import logging 

logging.basicConfig(filename="families.log",filemode="w",level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

db_handle = ramanujan_db.RamanujanDB()

def getLastResults(model):
    today = date.today()
    yesterday = today - timedelta(days=1)
    return db_handle.session.query(model).filter(model.insertion_date > yesterday)

def merge_families(family_1_id, family_2_id):
    if family_1_id == family_2_id:
        logging.info('families the same, skip merging')
        return
    family_1 = db_handle.session.query(models.CfFamily).filter(models.CfFamily.family_id == family_1_id).one()
    family_2 = db_handle.session.query(models.CfFamily).filter(models.CfFamily.family_id == family_2_id).one()
    assert(family_1)
    assert(family_2)
    family_1_cfs = db_handle.session.query(models.Cf).filter(models.Cf.family_id == family_1_id).all()
    family_2_cfs = db_handle.session.query(models.Cf).filter(models.Cf.family_id == family_2_id).all()
    family_1_const = db_handle.session.query(models.Constant).filter(models.Constant.constant_id == family_1.constant).one()
    family_2_const = db_handle.session.query(models.Constant).filter(models.Constant.constant_id == family_2.constant).one()
    assert(family_1_const)
    assert(family_2_const)
    assert(len(family_1_cfs) > 0)
    assert(len(family_2_cfs) > 0)

    if family_1_const.startswith("cf const"):
        for cf in family_1_cfs:
            cf.family_id = family_2_id
        db_handle.session.add(family_1_cfs)
        db_handle.session.query(models.CfFamily).filter(models.CfFamily.family_id == family_1_id).delete()
        db_handle.session.query(models.Constant).filter(models.Constant.constant_id == family_1.constant).delete()
    elif family_2_const.startswith("cf const"):
        for cf in family_2_cfs:
            cf.family_id = family_1_id
        db_handle.session.add(family_2_cfs)
        db_handle.session.query(models.CfFamily).filter(models.CfFamily.family_id == family_2_id).delete()
        db_handle.session.query(models.Constant).filter(models.Constant.constant_id == family_2.constant).delete()
    else:
        logging.critical("Eurika!!!!!!")
        logging.critical(f'found relations between 2 constants {family_2_const.name} and {family_1_const.name}')
        #TODO: call 911

    db_handle.session.commit()

def set_family(cf,family_id):
    cf.family_id = family_id
    db_handle.session.add([cf])

def generate_family(cf_1,cf_2):
    family_id = uuid.uuid4()
    const_id = uuid.uuid4()
    const = models.Constant(name = const_id,description ="cf const "+ const_id)
    db_handle.session.add([const])
    family = models.CfFamily(family_id = family_id, description = "", constant = const_id)
    return family

def get_family_by_const_relation(result):
    constant = db_handle.session.query(models.Constant).filter(models.Constant.constant_id == result.constant_id).one()
    cf = db_handle.session.query(models.Cf).filter(models.Cf.cf_id == result.cf_id).one()
    assert(constant)
    assert(cf)
    if cf.family_id:
        curr_family = db_handle.session.query(models.CfFamily).filter(models.CfFamily.family_id == cf.family_id).one()
        assert(curr_family)
        curr_family_const = db_handle.session.query(models.Constant).filter(models.Constant.constant_id == curr_family.constant).one()
            
        if curr_family_const.desciption.startswith("cf const"):
            const_id = constant.constant_id
        else:
            logging.critical("Eurika!!!!!!")
            logging.critical(f'found relations between 2 constants {curr_family_const.name} and {constant.name}')
            const_id = curr_family_const.constant_id

            return models.CfFamily(family_id = cf.family_id, description = "", constant = const_id)
    else:
        logging.debug(f'create new family for cf num: {cf.partial_numerator}, denom: {cf.partial_denominator}')
        return models.CfFamily(family_id = uuid.uuid4(), description = "", constant = constant.constant_id)

def link_families_by_const_relations(constants_results):
    families = []
    logging.info('linking families for const relations')
    logging.debug(f'num of constants result {len(constants_results)}')
    for result in constants_results:
        try:
            family = get_family_by_const_relation(result)
            families.append(family)
        except Exception as e:
            logging.error("Exception occurred", exc_info=True)
        

    db_handle.session.add(families)
    db_handle.session.commit()

def get_family_by_cf_relation(result):
    source_cf = db_handle.session.query(models.Cf).filter(models.Cf.cf_id == result.source_cf).one()
    target_cf = db_handle.session.query(models.Cf).filter(models.Cf.cf_id == result.target_cf).one()
    assert(source_cf)
    assert(target_cf)
    if source_cf.family_id and target_cf.family_id:
        logging.info('merging families')
        merge_families(source_cf.family_id, target_cf.family_id)
    elif source_cf.family_id:
        set_family(target_cf,source_cf.family_id)
    elif target_cf.family_id:
        set_family(source_cf,target_cf.family_id)
    else:
        logging.info('generating new family')
        family = generate_family(source_cf,target_cf)
        set_family(source_cf,family.family_id)
        set_family(target_cf,family.family_id)
    return family


def link_families_by_cf_relations(cf_results):
    families = []
    for result in cf_results:
        try:
            family = get_family_by_cf_relation(result)
            if family:
                families.append(family)
        except Exception as e:
            logging.error("Exception occurred", exc_info=True)

    db_handle.session.add(families)
    db_handle.session.commit()


def run_job():
    constants_results = getLastResults(models.CfConstantConnection)
    cf_results = getLastResults(models.ContinuedFractionRelation)

    link_families_by_const_relations(constants_results)
    link_families_by_cf_relations(cf_results)


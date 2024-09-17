from .calpha import CalphaMapping
from .calphacbeta import CalphaCbetaMapping
from .heavyatom import HeavyAtomMapping
from .awsem import AwsemMapping, AwsemBackboneMapping

def assign_mapping(code, topology):
    MAPPINGS = {"CA":CalphaMapping, "CACB":CalphaCbetaMapping,
                "All-Atom":HeavyAtomMapping, "AWSEM":AwsemMapping, 
                "AWSEM_backbone":AwsemBackboneMapping}
    return MAPPINGS[code](topology)

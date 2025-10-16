from ariadne import ObjectType
from domain.walks import get_treatment

walk = ObjectType("Walk")

walk.set_field("treatment", get_treatment)
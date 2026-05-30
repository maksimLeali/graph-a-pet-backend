from ariadne import ObjectType

import domain.cures as cures_domain

cure = ObjectType("Cure")

cure.set_field('treatment', cures_domain.get_treatment)
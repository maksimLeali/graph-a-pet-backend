from ariadne import ObjectType

from domain.reports import get_coordinates, get_pet

report = ObjectType('Report')

report.set_field('coordinates', get_coordinates)

report.set_field('pet', get_pet)
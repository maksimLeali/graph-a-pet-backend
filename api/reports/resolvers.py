from ariadne import ObjectType

from domain.reports import get_coordinates

report = ObjectType('Report')

report.set_field('coordinates', get_coordinates)
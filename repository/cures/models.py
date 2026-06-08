from enum import Enum
from repository import db, Base

class FrequencyUnit(Enum):
    DAILY = "DAILY",
    WEEKLY = "WEEKLY",
    MONTHLY = "MONTHLY",
    YEARLY = "YEARLY"


class Cure(Base):
    __tablename__ = 'cures'    
    treatment_id= db.Column(db.String, db.ForeignKey('treatments.id'))
    frequency_value = db.Column(db.Integer)
    frequency_unit = db.Column(db.Enum(FrequencyUnit))
    frequency_times = db.Column(db.Integer)

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": str(self.created_at),
            "treatment_id": self.treatment_id,            
            "frequency_value": self.frequency_value,
            "frequency_unit": self.frequency_unit.name if self.frequency_unit else None,
            "frequency_times": self.frequency_times,
        }

from typing import List
from sqlalchemy.orm import Session
from app.soil_analysis.domain.schemas import SoilAnalysisCreate, SoilClassificationCreate
from app.soil_analysis.infrastructure.orm_models import SoilAnalysis, SoilClassification, SoilType
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

class SoilAnalysisRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_analysis(self, analysis_data: SoilAnalysisCreate) -> SoilAnalysis:
        analysis = SoilAnalysis(**analysis_data.model_dump())
        self.db.add(analysis)
        self.db.flush()
        return analysis

    def create_classification(self, classification_data: SoilClassificationCreate) -> SoilClassification:
        classification = SoilClassification(**classification_data.model_dump())
        self.db.add(classification)
        return classification

    def save_changes(self):
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise DomainException(
                message=f"Error guardando los resultados: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    def get_analysis_by_task_id(self, task_id: int) -> SoilAnalysis:
        return self.db.query(SoilAnalysis)\
            .filter(SoilAnalysis.tarea_labor_id == task_id)\
            .first()
            
    def get_analysis_by_id(self, analysis_id: int) -> SoilAnalysis:
        return self.db.query(SoilAnalysis)\
            .filter(SoilAnalysis.id == analysis_id)\
            .first()

    def get_classifications_by_analysis_id(self, analysis_id: int) -> List[SoilClassification]:
        return self.db.query(SoilClassification)\
            .filter(SoilClassification.analisis_suelo_id == analysis_id)\
            .all()
            
    def get_soil_type_by_name(self, predicted_class: str) -> SoilType:
        return self.db.query(SoilType)\
            .filter(SoilType.nombre == predicted_class)\
            .first()
            
    def get_soil_type_by_id(self, soil_type_id: int) -> SoilType:
        return self.db.query(SoilType)\
            .filter(SoilType.id == soil_type_id)\
            .first()

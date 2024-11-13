from fastapi import status
from sqlalchemy.orm import Session
from app.soil_analysis.infrastructure.sql_repository import SoilAnalysisRepository
from app.infrastructure.common.common_exceptions import DomainException
import os
from dotenv import load_dotenv
        
load_dotenv(override=True)

class GetAnalysisStatusUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.soil_analysis_repository = SoilAnalysisRepository(db)        
        
    def get_analysis_status(self, analysis_id: int) -> dict:
        
        analysis = self.soil_analysis_repository.get_analysis_by_id(analysis_id)
        if not analysis:
            raise DomainException(
                message="No se encontró el análisis",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        classifications = self.soil_analysis_repository.get_classifications_by_analysis_id(analysis.id)

        return {
            "status": analysis.estado.value,
            "total_processed": len(classifications),
            "analysis_id": analysis.id
        }
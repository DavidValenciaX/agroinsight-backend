from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.cultural_practices.application.services.task_service import TaskService
from app.soil_analysis.domain.schemas import ClassificationResult, SoilAnalysisResult
from app.soil_analysis.infrastructure.sql_repository import SoilAnalysisRepository
from app.farm.application.services.farm_service import FarmService
from app.plot.infrastructure.sql_repository import PlotRepository
from app.user.domain.schemas import UserInDB
from app.cultural_practices.infrastructure.sql_repository import CulturalPracticesRepository

class GetAnalysisUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.soil_analysis_repository = SoilAnalysisRepository(db)
        self.task_service = TaskService(db)
        self.task_repository = CulturalPracticesRepository(db)
        self.plot_repository = PlotRepository(db)
        self.farm_service = FarmService(db)

    def get_analysis(self, analysis_id: int, current_user: UserInDB) -> SoilAnalysisResult:
        # Obtener análisis y sus clasificaciones
        analysis = self.soil_analysis_repository.get_analysis_by_id(analysis_id)
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Análisis de suelo no encontrado"
            )
            
        # Verificar que el usuario tenga acceso al análisis
        task = self.task_repository.get_task_by_id(analysis.tarea_labor_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea asociada no encontrada"
            )
            
        plot = self.plot_repository.get_plot_by_id(task.lote_id)
        if not plot:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Lote no encontrado"
            )
            
        if not self.farm_service.user_is_farm_admin(current_user.id, plot.finca_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para ver este análisis"
            )

        # Obtener las clasificaciones asociadas
        classifications = self.soil_analysis_repository.get_classifications_by_analysis_id(analysis.id)
            
        return SoilAnalysisResult(
            id=analysis.id,
            tarea_labor_id=analysis.tarea_labor_id,
            fecha_analisis=analysis.fecha_analisis,
            observaciones=analysis.observaciones,
            estado=analysis.estado,
            cantidad_imagenes=analysis.cantidad_imagenes,
            clasificaciones=[
                ClassificationResult(
                    id=classification.id,
                    imagen_url=classification.imagen_url,
                    resultado_analisis=classification.resultado_analisis_id,
                    confianza_clasificacion=classification.confianza_clasificacion,
                    prob_alluvial_soil=classification.prob_alluvial_soil,
                    prob_black_soil=classification.prob_black_soil,
                    prob_cinder_soil=classification.prob_cinder_soil,
                    prob_clay_soil=classification.prob_clay_soil,
                    prob_laterite_soil=classification.prob_laterite_soil,
                    prob_peat_soil=classification.prob_peat_soil,
                    prob_yellow_soil=classification.prob_yellow_soil
                )
                for classification in classifications
            ]
        )
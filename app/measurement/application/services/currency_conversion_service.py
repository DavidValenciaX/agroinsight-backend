from decimal import Decimal
from typing import Dict
import httpx
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.measurement.infrastructure.sql_repository import MeasurementRepository
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

class CurrencyConversionService:
    """Servicio para manejar conversiones entre diferentes monedas usando Frankfurter API"""
    
    FRANKFURTER_BASE_URL = "https://api.frankfurter.app"
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = MeasurementRepository(db)
        self._rates_cache = {}
        self._last_update = None
        self._cache_duration = timedelta(hours=1)  # Actualizar tasas cada hora

    def _get_latest_rates(self, base_currency: str) -> Dict[str, Decimal]:
        """Obtiene las tasas de cambio actualizadas desde Frankfurter API"""
        current_time = datetime.now()
        
        # Verificar si podemos usar el caché
        if (base_currency in self._rates_cache and 
            self._last_update and 
            current_time - self._last_update < self._cache_duration):
            return self._rates_cache[base_currency]

        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.FRANKFURTER_BASE_URL}/latest",
                    params={"base": base_currency}
                )
                response.raise_for_status()
                data = response.json()
                
                # Convertir las tasas a Decimal
                rates = {
                    currency: Decimal(str(rate))
                    for currency, rate in data["rates"].items()
                }
                
                # Actualizar el caché
                self._rates_cache[base_currency] = rates
                self._last_update = current_time
                
                return rates
                
        except httpx.HTTPError as e:
            raise DomainException(
                message=f"Error al obtener tasas de cambio: {str(e)}",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    def convert_amount(
        self, 
        amount: Decimal, 
        from_currency: str, 
        to_currency: str
    ) -> Decimal:
        """
        Convierte un monto de una moneda a otra usando tasas en tiempo real
        
        Args:
            amount: Cantidad a convertir
            from_currency: Símbolo de la moneda origen
            to_currency: Símbolo de la moneda destino
            
        Returns:
            Decimal: Monto convertido
        """
        if from_currency == to_currency:
            return amount

        try:
            # Obtener tasas actualizadas
            rates = self._get_latest_rates(from_currency)
            
            if to_currency not in rates:
                raise DomainException(
                    message=f"No se encontró tasa de conversión para {to_currency}",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
            return amount * rates[to_currency]
            
        except KeyError:
            raise DomainException(
                message=f"Moneda no soportada: {from_currency}",
                status_code=status.HTTP_400_BAD_REQUEST
            )

    def get_currency_symbol(self, currency_id: int) -> str:
        """Obtiene el símbolo de la moneda por su ID"""
        currency = self.repository.get_unit_of_measure_by_id(currency_id)
        if not currency:
            raise DomainException(
                message="Moneda no encontrada",
                status_code=status.HTTP_404_NOT_FOUND
            )
        return currency.abreviatura
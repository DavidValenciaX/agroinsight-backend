from decimal import Decimal
from typing import Dict
import requests
import os
from sqlalchemy.orm import Session
from app.measurement.infrastructure.sql_repository import MeasurementRepository
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status
from dotenv import load_dotenv
load_dotenv(override=True)

class CurrencyConversionService:
    """Servicio para manejar conversiones entre diferentes monedas"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = MeasurementRepository(db)
        self.api_key = os.getenv('EXCHANGE_RATE_API_KEY')
        self.base_url = "https://v6.exchangerate-api.com/v6"
        self._conversion_rates = {}
        self._base_currency = None

    def _fetch_conversion_rates(self, base_currency: str = 'USD') -> Dict[str, Decimal]:
        """
        Obtiene las tasas de conversión actualizadas desde la API
        
        Args:
            base_currency: Moneda base para las conversiones
            
        Returns:
            Dict[str, Decimal]: Diccionario con las tasas de conversión
        """
        try:
            url = f"{self.base_url}/{self.api_key}/latest/{base_currency}"
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            if data.get('result') == 'success':
                self._conversion_rates = {
                    currency: Decimal(str(rate))
                    for currency, rate in data['conversion_rates'].items()
                }
                self._base_currency = base_currency
                return self._conversion_rates
            else:
                raise DomainException(
                    message="Error al obtener tasas de conversión",
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE
                )
        except requests.exceptions.RequestException as e:
            raise DomainException(
                message="Error al conectar con el servicio de conversión de monedas",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
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

    def convert_amount(self, amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
        """
        Convierte un monto de una moneda a otra
        
        Args:
            amount: Cantidad a convertir
            from_currency: Símbolo de la moneda origen
            to_currency: Símbolo de la moneda destino
            
        Returns:
            Decimal: Monto convertido
        """
        if from_currency == to_currency:
            return amount

        # Si no tenemos tasas o la moneda base es diferente, actualizamos las tasas
        if not self._conversion_rates or self._base_currency != from_currency:
            self._fetch_conversion_rates(from_currency)

        if to_currency not in self._conversion_rates:
            raise DomainException(
                message=f"No se encontró tasa de conversión para {to_currency}",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return amount * self._conversion_rates[to_currency] 
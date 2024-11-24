from decimal import Decimal
from typing import Dict
from sqlalchemy.orm import Session
from app.measurement.infrastructure.sql_repository import MeasurementRepository
from app.infrastructure.common.common_exceptions import DomainException
from fastapi import status

class CurrencyConversionService:
    """Servicio para manejar conversiones entre diferentes monedas"""
    
    # Tasas de conversión temporales (usando COP como base)
    # Estos valores serán reemplazados posteriormente con datos de una API
    CONVERSION_RATES = {
        'COP': Decimal('1.0'),  # 1 COP = 1 COP (base)
        'USD': Decimal('0.00025'),  # 1 COP = 0.00025 USD
        'EUR': Decimal('0.00023'),  # 1 COP = 0.00023 EUR
        'MXN': Decimal('0.0043'),   # 1 COP = 0.0043 MXN
        'GBP': Decimal('0.0002'),   # 1 COP = 0.0002 GBP
    }

    def __init__(self, db: Session):
        self.db = db
        self.repository = MeasurementRepository(db)

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

        if from_currency not in self.CONVERSION_RATES or to_currency not in self.CONVERSION_RATES:
            raise DomainException(
                message=f"No se encontró tasa de conversión para {from_currency} a {to_currency}",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Convertir primero a COP (moneda base) y luego a la moneda destino
        amount_in_cop = amount / self.CONVERSION_RATES[from_currency]
        return amount_in_cop * self.CONVERSION_RATES[to_currency] 
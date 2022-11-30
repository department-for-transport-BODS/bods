from typing import Optional

from .elements import Element, Ref


class Operator(Element):
    @property
    def national_operator_code(self) -> Optional[str]:
        path = "NationalOperatorCode"
        return self.find_text(path)

    @property
    def operator_code(self) -> Optional[str]:
        path = "OperatorCode"
        return self.find_text(path)

    @property
    def operator_short_name(self) -> Optional[str]:
        path = "OperatorShortName"
        return self.find_text(path)

    @property
    def operator_name_on_licence(self) -> Optional[str]:
        path = "OperatorNameOnLicence"
        return self.find_text(path)

    @property
    def trading_name(self) -> Optional[str]:
        path = "TradingName"
        return self.find_text(path)

    @property
    def licence_number(self) -> Optional[str]:
        path = "LicenceNumber"
        return self.find_text(path)


class OperatorRef(Ref):
    path = "Operators/Operator"

    def resolve(self) -> Operator:
        return super()._resolve(Operator)

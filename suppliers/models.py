from dataclasses import dataclass, field


@dataclass
class PartResult:
    store: str
    brand: str
    price: float
    eta: str
    part_number: str = ""
    list_price: float = 0.0
    store_qty: int = 0
    total_qty: int = 0
    position: str = ""
    description: str = ""
    attributes: dict = field(default_factory=dict)
    fits_vehicle: bool = False
    image_url: str = ""


@dataclass
class SupplierSearchResult:
    store: str
    parts: list[PartResult] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return not self.error and bool(self.parts)

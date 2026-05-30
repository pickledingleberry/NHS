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
    position: str = ""          # Front / Rear / etc.
    description: str = ""       # Full part name
    attributes: dict = field(default_factory=dict)   # Pad Type, Hardware, etc.
    fits_vehicle: bool = False


@dataclass
class SupplierSearchResult:
    store: str
    parts: list[PartResult] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return not self.error and bool(self.parts)

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
    available: bool = True       # False = no real stock / call for estimate
    avail_score: int = 0         # 3=store, 2=hub/dm, 1=network, 0=none


@dataclass
class SupplierSearchResult:
    store: str
    parts: list[PartResult] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return not self.error and bool(self.parts)

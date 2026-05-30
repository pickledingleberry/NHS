from dataclasses import dataclass, field


@dataclass
class PartResult:
    store: str
    brand: str
    price: float
    eta: str
    part_number: str = ""


@dataclass
class SupplierSearchResult:
    store: str
    parts: list[PartResult] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return not self.error and bool(self.parts)

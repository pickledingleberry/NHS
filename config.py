import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

PLACEHOLDER = "username_here"


@dataclass
class SupplierCredentials:
    user: str
    password: str

    @property
    def configured(self) -> bool:
        return bool(
            self.user
            and self.password
            and self.user != PLACEHOLDER
            and self.password != "password_here"
        )


@dataclass
class AppConfig:
    autozone: SupplierCredentials
    fmp: SupplierCredentials
    oreilly: SupplierCredentials

    @property
    def any_configured(self) -> bool:
        return any(
            (
                self.autozone.configured,
                self.fmp.configured,
                self.oreilly.configured,
            )
        )

    def status_lines(self) -> list[str]:
        lines = []
        for label, creds in (
            ("AutoZone Pro", self.autozone),
            ("FMP Delivers", self.fmp),
            ("O'Reilly First Call", self.oreilly),
        ):
            state = "Ready" if creds.configured else "Not configured"
            lines.append(f"{label}: {state}")
        return lines


def get_config() -> AppConfig:
    return AppConfig(
        autozone=SupplierCredentials(
            user=os.getenv("AZ_USER", "").strip().strip('"'),
            password=os.getenv("AZ_PASS", "").strip().strip('"'),
        ),
        fmp=SupplierCredentials(
            user=os.getenv("FMP_USER", "").strip().strip('"'),
            password=os.getenv("FMP_PASS", "").strip().strip('"'),
        ),
        oreilly=SupplierCredentials(
            user=os.getenv("OR_USER", "").strip().strip('"'),
            password=os.getenv("OR_PASS", "").strip().strip('"'),
        ),
    )

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()

PLACEHOLDER = "username_here"


def _env(key: str) -> str:
    return os.getenv(key, "").strip().strip('"')


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
class AutoZoneConfig(SupplierCredentials):
    store_id: str = ""
    customer_id: str = ""


@dataclass
class OReillyCConfig(SupplierCredentials):
    shop_id: str = ""


@dataclass
class AppConfig:
    autozone: AutoZoneConfig
    fmp: SupplierCredentials
    oreilly: OReillyCConfig

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
            # ("FMP Delivers", self.fmp),
            ("O'Reilly First Call", self.oreilly),
        ):
            state = "Ready" if creds.configured else "Not configured"
            lines.append(f"{label}: {state}")
        return lines


def get_config() -> AppConfig:
    return AppConfig(
        autozone=AutoZoneConfig(
            user=_env("AZ_USER"),
            password=_env("AZ_PASS"),
            store_id=_env("AZ_STORE_ID"),
            customer_id=_env("AZ_CUSTOMER_ID"),
        ),
        fmp=SupplierCredentials(
            user=_env("FMP_USER"),
            password=_env("FMP_PASS"),
        ),
        oreilly=OReillyCConfig(
            user=_env("OR_USER"),
            password=_env("OR_PASS"),
            shop_id=_env("OR_SHOP_ID"),
        ),
    )

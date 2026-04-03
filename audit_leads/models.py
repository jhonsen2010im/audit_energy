from dataclasses import dataclass, field


@dataclass
class Contact:
    name: str
    title: str | None = None
    email: str | None = None
    phone: str | None = None
    is_primary: bool = False


@dataclass
class Lead:
    company_name: str
    address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    industry: str | None = None
    building_sqft: int | None = None
    building_year_built: int | None = None
    estimated_energy_spend: float | None = None
    source: str = "manual"
    contacts: list[Contact] = field(default_factory=list)

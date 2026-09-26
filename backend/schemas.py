import ipaddress, re
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

TYPES = {"A", "AAAA", "CNAME", "TXT", "MX", "NS", "PTR", "SRV", "CAA", "SOA"}

DOMAIN = re.compile(r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)(?:\.(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?))*\.?$", re.I)

def valid_dns_name(value: str) -> bool:
    return bool(DOMAIN.fullmatch(value.strip()))

class ZoneInput(BaseModel):
    name: str = Field(min_length=1, max_length=253)
    comment: str = Field(default="", max_length=500)
    is_private: bool = False
    @field_validator("name")
    @classmethod
    def valid_domain(cls, v):
        v = v.strip().rstrip(".").lower()
        if not valid_dns_name(v):
            raise ValueError("Enter a valid DNS domain name")
        return v

class ZoneOut(ZoneInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime | None = None

class RecordInput(BaseModel):
    name: str = Field(min_length=1, max_length=253)
    type: str
    value: str = Field(min_length=1, max_length=4096)
    ttl: int = Field(default=300, ge=1, le=2147483647)
    routing_policy: str = Field(default="Simple", max_length=40)
    @field_validator("type", mode="before")
    @classmethod
    def record_type(cls, v):
        v = str(v).strip().upper()
        if v not in TYPES: raise ValueError(f"Type must be one of {', '.join(sorted(TYPES))}")
        return v
    @field_validator("value")
    @classmethod
    def valid_value(cls, v, info):
        kind = info.data.get("type")
        lines = [line.strip() for line in v.splitlines() if line.strip()]
        if not lines:
            raise ValueError("At least one non-empty record value is required")
        if kind in {"CNAME", "SOA"} and len(lines) != 1:
            raise ValueError(f"{kind} records accept exactly one value")
        try:
            for line in lines:
                fields = line.split()
                if kind == "A":
                    ipaddress.IPv4Address(line)
                elif kind == "AAAA":
                    ipaddress.IPv6Address(line)
                elif kind in {"CNAME", "NS", "PTR"}:
                    if not valid_dns_name(line): raise ValueError("Enter a valid DNS hostname")
                elif kind == "MX":
                    if len(fields) != 2 or not fields[0].isdigit() or not 0 <= int(fields[0]) <= 65535 or not valid_dns_name(fields[1]): raise ValueError("Use: priority mail.example.com (priority 0–65535)")
                elif kind == "SRV":
                    if len(fields) != 4 or not all(f.isdigit() for f in fields[:3]) or not (0 <= int(fields[0]) <= 65535 and 0 <= int(fields[1]) <= 65535 and 0 <= int(fields[2]) <= 65535) or not valid_dns_name(fields[3]): raise ValueError("Use: priority weight port target (numeric fields 0–65535)")
                elif kind == "CAA":
                    if len(fields) < 3 or not fields[0].isdigit() or not 0 <= int(fields[0]) <= 255 or not re.fullmatch(r"[A-Za-z0-9-]{1,15}", fields[1]): raise ValueError("Use: flags tag value (flags 0–255)")
                elif kind == "SOA":
                    if len(fields) != 7 or not valid_dns_name(fields[0]) or not valid_dns_name(fields[1]) or not all(f.isdigit() and 0 <= int(f) <= 4294967295 for f in fields[2:]): raise ValueError("Use: mname rname serial refresh retry expire minimum")
                elif kind == "TXT":
                    if any(ord(char) < 32 and char not in "\t" for char in line): raise ValueError("TXT values cannot include control characters")
        except (ValueError, ipaddress.AddressValueError) as exc:
            raise ValueError(str(exc)) from exc
        return "\n".join(lines)

    @field_validator("name")
    @classmethod
    def valid_record_name(cls, value):
        value = value.strip().rstrip(".")
        labels = value.split(".")
        if value != "@" and any(not re.fullmatch(r"[A-Za-z0-9_*_-]{1,63}", label) for label in labels):
            raise ValueError("Enter a valid DNS record name (underscores are allowed for service labels)")
        return value

class RecordOut(RecordInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    zone_id: int
    created_at: datetime | None = None

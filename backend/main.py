import os
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_, select, func
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from models import HostedZone, DNSRecord
from schemas import ZoneInput, ZoneOut, RecordInput, RecordOut, TYPES

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Route 53 Console API", version="1.0.0", description="Hosted zone and DNS record management API")
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in origins], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health(): return {"status": "ok"}

@app.get("/api/summary")
def summary(db: Session = Depends(get_db)):
    return {"hosted_zones": db.scalar(select(func.count()).select_from(HostedZone)) or 0,
            "dns_records": db.scalar(select(func.count()).select_from(DNSRecord)) or 0}

@app.get("/api/zones")
def list_zones(search: str = "", page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    q = select(HostedZone)
    if search: q = q.where(or_(HostedZone.name.ilike(f"%{search}%"), HostedZone.comment.ilike(f"%{search}%")))
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = db.scalars(q.order_by(HostedZone.id.desc()).offset((page-1)*page_size).limit(page_size)).all()
    return {"items": [{**ZoneOut.model_validate(x).model_dump(mode="json"), "record_count": len(x.records)} for x in rows], "total": total, "page": page, "page_size": page_size}

@app.post("/api/zones", response_model=ZoneOut, status_code=201)
def create_zone(data: ZoneInput, db: Session = Depends(get_db)):
    if db.scalar(select(HostedZone).where(HostedZone.name == data.name)): raise HTTPException(409, "A hosted zone with this domain already exists")
    item = HostedZone(**data.model_dump()); db.add(item); db.flush()
    if not item.is_private:
        origin = f"{item.name}."
        nameservers = [f"ns-{1000 + item.id}.awsdns-00.com.", f"ns-{2000 + item.id}.awsdns-00.net.", f"ns-{3000 + item.id}.awsdns-00.org.", f"ns-{4000 + item.id}.awsdns-00.co.uk."]
        serial = datetime.now(timezone.utc).strftime("%Y%m%d01")
        db.add_all([
            DNSRecord(zone_id=item.id, name=origin, type="NS", value="\n".join(nameservers), ttl=172800),
            DNSRecord(zone_id=item.id, name=origin, type="SOA", value=f"{nameservers[0]} hostmaster.{origin} {serial} 7200 900 1209600 86400", ttl=900),
        ])
    db.commit(); db.refresh(item); return item

@app.get("/api/zones/{zone_id}", response_model=ZoneOut)
def get_zone(zone_id: int, db: Session = Depends(get_db)):
    item = db.get(HostedZone, zone_id)
    if not item: raise HTTPException(404, "Hosted zone not found")
    return item

@app.patch("/api/zones/{zone_id}", response_model=ZoneOut)
def update_zone(zone_id: int, data: ZoneInput, db: Session = Depends(get_db)):
    item = db.get(HostedZone, zone_id)
    if not item: raise HTTPException(404, "Hosted zone not found")
    duplicate = db.scalar(select(HostedZone).where(HostedZone.name == data.name, HostedZone.id != zone_id))
    if duplicate: raise HTTPException(409, "A hosted zone with this domain already exists")
    for k,v in data.model_dump().items(): setattr(item,k,v)
    db.commit(); db.refresh(item); return item

@app.delete("/api/zones/{zone_id}", status_code=204)
def delete_zone(zone_id: int, db: Session = Depends(get_db)):
    item = db.get(HostedZone, zone_id)
    if not item: raise HTTPException(404, "Hosted zone not found")
    db.delete(item); db.commit(); return Response(status_code=204)

@app.post("/api/zones/bulk-delete")
def bulk_delete_zones(payload: dict, db: Session = Depends(get_db)):
    ids = payload.get("ids") or []
    if not isinstance(ids, list) or not ids:
        raise HTTPException(422, "Provide a non-empty list of hosted zone ids to delete")
    rows = db.scalars(select(HostedZone).where(HostedZone.id.in_(ids))).all()
    found_ids = {row.id for row in rows}
    for row in rows: db.delete(row)
    db.commit()
    return {"deleted": len(rows), "not_found": [i for i in ids if i not in found_ids]}

def require_zone(zone_id: int, db: Session):
    zone = db.get(HostedZone, zone_id)
    if not zone: raise HTTPException(404, "Hosted zone not found")
    return zone

def validate_record_compatibility(zone: HostedZone, data: RecordInput, db: Session, record_id: int | None = None):
    owner = data.name.rstrip(".").lower()
    apex = zone.name.lower()
    if owner == "@": owner = apex
    if data.type == "SOA" and owner != apex:
        raise HTTPException(422, "SOA records must be created at the hosted zone apex")
    existing = db.scalars(select(DNSRecord).where(DNSRecord.zone_id == zone.id, DNSRecord.id != (record_id or 0))).all()
    same_name = [record for record in existing if record.name.rstrip(".").lower() == owner]
    if data.type == "CNAME" and same_name:
        raise HTTPException(409, "A CNAME record cannot coexist with other records at the same name")
    if any(record.type == "CNAME" for record in same_name):
        raise HTTPException(409, "This name already has a CNAME record; CNAME cannot coexist with other records")
    if data.type == "SOA" and any(record.type == "SOA" for record in same_name):
        raise HTTPException(409, "A hosted zone can have only one SOA record")

@app.get("/api/zones/{zone_id}/records")
def list_records(zone_id: int, search: str = "", record_type: str = "", page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    require_zone(zone_id, db); q = select(DNSRecord).where(DNSRecord.zone_id == zone_id)
    if search: q = q.where(or_(DNSRecord.name.ilike(f"%{search}%"), DNSRecord.value.ilike(f"%{search}%")))
    if record_type: q = q.where(DNSRecord.type == record_type.upper())
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = db.scalars(q.order_by(DNSRecord.name, DNSRecord.type).offset((page-1)*page_size).limit(page_size)).all()
    return {"items": [RecordOut.model_validate(x).model_dump(mode="json") for x in rows], "total": total, "page": page, "page_size": page_size}

@app.post("/api/zones/{zone_id}/records", response_model=RecordOut, status_code=201)
def create_record(zone_id: int, data: RecordInput, db: Session = Depends(get_db)):
    zone = require_zone(zone_id, db); validate_record_compatibility(zone, data, db); item = DNSRecord(zone_id=zone_id, **data.model_dump()); db.add(item); db.commit(); db.refresh(item); return item

@app.patch("/api/records/{record_id}", response_model=RecordOut)
def update_record(record_id: int, data: RecordInput, db: Session = Depends(get_db)):
    item = db.get(DNSRecord, record_id)
    if not item: raise HTTPException(404, "DNS record not found")
    validate_record_compatibility(item.zone, data, db, record_id)
    for k,v in data.model_dump().items(): setattr(item,k,v)
    db.commit(); db.refresh(item); return item

@app.delete("/api/records/{record_id}", status_code=204)
def delete_record(record_id: int, db: Session = Depends(get_db)):
    item = db.get(DNSRecord, record_id)
    if not item: raise HTTPException(404, "DNS record not found")
    db.delete(item); db.commit(); return Response(status_code=204)

@app.post("/api/records/bulk-delete")
def bulk_delete_records(payload: dict, db: Session = Depends(get_db)):
    ids = payload.get("ids") or []
    if not isinstance(ids, list) or not ids:
        raise HTTPException(422, "Provide a non-empty list of record ids to delete")
    rows = db.scalars(select(DNSRecord).where(DNSRecord.id.in_(ids))).all()
    found_ids = {row.id for row in rows}
    for row in rows: db.delete(row)
    db.commit()
    return {"deleted": len(rows), "not_found": [i for i in ids if i not in found_ids]}

@app.post("/api/zones/{zone_id}/import")
def import_zone(zone_id: int, payload: dict, db: Session = Depends(get_db)):
    zone = require_zone(zone_id, db)
    text = payload.get("content", "")
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(422, "Provide BIND zone file content to import")
    origin = f"{zone.name}."
    ttl_default = 300
    last_name = origin
    imported, skipped = 0, []
    for raw_line in text.splitlines():
        line = raw_line.split(";", 1)[0].strip()
        if not line:
            continue
        if line.upper().startswith("$ORIGIN"):
            origin = line.split(None, 1)[1].strip()
            continue
        if line.upper().startswith("$TTL"):
            try: ttl_default = int(line.split(None, 1)[1].strip())
            except (IndexError, ValueError): pass
            continue
        parts = line.split()
        if len(parts) < 3:
            skipped.append(raw_line); continue
        # optional leading name (blank means "same as previous")
        idx = 0
        if parts[0].isdigit() or parts[0].upper() == "IN":
            name = last_name
        else:
            name = parts[0]; idx = 1
        rest = parts[idx:]
        ttl = ttl_default
        if rest and rest[0].isdigit():
            ttl = int(rest[0]); rest = rest[1:]
        if rest and rest[0].upper() == "IN":
            rest = rest[1:]
        if not rest or rest[0].upper() not in TYPES:
            skipped.append(raw_line); continue
        rtype = rest[0].upper()
        value = " ".join(rest[1:]).strip()
        if not value:
            skipped.append(raw_line); continue
        last_name = name
        try:
            data = RecordInput(name=name, type=rtype, value=value, ttl=ttl)
            validate_record_compatibility(zone, data, db)
            db.add(DNSRecord(zone_id=zone.id, **data.model_dump()))
            db.flush()
            imported += 1
        except (HTTPException, ValueError):
            skipped.append(raw_line)
    db.commit()
    return {"imported": imported, "skipped": skipped}

@app.get("/api/zones/{zone_id}/export")
def export_zone(zone_id: int, format: str = "json", db: Session = Depends(get_db)):
    zone = require_zone(zone_id, db)
    records = db.scalars(select(DNSRecord).where(DNSRecord.zone_id == zone_id).order_by(DNSRecord.name)).all()
    if format.lower() == "bind":
        body = f"$ORIGIN {zone.name}.\n$TTL 300\n" + "".join(f"{r.name} {r.ttl} IN {r.type} {value}\n" for r in records for value in r.value.splitlines() if value.strip())
        return Response(body, media_type="text/dns", headers={"Content-Disposition": f'attachment; filename="{zone.name}.zone"'})
    return {"zone": ZoneOut.model_validate(zone).model_dump(mode="json"), "records": [RecordOut.model_validate(r).model_dump(mode="json") for r in records]}

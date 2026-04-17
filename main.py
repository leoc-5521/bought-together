import io
import os
import csv
import pickle
from collections import defaultdict
from typing import Optional
from datetime import datetime, date

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Persistent storage ───────────────────────────────────────────
DATA_FILE = "/tmp/orders_data.pkl"

def save_to_disk(om, s):
    try:
        with open(DATA_FILE, "wb") as f:
            pickle.dump({"orders_map": om, "stats": s}, f)
    except Exception as e:
        print(f"Warning: could not save data to disk: {e}")

def load_from_disk():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "rb") as f:
                data = pickle.load(f)
                return data["orders_map"], data["stats"]
    except Exception as e:
        print(f"Warning: could not load data from disk: {e}")
    return {}, {}

# ── In-memory store ──────────────────────────────────────────────
orders_map, stats = load_from_disk()

FIELD_SYNONYMS = {
    "order_id":    ["order id","name","order name","order_id","order number","order_no"],
    "product_name":["lineitem name","line item name","product title","lineitem_name","product name","title"],
    "sku":         ["lineitem sku","sku","variant sku","lineitem_sku","variant_sku"],
    "product_id":  ["product id","product_id"],
    "product_type":["product type","product_type","type","vendor"],
    "created_at":  ["created at","created_at","order date","date","processed at","processed_at"],
}

DATE_FORMATS = [
    "%Y-%m-%d %H:%M:%S %z",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y",
]

def parse_date(val: str) -> Optional[date]:
    if not val:
        return None
    val = val.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(val[:25], fmt).date()
        except ValueError:
            continue
    try:
        return datetime.strptime(val[:10], "%Y-%m-%d").date()
    except ValueError:
        return None

def detect_columns(headers: list[str]) -> dict[str, int]:
    col_map = {}
    normalised = [h.lower().strip().replace('"','') for h in headers]
    for field, synonyms in FIELD_SYNONYMS.items():
        for i, h in enumerate(normalised):
            if any(h == s or h.startswith(s) for s in synonyms):
                if field not in col_map:
                    col_map[field] = i
    return col_map

def parse_csv_bytes(content: bytes) -> tuple[list[str], list[list[str]]]:
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        raise ValueError("File is empty")
    return rows[0], rows[1:]

# ── Upload endpoints ─────────────────────────────────────────────
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    global orders_map, stats
    content = await file.read()
    headers, rows = parse_csv_bytes(content)
    col_map = detect_columns(headers)

    if "order_id" not in col_map or "product_name" not in col_map:
        return {
            "status": "needs_mapping",
            "headers": headers,
            "col_map": col_map,
            "row_count": len(rows),
        }

    orders_map, stats = build_orders_map(rows, col_map)
    save_to_disk(orders_map, stats)
    return {"status": "ok", **stats}

class MappingRequest(BaseModel):
    headers: list[str]
    rows_sample: list[list[str]]
    col_map: dict[str, int]

@app.post("/upload-with-mapping")
async def upload_with_mapping(
    file: UploadFile = File(...),
    order_id_col: int = Query(...),
    product_name_col: int = Query(...),
    sku_col: int = Query(-1),
    product_id_col: int = Query(-1),
    product_type_col: int = Query(-1),
    date_col: int = Query(-1),
):
    global orders_map, stats
    content = await file.read()
    _, rows = parse_csv_bytes(content)
    col_map = {
        "order_id": order_id_col,
        "product_name": product_name_col,
    }
    if sku_col >= 0:          col_map["sku"] = sku_col
    if product_id_col >= 0:   col_map["product_id"] = product_id_col
    if product_type_col >= 0: col_map["product_type"] = product_type_col
    if date_col >= 0:         col_map["created_at"] = date_col

    orders_map, stats = build_orders_map(rows, col_map)
    save_to_disk(orders_map, stats)
    return {"status": "ok", **stats}

def build_orders_map(rows, col_map):
    om: dict[str, dict] = defaultdict(lambda: {"products": [], "date": None})

    def get(row, field):
        idx = col_map.get(field)
        if idx is None or idx >= len(row):
            return ""
        return str(row[idx]).strip()

    for row in rows:
        order_id = get(row, "order_id")
        name     = get(row, "product_name")
        if not order_id or not name:
            continue

        sku      = get(row, "sku")
        pid      = get(row, "product_id")
        ptype    = get(row, "product_type")
        raw_date = get(row, "created_at")

        if om[order_id]["date"] is None and raw_date:
            om[order_id]["date"] = parse_date(raw_date)

        key = f"{name}|{sku}"
        if not any(p["_key"] == key for p in om[order_id]["products"]):
            om[order_id]["products"].append({
                "name": name, "sku": sku, "id": pid, "type": ptype, "_key": key
            })

    om = dict(om)

    all_names = set()
    all_skus  = set()
    all_types = set()
    all_dates = []

    for order in om.values():
        for p in order["products"]:
            if p["name"]:  all_names.add(p["name"])
            if p["sku"]:   all_skus.add(p["sku"])
            if p["type"]:  all_types.add(p["type"])
        if order["date"]:
            all_dates.append(order["date"])

    s = {
        "order_count":   len(om),
        "product_count": len(all_names),
        "sku_count":     len(all_skus),
        "type_count":    len(all_types),
        "types":         sorted(all_types),
        "names":         sorted(all_names),
        "min_date":      str(min(all_dates)) if all_dates else None,
        "max_date":      str(max(all_dates)) if all_dates else None,
        "has_dates":     bool(all_dates),
    }
    return om, s

# ── Stats endpoint ───────────────────────────────────────────────
@app.get("/stats")
def get_stats():
    if not orders_map:
        raise HTTPException(status_code=404, detail="No data loaded")
    return stats

# ── Search endpoint ──────────────────────────────────────────────
@app.get("/search")
def search(
    name:      Optional[str] = Query(None),
    sku:       Optional[str] = Query(None),
    pid:       Optional[str] = Query(None),
    type:      Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to:   Optional[str] = Query(None),
    limit:     int           = Query(50),
):
    if not orders_map:
        raise HTTPException(status_code=404, detail="No data loaded. Please upload a file first.")

    nl = (name or "").lower()
    sl = (sku  or "").lower()
    il = (pid  or "").lower()
    tl = (type or "").lower()

    if not any([nl, sl, il, tl]):
        raise HTTPException(status_code=400, detail="Provide at least one search term")

    df = parse_date(date_from) if date_from else None
    dt = parse_date(date_to)   if date_to   else None

    def is_match(p):
        return (
            (nl and nl in p["name"].lower()) or
            (sl and sl in p["sku"].lower())  or
            (il and il in p["id"].lower())   or
            (tl and tl in p["type"].lower())
        )

    def in_date_range(order):
        if not df and not dt:
            return True
        od = order.get("date")
        if od is None:
            return True
        if df and od < df:
            return False
        if dt and od > dt:
            return False
        return True

    matching_orders = []
    for order_id, order in orders_map.items():
        if not in_date_range(order):
            continue
        if any(is_match(p) for p in order["products"]):
            matching_orders.append(order["products"])

    if not matching_orders:
        return {"match_count": 0, "results": []}

    co_count: dict[str, int] = defaultdict(int)
    co_data:  dict[str, dict] = {}

    for products in matching_orders:
        others = [p for p in products if not is_match(p)]
        for p in others:
            key = p["_key"]
            co_count[key] += 1
            if key not in co_data:
                co_data[key] = {k: v for k, v in p.items() if k != "_key"}

    total = len(matching_orders)
    results = sorted(
        [
            {**co_data[k], "count": c, "pct": round(c / total * 100, 1)}
            for k, c in co_count.items()
        ],
        key=lambda x: (-x["pct"], -x["count"])
    )[:limit]

    return {"match_count": total, "results": results}

# ── Serve frontend ───────────────────────────────────────────────
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {"message": "Bought Together API running."}

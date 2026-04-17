import io
import os
import csv
import pickle
import gc
from collections import defaultdict
from typing import Optional
from datetime import datetime, date
from itertools import combinations

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
            pickle.dump({"orders_map": om, "stats": s}, f, protocol=4)
    except Exception as e:
        print(f"Warning: could not save to disk: {e}")

def load_from_disk():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "rb") as f:
                data = pickle.load(f)
                return data["orders_map"], data["stats"]
    except Exception as e:
        print(f"Warning: could not load from disk: {e}")
    return {}, {}

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
    "%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S%z",  "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d", "%d/%m/%Y %H:%M", "%d/%m/%Y",
    "%m/%d/%Y %H:%M", "%m/%d/%Y",
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

def detect_columns(headers):
    col_map = {}
    normalised = [h.lower().strip().replace('"','') for h in headers]
    for field, synonyms in FIELD_SYNONYMS.items():
        for i, h in enumerate(normalised):
            if any(h == s or h.startswith(s) for s in synonyms):
                if field not in col_map:
                    col_map[field] = i
    return col_map

def parse_csv_bytes(content: bytes):
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        raise ValueError("File is empty")
    return rows[0], rows[1:]

def in_date_range(order, df, dt):
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

# ── Upload endpoints ─────────────────────────────────────────────
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    global orders_map, stats
    content = await file.read()
    headers, rows = parse_csv_bytes(content)
    del content  # free memory immediately
    col_map = detect_columns(headers)
    if "order_id" not in col_map or "product_name" not in col_map:
        return {"status": "needs_mapping", "headers": headers, "col_map": col_map, "row_count": len(rows)}
    orders_map, stats = build_orders_map(rows, col_map)
    del rows
    gc.collect()
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
    del content
    col_map = {"order_id": order_id_col, "product_name": product_name_col}
    if sku_col >= 0:          col_map["sku"] = sku_col
    if product_id_col >= 0:   col_map["product_id"] = product_id_col
    if product_type_col >= 0: col_map["product_type"] = product_type_col
    if date_col >= 0:         col_map["created_at"] = date_col
    orders_map, stats = build_orders_map(rows, col_map)
    del rows
    gc.collect()
    save_to_disk(orders_map, stats)
    return {"status": "ok", **stats}

def build_orders_map(rows, col_map):
    # Use __slots__-style plain tuples to reduce memory vs dicts
    om = defaultdict(lambda: {"products": [], "date": None})

    def get(row, field):
        idx = col_map.get(field)
        if idx is None or idx >= len(row):
            return ""
        v = row[idx]
        return str(v).strip() if v is not None else ""

    for row in rows:
        order_id = get(row, "order_id")
        name     = get(row, "product_name")
        if not order_id or not name:
            continue
        sku = get(row, "sku"); pid = get(row, "product_id")
        ptype = get(row, "product_type"); raw_date = get(row, "created_at")
        if om[order_id]["date"] is None and raw_date:
            om[order_id]["date"] = parse_date(raw_date)
        key = f"{name}|{sku}"
        existing_keys = {p["_key"] for p in om[order_id]["products"]}
        if key not in existing_keys:
            # Only store what we need — drop empty strings to save memory
            p = {"_key": key, "name": name}
            if sku:   p["sku"]  = sku
            if pid:   p["id"]   = pid
            if ptype: p["type"] = ptype
            om[order_id]["products"].append(p)

    om = dict(om)

    all_names = set(); all_skus = set(); all_types = set(); all_dates = []
    for order in om.values():
        for p in order["products"]:
            all_names.add(p["name"])
            if p.get("sku"):  all_skus.add(p["sku"])
            if p.get("type"): all_types.add(p["type"])
        if order["date"]: all_dates.append(order["date"])

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

def get_p(p, field):
    """Safe field getter for product dicts (some fields may be missing if empty)."""
    return p.get(field, "")

# ── Stats endpoint ───────────────────────────────────────────────
@app.get("/stats")
def get_stats():
    if not orders_map:
        raise HTTPException(status_code=404, detail="No data loaded")
    return stats

# ── Dashboard endpoint ───────────────────────────────────────────
@app.get("/dashboard")
def dashboard(
    date_from: Optional[str] = Query(None),
    date_to:   Optional[str] = Query(None),
    limit:     int           = Query(25),
):
    if not orders_map:
        raise HTTPException(status_code=404, detail="No data loaded. Please upload a file first.")

    df = parse_date(date_from) if date_from else None
    dt = parse_date(date_to)   if date_to   else None

    filtered_orders = [o for o in orders_map.values() if in_date_range(o, df, dt)]
    total_orders = len(filtered_orders)
    if total_orders == 0:
        return {"total_orders": 0, "top_products": [], "top_pairs": []}

    # ── Top products
    product_total: dict[str, int] = defaultdict(int)
    product_multi: dict[str, int] = defaultdict(int)
    product_data:  dict[str, dict] = {}

    for order in filtered_orders:
        prods = order["products"]
        multi = len(prods) > 1
        for p in prods:
            k = p["_key"]
            product_total[k] += 1
            if multi: product_multi[k] += 1
            if k not in product_data:
                product_data[k] = {"name": p["name"], "sku": get_p(p,"sku"), "id": get_p(p,"id"), "type": get_p(p,"type")}

    top_products = sorted(
        [{"name": product_data[k]["name"], "sku": product_data[k]["sku"],
          "id": product_data[k]["id"], "type": product_data[k]["type"],
          "total_orders": product_total[k], "copurchase_orders": product_multi[k],
          "copurchase_pct": round(product_multi[k] / product_total[k] * 100, 1) if product_total[k] else 0}
         for k in product_data],
        key=lambda x: (-x["copurchase_pct"], -x["copurchase_orders"])
    )[:limit]

    # ── Top pairs
    pair_count: dict[tuple, int] = defaultdict(int)
    pair_data:  dict[tuple, dict] = {}

    for order in filtered_orders:
        prods = order["products"]
        if len(prods) < 2:
            continue
        keys = sorted({p["_key"] for p in prods})
        prod_lookup = {p["_key"]: p for p in prods}
        for ka, kb in combinations(keys, 2):
            pair = (ka, kb)
            pair_count[pair] += 1
            if pair not in pair_data:
                pa, pb = prod_lookup[ka], prod_lookup[kb]
                pair_data[pair] = {
                    "product_a": {"name": pa["name"], "sku": get_p(pa,"sku"), "id": get_p(pa,"id"), "type": get_p(pa,"type")},
                    "product_b": {"name": pb["name"], "sku": get_p(pb,"sku"), "id": get_p(pb,"id"), "type": get_p(pb,"type")},
                }

    top_pairs = sorted(
        [{"product_a": pair_data[p]["product_a"], "product_b": pair_data[p]["product_b"],
          "count": c, "pct": round(c / total_orders * 100, 1)}
         for p, c in pair_count.items()],
        key=lambda x: (-x["pct"], -x["count"])
    )[:limit]

    return {"total_orders": total_orders, "top_products": top_products, "top_pairs": top_pairs}

# ── Trios endpoint (separate, on-demand) ─────────────────────────
@app.get("/trios")
def trios(
    date_from: Optional[str] = Query(None),
    date_to:   Optional[str] = Query(None),
):
    if not orders_map:
        raise HTTPException(status_code=404, detail="No data loaded. Please upload a file first.")

    df = parse_date(date_from) if date_from else None
    dt = parse_date(date_to)   if date_to   else None

    filtered_orders = [o for o in orders_map.values() if in_date_range(o, df, dt)]
    total_orders = len(filtered_orders)
    if total_orders == 0:
        return {"total_orders": 0, "top_trios": []}

    trio_count: dict[tuple, int] = defaultdict(int)
    trio_data:  dict[tuple, dict] = {}

    for order in filtered_orders:
        prods = order["products"]
        if len(prods) < 3:
            continue
        keys = sorted({p["_key"] for p in prods})
        prod_lookup = {p["_key"]: p for p in prods}
        for ka, kb, kc in combinations(keys, 3):
            trio = (ka, kb, kc)
            trio_count[trio] += 1
            if trio not in trio_data:
                pa, pb, pc = prod_lookup[ka], prod_lookup[kb], prod_lookup[kc]
                trio_data[trio] = {
                    "product_a": {"name": pa["name"], "sku": get_p(pa,"sku"), "id": get_p(pa,"id"), "type": get_p(pa,"type")},
                    "product_b": {"name": pb["name"], "sku": get_p(pb,"sku"), "id": get_p(pb,"id"), "type": get_p(pb,"type")},
                    "product_c": {"name": pc["name"], "sku": get_p(pc,"sku"), "id": get_p(pc,"id"), "type": get_p(pc,"type")},
                }

    top_trios = sorted(
        [{"product_a": trio_data[t]["product_a"], "product_b": trio_data[t]["product_b"],
          "product_c": trio_data[t]["product_c"], "count": c, "pct": round(c / total_orders * 100, 1)}
         for t, c in trio_count.items()],
        key=lambda x: (-x["pct"], -x["count"])
    )[:50]

    # Free memory
    del trio_count, trio_data, filtered_orders
    gc.collect()

    return {"total_orders": total_orders, "top_trios": top_trios}

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

    nl = (name or "").lower(); sl = (sku  or "").lower()
    il = (pid  or "").lower(); tl = (type or "").lower()
    if not any([nl, sl, il, tl]):
        raise HTTPException(status_code=400, detail="Provide at least one search term")

    df = parse_date(date_from) if date_from else None
    dt = parse_date(date_to)   if date_to   else None

    def is_match(p):
        return ((nl and nl in p["name"].lower()) or
                (sl and sl in get_p(p,"sku").lower()) or
                (il and il in get_p(p,"id").lower())  or
                (tl and tl in get_p(p,"type").lower()))

    matching_orders = [
        order["products"] for order in orders_map.values()
        if in_date_range(order, df, dt) and any(is_match(p) for p in order["products"])
    ]

    if not matching_orders:
        return {"match_count": 0, "results": []}

    co_count: dict[str, int] = defaultdict(int)
    co_data:  dict[str, dict] = {}

    for products in matching_orders:
        for p in [p for p in products if not is_match(p)]:
            key = p["_key"]
            co_count[key] += 1
            if key not in co_data:
                co_data[key] = {"name": p["name"], "sku": get_p(p,"sku"), "id": get_p(p,"id"), "type": get_p(p,"type")}

    total = len(matching_orders)
    results = sorted(
        [{"name": co_data[k]["name"], "sku": co_data[k]["sku"], "id": co_data[k]["id"],
          "type": co_data[k]["type"], "count": c, "pct": round(c / total * 100, 1)}
         for k, c in co_count.items()],
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

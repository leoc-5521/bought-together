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

def save_to_disk(om, s, pr=None):
    try:
        with open(DATA_FILE, "wb") as f:
            pickle.dump({"orders_map": om, "stats": s, "product_revenue": pr or {}}, f, protocol=4)
    except Exception as e:
        print(f"Warning: could not save to disk: {e}")

def load_from_disk():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "rb") as f:
                data = pickle.load(f)
                return data["orders_map"], data["stats"], data.get("product_revenue", {})
    except Exception as e:
        print(f"Warning: could not load from disk: {e}")
    return {}, {}, {}

orders_map, stats, product_revenue = load_from_disk()

FIELD_SYNONYMS = {
    "order_id":    ["order id","name","order name","order_id","order number","order_no"],
    "product_name":["lineitem name","line item name","product title","lineitem_name","product name","title"],
    "sku":         ["lineitem sku","sku","variant sku","lineitem_sku","variant_sku"],
    "product_id":  ["product id","product_id"],
    "product_type":["product type","product_type","type","vendor"],
    "created_at":  ["created at","created_at","order date","date","processed at","processed_at"],
    "price":       ["lineitem price","line item price","price","item price","unit price","lineitem_price"],
    "quantity":    ["lineitem quantity","line item quantity","quantity","qty","lineitem_quantity"],
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
    global orders_map, stats, product_revenue
    content = await file.read()
    headers, rows = parse_csv_bytes(content)
    del content  # free memory immediately
    col_map = detect_columns(headers)
    if "order_id" not in col_map or "product_name" not in col_map:
        return {"status": "needs_mapping", "headers": headers, "col_map": col_map, "row_count": len(rows)}
    orders_map, stats, product_revenue = build_orders_map(rows, col_map)
    del rows
    gc.collect()
    save_to_disk(orders_map, stats, product_revenue)
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
    price_col: int = Query(-1),
    quantity_col: int = Query(-1),
):
    global orders_map, stats, product_revenue
    content = await file.read()
    _, rows = parse_csv_bytes(content)
    del content
    col_map = {"order_id": order_id_col, "product_name": product_name_col}
    if sku_col >= 0:          col_map["sku"] = sku_col
    if product_id_col >= 0:   col_map["product_id"] = product_id_col
    if product_type_col >= 0: col_map["product_type"] = product_type_col
    if date_col >= 0:         col_map["created_at"] = date_col
    if price_col >= 0:        col_map["price"] = price_col
    if quantity_col >= 0:     col_map["quantity"] = quantity_col
    orders_map, stats, product_revenue = build_orders_map(rows, col_map)
    del rows
    gc.collect()
    save_to_disk(orders_map, stats, product_revenue)
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
        raw_price = get(row, "price"); raw_qty = get(row, "quantity")
        if om[order_id]["date"] is None and raw_date:
            om[order_id]["date"] = parse_date(raw_date)
        try:
            line_price = float(str(raw_price).replace(",","").strip()) if raw_price else 0.0
        except (ValueError, TypeError):
            line_price = 0.0
        try:
            line_qty = float(str(raw_qty).replace(",","").strip()) if raw_qty else 1.0
            if line_qty <= 0: line_qty = 1.0
        except (ValueError, TypeError):
            line_qty = 1.0
        line_revenue = line_price * line_qty
        key = f"{name}|{sku}"
        existing_keys = {p["_key"] for p in om[order_id]["products"]}
        if key not in existing_keys:
            # Only store what we need — drop empty strings to save memory
            p = {"_key": key, "name": name}
            if sku:   p["sku"]  = sku
            if pid:   p["id"]   = pid
            if ptype: p["type"] = ptype
            p["line_revenue"] = line_revenue
            om[order_id]["products"].append(p)
        else:
            # Accumulate revenue for same product appearing multiple times (different variants)
            for existing in om[order_id]["products"]:
                if existing["_key"] == key:
                    existing["line_revenue"] = existing.get("line_revenue", 0.0) + line_revenue
                    break

    om = dict(om)

    all_names = set(); all_skus = set(); all_types = set(); all_dates = []
    for order in om.values():
        for p in order["products"]:
            all_names.add(p["name"])
            if p.get("sku"):  all_skus.add(p["sku"])
            if p.get("type"): all_types.add(p["type"])
        if order["date"]: all_dates.append(order["date"])

    # Build global product revenue lookup: key -> total revenue across all orders
    product_revenue: dict[str, float] = defaultdict(float)
    for order in om.values():
        for p in order["products"]:
            product_revenue[p["_key"]] += p.get("line_revenue", 0.0)
    has_price_data = any(v > 0 for v in product_revenue.values())

    s = {
        "order_count":    len(om),
        "product_count":  len(all_names),
        "sku_count":      len(all_skus),
        "type_count":     len(all_types),
        "types":          sorted(all_types),
        "names":          sorted(all_names),
        "min_date":       str(min(all_dates)) if all_dates else None,
        "max_date":       str(max(all_dates)) if all_dates else None,
        "has_dates":      bool(all_dates),
        "has_price_data": has_price_data,
    }
    return om, s, dict(product_revenue)

def get_p(p, field):
    """Safe field getter for product dicts (some fields may be missing if empty)."""
    return p.get(field, "")

# ── Stats endpoint ───────────────────────────────────────────────
@app.get("/stats")
def get_stats():
    if not orders_map:
        raise HTTPException(status_code=404, detail="No data loaded")
    return stats

# ── Dashboard endpoint (just returns order count for the date range) ─
@app.get("/dashboard")
def dashboard(
    date_from: Optional[str] = Query(None),
    date_to:   Optional[str] = Query(None),
):
    if not orders_map:
        raise HTTPException(status_code=404, detail="No data loaded. Please upload a file first.")
    df = parse_date(date_from) if date_from else None
    dt = parse_date(date_to)   if date_to   else None
    total_orders = sum(1 for o in orders_map.values() if in_date_range(o, df, dt))
    return {"total_orders": total_orders}

# ── Pairs endpoint (on-demand) ───────────────────────────────────
@app.get("/pairs")
def pairs(
    date_from: Optional[str] = Query(None),
    date_to:   Optional[str] = Query(None),
):
    if not orders_map:
        raise HTTPException(status_code=404, detail="No data loaded. Please upload a file first.")

    df = parse_date(date_from) if date_from else None
    dt = parse_date(date_to)   if date_to   else None

    # Use integer IDs to keep memory low (same approach as trios)
    key_to_id: dict[str, int] = {}
    id_to_key: list[str] = []

    def get_id(key: str) -> int:
        if key not in key_to_id:
            key_to_id[key] = len(id_to_key)
            id_to_key.append(key)
        return key_to_id[key]

    pair_count: dict[tuple, int] = defaultdict(int)
    total_orders = 0

    for order in orders_map.values():
        if not in_date_range(order, df, dt):
            continue
        total_orders += 1
        prods = order["products"]
        if len(prods) < 2:
            continue
        ids = sorted({get_id(p["_key"]) for p in prods})
        for pair in combinations(ids, 2):
            pair_count[pair] += 1

    if total_orders == 0:
        return {"total_orders": 0, "top_pairs": []}

    top_raw = sorted(pair_count.items(), key=lambda x: -x[1])[:50]
    del pair_count
    gc.collect()

    needed_keys = set()
    for (ia, ib), _ in top_raw:
        needed_keys.update([id_to_key[ia], id_to_key[ib]])

    prod_info: dict[str, dict] = {}
    for order in orders_map.values():
        for p in order["products"]:
            k = p["_key"]
            if k in needed_keys and k not in prod_info:
                prod_info[k] = {"name": p["name"], "sku": get_p(p,"sku"),
                                "id": get_p(p,"id"), "type": get_p(p,"type")}
        if len(prod_info) == len(needed_keys):
            break

    top_pairs = []
    for (ia, ib), cnt in top_raw:
        ka, kb = id_to_key[ia], id_to_key[ib]
        top_pairs.append({
            "product_a": prod_info.get(ka, {"name": ka, "sku": "", "id": "", "type": ""}),
            "product_b": prod_info.get(kb, {"name": kb, "sku": "", "id": "", "type": ""}),
            "count": cnt,
            "pct": round(cnt / total_orders * 100, 1),
        })

    del top_raw, prod_info, key_to_id, id_to_key
    gc.collect()

    return {"total_orders": total_orders, "top_pairs": top_pairs}

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

    # ── Step 1: assign each unique product key a small integer ID
    # This lets us store tuples of ints instead of tuples of long strings,
    # massively reducing memory usage for the counts dict.
    key_to_id: dict[str, int] = {}
    id_to_key: list[str] = []

    def get_id(key: str) -> int:
        if key not in key_to_id:
            key_to_id[key] = len(id_to_key)
            id_to_key.append(key)
        return key_to_id[key]

    # ── Step 2: count trios using integer tuples (much smaller in memory)
    trio_count: dict[tuple, int] = defaultdict(int)
    total_orders = 0

    for order in orders_map.values():
        if not in_date_range(order, df, dt):
            continue
        total_orders += 1
        prods = order["products"]
        if len(prods) < 3:
            continue
        # Sort integer IDs — deduplicating products within the order
        ids = sorted({get_id(p["_key"]) for p in prods})
        for trio in combinations(ids, 3):
            trio_count[trio] += 1

    if total_orders == 0:
        return {"total_orders": 0, "top_trios": []}

    # ── Step 3: find top 50 by count — no need to keep all trio_data in memory
    top_raw = sorted(trio_count.items(), key=lambda x: -x[1])[:50]
    del trio_count
    gc.collect()

    # ── Step 4: build a lookup of key -> product info from orders_map
    # Only for the keys that appear in the top 50
    needed_keys = set()
    for (ia, ib, ic), _ in top_raw:
        needed_keys.update([id_to_key[ia], id_to_key[ib], id_to_key[ic]])

    prod_info: dict[str, dict] = {}
    for order in orders_map.values():
        for p in order["products"]:
            k = p["_key"]
            if k in needed_keys and k not in prod_info:
                prod_info[k] = {"name": p["name"], "sku": get_p(p,"sku"),
                                "id": get_p(p,"id"), "type": get_p(p,"type")}
        if len(prod_info) == len(needed_keys):
            break  # found everything we need

    # ── Step 5: build final result
    top_trios = []
    for (ia, ib, ic), cnt in top_raw:
        ka, kb, kc = id_to_key[ia], id_to_key[ib], id_to_key[ic]
        top_trios.append({
            "product_a": prod_info.get(ka, {"name": ka, "sku": "", "id": "", "type": ""}),
            "product_b": prod_info.get(kb, {"name": kb, "sku": "", "id": "", "type": ""}),
            "product_c": prod_info.get(kc, {"name": kc, "sku": "", "id": "", "type": ""}),
            "count": cnt,
            "pct": round(cnt / total_orders * 100, 1),
        })

    del top_raw, prod_info, key_to_id, id_to_key
    gc.collect()

    return {"total_orders": total_orders, "top_trios": top_trios}

# ── Type vs Type endpoint ────────────────────────────────────────
@app.get("/type-pairs")
def type_pairs(
    date_from:   Optional[str] = Query(None),
    date_to:     Optional[str] = Query(None),
    filter_type: Optional[str] = Query(None),  # if set, only show pairs involving this type
):
    if not orders_map:
        raise HTTPException(status_code=404, detail="No data loaded. Please upload a file first.")

    df = parse_date(date_from) if date_from else None
    dt = parse_date(date_to)   if date_to   else None
    ft = filter_type.strip().lower() if filter_type else None

    type_pair_count: dict[tuple, int] = defaultdict(int)
    # track orders that contain the filter type (for percentage denominator)
    matching_orders = 0
    total_orders = 0

    for order in orders_map.values():
        if not in_date_range(order, df, dt):
            continue
        total_orders += 1
        prods = order["products"]
        types = sorted({get_p(p, "type") for p in prods if get_p(p, "type")})
        if len(types) < 2:
            continue

        if ft:
            # Only count this order if the filter type is present
            order_types_lower = [t.lower() for t in types]
            if not any(ft == tl for tl in order_types_lower):
                continue
            matching_orders += 1
            # Find the actual cased version of the filter type
            matched_type = next(t for t in types if t.lower() == ft)
            # Pair matched type with every other type in this order
            for other in types:
                if other.lower() == ft:
                    continue
                pair = tuple(sorted([matched_type, other]))
                type_pair_count[pair] += 1
        else:
            matching_orders += 1
            for ta, tb in combinations(types, 2):
                type_pair_count[(ta, tb)] += 1

    if matching_orders == 0:
        return {"total_orders": total_orders, "matching_orders": 0, "top_type_pairs": []}

    top_type_pairs = sorted(
        [{"type_a": ta, "type_b": tb, "count": c, "pct": round(c / matching_orders * 100, 1)}
         for (ta, tb), c in type_pair_count.items()],
        key=lambda x: (-x["pct"], -x["count"])
    )[:50]

    del type_pair_count
    gc.collect()

    return {"total_orders": total_orders, "matching_orders": matching_orders, "top_type_pairs": top_type_pairs}

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

# ── Cross-sell endpoint ─────────────────────────────────────────
# Search for a SECONDARY product. Primary = any product with higher
# global total revenue (price x qty summed across all orders).
# Ranked by co-purchase count (how many orders had both).
@app.get("/crosssell")
def crosssell(
    name:      Optional[str] = Query(None),
    sku:       Optional[str] = Query(None),
    pid:       Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to:   Optional[str] = Query(None),
    limit:     int           = Query(50),
    sort_by:   str           = Query("co_count"),  # "co_count" or "revenue"
):
    if not orders_map:
        raise HTTPException(status_code=404, detail="No data loaded. Please upload a file first.")

    nl = (name or "").lower()
    sl = (sku  or "").lower()
    il = (pid  or "").lower()
    if not any([nl, sl, il]):
        raise HTTPException(status_code=400, detail="Provide at least one search term")

    df = parse_date(date_from) if date_from else None
    dt = parse_date(date_to)   if date_to   else None
    has_price = any(v > 0 for v in product_revenue.values()) if product_revenue else False

    def is_secondary(p):
        return ((nl and nl in p["name"].lower()) or
                (sl and sl in get_p(p, "sku").lower()) or
                (il and il in get_p(p, "id").lower()))

    # Get secondary's global revenue (0 if no price data)
    secondary_revenue = 0.0
    for k, rev in product_revenue.items():
        pk = k.split("|")[0].lower()  # product name from key
        if nl and nl in pk:
            secondary_revenue = max(secondary_revenue, rev)
        # Also check by sku
    # More precise: find secondary key from orders_map
    secondary_keys = set()
    for order in orders_map.values():
        for p in order["products"]:
            if is_secondary(p):
                secondary_keys.add(p["_key"])
    secondary_max_revenue = max((product_revenue.get(k, 0.0) for k in secondary_keys), default=0.0)

    primary_total:    dict[str, int]  = defaultdict(int)
    primary_with_sec: dict[str, int]  = defaultdict(int)
    primary_data:     dict[str, dict] = {}
    secondary_order_count = 0

    for order in orders_map.values():
        if not in_date_range(order, df, dt):
            continue
        products = order["products"]
        has_sec = any(is_secondary(p) for p in products)
        if has_sec:
            secondary_order_count += 1

        for p in products:
            if is_secondary(p):
                continue
            k = p["_key"]
            p_rev = product_revenue.get(k, 0.0)

            # If price data exists: only count as primary if its total revenue
            # is greater than or equal to the secondary's total revenue.
            # If no price data: all co-purchased products qualify as primary.
            if has_price and secondary_max_revenue > 0 and p_rev < secondary_max_revenue:
                continue

            primary_total[k] += 1
            if has_sec:
                primary_with_sec[k] += 1
            if k not in primary_data:
                primary_data[k] = {
                    "name":          p["name"],
                    "sku":           get_p(p, "sku"),
                    "id":            get_p(p, "id"),
                    "type":          get_p(p, "type"),
                    "total_revenue": round(product_revenue.get(k, 0.0), 2),
                }

    if secondary_order_count == 0:
        return {"secondary_order_count": 0, "has_price_data": has_price, "results": []}

    results = sorted(
        [
            {
                "name":          primary_data[k]["name"],
                "sku":           primary_data[k]["sku"],
                "id":            primary_data[k]["id"],
                "type":          primary_data[k]["type"],
                "total_revenue": primary_data[k]["total_revenue"],
                "primary_total": primary_total[k],
                "co_count":      primary_with_sec[k],
                "pct":           round(primary_with_sec[k] / primary_total[k] * 100, 1),
            }
            for k in primary_data
            if primary_with_sec[k] > 0
        ],
        key=lambda x: (-x["total_revenue"], -x["co_count"]) if sort_by == "revenue"
             else (-x["co_count"], -x["pct"])
    )[:limit]

    return {
        "secondary_order_count": secondary_order_count,
        "has_price_data": has_price,
        "results": results,
    }

# ── Serve frontend ───────────────────────────────────────────────
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {"message": "Bought Together API running."}

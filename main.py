import io
import os
import csv
import uuid
from collections import defaultdict
from typing import Optional

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

# ── In-memory store ──────────────────────────────────────────────
# orders_map: { order_id -> [ {name, sku, id, type} ] }
orders_map: dict[str, list[dict]] = {}
stats: dict = {}

FIELD_SYNONYMS = {
    "order_id":    ["order id","name","order name","order_id","order number","order_no"],
    "product_name":["lineitem name","line item name","product title","lineitem_name","product name","title"],
    "sku":         ["lineitem sku","sku","variant sku","lineitem_sku","variant_sku"],
    "product_id":  ["product id","product_id"],
    "product_type":["product type","product_type","type","vendor"],
}

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

# ── Upload endpoint ──────────────────────────────────────────────
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    global orders_map, stats

    content = await file.read()
    headers, rows = parse_csv_bytes(content)
    col_map = detect_columns(headers)

    if "order_id" not in col_map or "product_name" not in col_map:
        # Return headers so frontend can ask user to map them
        return {
            "status": "needs_mapping",
            "headers": headers,
            "col_map": col_map,
            "row_count": len(rows),
        }

    orders_map, stats = build_orders_map(rows, col_map)
    return {"status": "ok", **stats}

class MappingRequest(BaseModel):
    headers: list[str]
    rows_sample: list[list[str]]  # not used server-side (we re-read from stored raw)
    col_map: dict[str, int]

# We also allow the frontend to POST a confirmed mapping after upload
@app.post("/upload-with-mapping")
async def upload_with_mapping(
    file: UploadFile = File(...),
    order_id_col: int = Query(...),
    product_name_col: int = Query(...),
    sku_col: int = Query(-1),
    product_id_col: int = Query(-1),
    product_type_col: int = Query(-1),
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

    orders_map, stats = build_orders_map(rows, col_map)
    return {"status": "ok", **stats}

def build_orders_map(rows, col_map):
    om: dict[str, list[dict]] = defaultdict(list)

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

        key = f"{name}|{sku}"
        if not any(p["_key"] == key for p in om[order_id]):
            om[order_id].append({"name": name, "sku": sku, "id": pid, "type": ptype, "_key": key})

    om = dict(om)

    all_names  = set()
    all_skus   = set()
    all_types  = set()
    for prods in om.values():
        for p in prods:
            if p["name"]:  all_names.add(p["name"])
            if p["sku"]:   all_skus.add(p["sku"])
            if p["type"]:  all_types.add(p["type"])

    s = {
        "order_count":   len(om),
        "product_count": len(all_names),
        "sku_count":     len(all_skus),
        "type_count":    len(all_types),
        "types":         sorted(all_types),
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
    name: Optional[str] = Query(None),
    sku:  Optional[str] = Query(None),
    pid:  Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    limit: int = Query(50),
):
    if not orders_map:
        raise HTTPException(status_code=404, detail="No data loaded. Please upload a file first.")

    nl = (name or "").lower()
    sl = (sku  or "").lower()
    il = (pid  or "").lower()
    tl = (type or "").lower()

    if not any([nl, sl, il, tl]):
        raise HTTPException(status_code=400, detail="Provide at least one search term")

    def is_match(p):
        return (
            (nl and nl in p["name"].lower()) or
            (sl and sl in p["sku"].lower())  or
            (il and il in p["id"].lower())   or
            (tl and tl in p["type"].lower())
        )

    matching_orders = []
    for order_id, products in orders_map.items():
        if any(is_match(p) for p in products):
            matching_orders.append(products)

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
    return {"message": "Bought Together API running. POST /upload to load data, GET /search to query."}

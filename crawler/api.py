#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
백링크 데이터베이스 조회 및 분석 API
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from datetime import datetime
import json

app = FastAPI(
    title="Backlink Database API",
    description="Direct Ahrefs-like backlink database",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = 'backlinks.db'


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Backlink Database API",
        "endpoints": [
            "/api/domain/{domain}",
            "/api/backlinks?domain={domain}&limit=100",
            "/api/compare?domain1={d1}&domain2={d2}",
            "/api/stats"
        ]
    }


@app.get("/api/domain/{domain}")
async def get_domain_info(domain: str):
    """도메인 정보 조회"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('''
        SELECT 
            domain,
            domain_rating,
            inbound_links,
            outbound_links,
            crawl_count,
            last_crawled,
            status
        FROM domains
        WHERE domain = ?
    ''', (domain,))
    
    result = c.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    return dict(result)


@app.get("/api/backlinks")
async def get_backlinks(domain: str, limit: int = Query(100, ge=1, le=1000)):
    """도메인의 백링크 조회"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('''
        SELECT 
            d.domain as source_domain,
            b.source_url,
            b.anchor_text,
            b.discovered_at,
            d.domain_rating as source_rating
        FROM backlinks b
        JOIN domains d ON b.source_domain_id = d.id
        JOIN domains d2 ON b.target_domain_id = d2.id
        WHERE d2.domain = ?
        AND b.is_active = 1
        ORDER BY d.domain_rating DESC
        LIMIT ?
    ''', (domain, limit))
    
    results = [dict(row) for row in c.fetchall()]
    conn.close()
    
    total = len(results)
    unique_domains = len(set(r['source_domain'] for r in results))
    avg_score = sum(r['source_rating'] for r in results) / total if total > 0 else 0
    
    return {
        "domain": domain,
        "total_backlinks": total,
        "unique_domains": unique_domains,
        "average_source_rating": round(avg_score, 2),
        "backlinks": results[:limit]
    }


@app.get("/api/compare")
async def compare_domains(domain1: str, domain2: str):
    """두 도메인 비교"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Domain 1 정보
    c.execute('''
        SELECT domain_rating, inbound_links, outbound_links
        FROM domains WHERE domain = ?
    ''', (domain1,))
    d1_info = dict(c.fetchone() or {})
    
    # Domain 2 정보
    c.execute('''
        SELECT domain_rating, inbound_links, outbound_links
        FROM domains WHERE domain = ?
    ''', (domain2,))
    d2_info = dict(c.fetchone() or {})
    
    conn.close()
    
    return {
        "domain1": {
            "domain": domain1,
            **d1_info
        },
        "domain2": {
            "domain": domain2,
            **d2_info
        },
        "winner": domain1 if d1_info.get('domain_rating', 0) > d2_info.get('domain_rating', 0) else domain2
    }


@app.get("/api/stats")
async def get_stats():
    """데이터베이스 통계"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM domains')
    total_domains = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM backlinks')
    total_backlinks = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM pages')
    total_pages = c.fetchone()[0]
    
    c.execute('SELECT AVG(domain_rating) FROM domains')
    avg_rating = c.fetchone()[0] or 0
    
    c.execute('SELECT domain FROM domains ORDER BY domain_rating DESC LIMIT 10')
    top_domains = [row[0] for row in c.fetchall()]
    
    conn.close()
    
    return {
        "total_domains": total_domains,
        "total_backlinks": total_backlinks,
        "total_pages": total_pages,
        "average_domain_rating": round(avg_rating, 2),
        "top_domains": top_domains
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8001, reload=True)

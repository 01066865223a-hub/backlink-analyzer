#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
백링크 데이터베이스 관리 CLI
"""

import sqlite3
import sys
from backlink_crawler import BacklinkDatabase

def show_stats():
    """통계 표시"""
    conn = sqlite3.connect('backlinks.db')
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM domains')
    domains = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM backlinks')
    backlinks = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM pages')
    pages = c.fetchone()[0]
    
    print(f"\n=== Database Stats ===")
    print(f"Domains: {domains}")
    print(f"Backlinks: {backlinks}")
    print(f"Pages: {pages}")
    
    c.execute('SELECT domain, domain_rating FROM domains ORDER BY domain_rating DESC LIMIT 10')
    print(f"\nTop 10 Domains:")
    for domain, rating in c.fetchall():
        print(f"  {domain}: {rating:.2f}")
    
    conn.close()

def query_domain(domain: str):
    """도메인 조회"""
    db = BacklinkDatabase()
    backlinks = db.get_backlinks_for_domain(domain, limit=20)
    
    print(f"\n=== Backlinks for {domain} ===")
    for source_domain, source_url, anchor, discovered, rating in backlinks:
        print(f"From: {source_domain} (Rating: {rating:.2f})")
        print(f"  URL: {source_url[:80]}...")
        print(f"  Anchor: {anchor}")
        print()

def crawl(max_crawls: int = 100):
    """크롤러 실행"""
    seed_domains = [
        'github.com',
        'stackoverflow.com',
        'wikipedia.org',
        'medium.com',
        'techcrunch.com',
    ]
    
    db = BacklinkDatabase()
    db.run_crawler(seed_domains, max_crawls=max_crawls)

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python cli.py crawl [max_crawls]")
        print("  python cli.py query <domain>")
        print("  python cli.py stats")
        return
    
    cmd = sys.argv[1]
    
    if cmd == 'stats':
        show_stats()
    elif cmd == 'query':
        if len(sys.argv) < 3:
            print("Usage: python cli.py query <domain>")
            return
        query_domain(sys.argv[2])
    elif cmd == 'crawl':
        max_crawls = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        crawl(max_crawls)
    else:
        print(f"Unknown command: {cmd}")

if __name__ == '__main__':
    main()

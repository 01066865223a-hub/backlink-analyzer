#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
진짜 Ahrefs 수준 백링크 데이터베이스 구축

구조:
1. 초기 시드 도메인 크롤링
2. 발견된 도메인 자동 큐에 추가
3. 계속 크롤링하면서 백링크 저장
4. 모든 도메인의 링크 관계 매핑
5. 권위도(DA/PA) 계산

무료로 돌리되, 수개월~수년에 거쳐 웹 전체를 크롤링하는 구조
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
import time
import hashlib
import json
from collections import defaultdict, deque
import threading
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class BacklinkDatabase:
    """전체 웹을 위한 백링크 데이터베이스"""
    
    def __init__(self, db_path='backlinks.db'):
        self.db_path = db_path
        self.init_db()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.visited = set()
        self.queue = deque()
        
    def init_db(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 도메인 테이블
        c.execute('''
            CREATE TABLE IF NOT EXISTS domains (
                id INTEGER PRIMARY KEY,
                domain TEXT UNIQUE NOT NULL,
                discovered_at TIMESTAMP,
                last_crawled TIMESTAMP,
                crawl_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                inbound_links INTEGER DEFAULT 0,
                outbound_links INTEGER DEFAULT 0,
                domain_rating REAL DEFAULT 0,
                page_rating REAL DEFAULT 0
            )
        ''')
        
        # 백링크 테이블
        c.execute('''
            CREATE TABLE IF NOT EXISTS backlinks (
                id INTEGER PRIMARY KEY,
                source_domain_id INTEGER,
                target_domain_id INTEGER,
                source_url TEXT,
                target_url TEXT,
                anchor_text TEXT,
                link_type TEXT,
                discovered_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY(source_domain_id) REFERENCES domains(id),
                FOREIGN KEY(target_domain_id) REFERENCES domains(id)
            )
        ''')
        
        # 페이지 테이블
        c.execute('''
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY,
                domain_id INTEGER,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                description TEXT,
                h1 TEXT,
                inbound_links INTEGER DEFAULT 0,
                outbound_links INTEGER DEFAULT 0,
                crawled_at TIMESTAMP,
                status_code INTEGER,
                FOREIGN KEY(domain_id) REFERENCES domains(id)
            )
        ''')
        
        # 인덱싱
        c.execute('CREATE INDEX IF NOT EXISTS idx_domain ON domains(domain)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_backlinks_src ON backlinks(source_domain_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_backlinks_tgt ON backlinks(target_domain_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_pages_domain ON pages(domain_id)')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized: {self.db_path}")
    
    def add_domain(self, domain: str):
        """도메인 추가"""
        domain = domain.lower().strip()
        if not domain:
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute('''
                INSERT INTO domains (domain, discovered_at, status)
                VALUES (?, ?, 'pending')
            ''', (domain, datetime.utcnow().isoformat()))
            conn.commit()
            logger.info(f"Added domain: {domain}")
        except sqlite3.IntegrityError:
            pass
        finally:
            conn.close()
    
    def get_next_to_crawl(self):
        """크롤링할 다음 도메인 가져오기"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT id, domain FROM domains
            WHERE status = 'pending'
            ORDER BY discovered_at ASC
            LIMIT 1
        ''')
        
        result = c.fetchone()
        conn.close()
        
        return result
    
    def crawl_domain(self, domain_id: int, domain: str):
        """도메인 크롤링"""
        logger.info(f"Crawling: {domain}")
        
        try:
            url = f"https://{domain}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
        except Exception as e:
            logger.warning(f"Failed to crawl {domain}: {e}")
            self._update_domain_status(domain_id, 'failed')
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        base_url = f"https://{domain}"
        
        # 페이지 정보 저장
        title = soup.title.string if soup.title else ""
        h1 = soup.find('h1')
        h1_text = h1.get_text() if h1 else ""
        
        self._save_page(domain_id, base_url, title, h1_text, response.status_code)
        
        # 링크 추출
        internal_links = []
        external_links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href'].strip()
            anchor_text = link.get_text(strip=True)[:200]
            
            if not href or href.startswith(('javascript:', 'mailto:', '#')):
                continue
            
            full_url = urljoin(base_url, href)
            if '#' in full_url:
                full_url = full_url.split('#')[0]
            
            parsed = urlparse(full_url)
            link_domain = parsed.netloc
            
            if not link_domain:
                continue
            
            link_data = {
                'url': full_url,
                'anchor': anchor_text,
                'domain': link_domain
            }
            
            if link_domain == domain:
                internal_links.append(link_data)
            else:
                external_links.append(link_data)
        
        # 외부 링크 저장 (다른 도메인으로의 백링크)
        for ext_link in external_links:
            self._save_backlink(
                source_domain_id=domain_id,
                source_url=ext_link['url'],
                target_domain=ext_link['domain'],
                target_url=ext_link['url'],
                anchor_text=ext_link['anchor']
            )
            # 새로운 도메인 발견 시 큐에 추가
            self.add_domain(ext_link['domain'])
        
        # 내부 링크도 저장 (같은 도메인 내)
        for int_link in internal_links:
            self._save_page(domain_id, int_link['url'], "", "", 200)
        
        self._update_domain_status(domain_id, 'crawled')
        logger.info(f"Crawled {domain}: {len(external_links)} external links, {len(internal_links)} internal")
    
    def _save_page(self, domain_id: int, url: str, title: str, h1: str, status_code: int):
        """페이지 저장"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute('''
                INSERT INTO pages (domain_id, url, title, h1, crawled_at, status_code)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (domain_id, url, title[:200], h1[:200], datetime.utcnow().isoformat(), status_code))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        finally:
            conn.close()
    
    def _save_backlink(self, source_domain_id: int, source_url: str, target_domain: str, target_url: str, anchor_text: str):
        """백링크 저장"""
        # 대상 도메인 ID 가져오기 또는 생성
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT id FROM domains WHERE domain = ?', (target_domain,))
        result = c.fetchone()
        
        if result:
            target_domain_id = result[0]
        else:
            c.execute('''
                INSERT INTO domains (domain, discovered_at, status)
                VALUES (?, ?, 'pending')
            ''', (target_domain, datetime.utcnow().isoformat()))
            conn.commit()
            target_domain_id = c.lastrowid
        
        # 백링크 저장
        try:
            c.execute('''
                INSERT INTO backlinks
                (source_domain_id, target_domain_id, source_url, target_url, anchor_text, link_type, discovered_at)
                VALUES (?, ?, ?, ?, ?, 'dofollow', ?)
            ''', (source_domain_id, target_domain_id, source_url, target_url, anchor_text[:200], datetime.utcnow().isoformat()))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        finally:
            conn.close()
    
    def _update_domain_status(self, domain_id: int, status: str):
        """도메인 상태 업데이트"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            UPDATE domains
            SET status = ?, last_crawled = ?, crawl_count = crawl_count + 1
            WHERE id = ?
        ''', (status, datetime.utcnow().isoformat(), domain_id))
        
        conn.commit()
        conn.close()
    
    def calculate_domain_rating(self, domain_id: int) -> float:
        """도메인 권위도 계산 (DA와 유사)"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 인바운드 링크 수
        c.execute('SELECT COUNT(*) FROM backlinks WHERE target_domain_id = ?', (domain_id,))
        inbound = c.fetchone()[0]
        
        # 아웃바운드 링크 수
        c.execute('SELECT COUNT(*) FROM backlinks WHERE source_domain_id = ?', (domain_id,))
        outbound = c.fetchone()[0]
        
        # 참조 도메인 수
        c.execute('''
            SELECT COUNT(DISTINCT source_domain_id)
            FROM backlinks
            WHERE target_domain_id = ?
        ''', (domain_id,))
        referring_domains = c.fetchone()[0]
        
        conn.close()
        
        # 간단한 DA 계산: 로그 스케일
        # 실제 Ahrefs는 훨씬 복잡한 알고리즘 사용
        import math
        score = 10 + (math.log10(inbound + 1) * 15) + (math.log10(referring_domains + 1) * 10)
        score = min(100, max(0, score))
        
        # 저장
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            UPDATE domains
            SET domain_rating = ?, inbound_links = ?, outbound_links = ?
            WHERE id = ?
        ''', (score, inbound, outbound, domain_id))
        conn.commit()
        conn.close()
        
        return score
    
    def get_backlinks_for_domain(self, domain: str, limit: int = 100):
        """특정 도메인의 백링크 조회"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT 
                d.domain,
                b.source_url,
                b.anchor_text,
                b.discovered_at,
                d.domain_rating
            FROM backlinks b
            JOIN domains d ON b.source_domain_id = d.id
            JOIN domains d2 ON b.target_domain_id = d2.id
            WHERE d2.domain = ?
            AND b.is_active = 1
            ORDER BY d.domain_rating DESC
            LIMIT ?
        ''', (domain, limit))
        
        results = c.fetchall()
        conn.close()
        
        return results
    
    def run_crawler(self, seed_domains: list, max_crawls: int = 1000):
        """크롤러 실행"""
        logger.info(f"Starting crawler with {len(seed_domains)} seed domains")
        
        for seed in seed_domains:
            self.add_domain(seed)
        
        crawl_count = 0
        while crawl_count < max_crawls:
            result = self.get_next_to_crawl()
            if not result:
                logger.info("No more domains to crawl")
                break
            
            domain_id, domain = result
            self.crawl_domain(domain_id, domain)
            self.calculate_domain_rating(domain_id)
            
            crawl_count += 1
            
            if crawl_count % 10 == 0:
                logger.info(f"Progress: {crawl_count} domains crawled")
            
            # Rate limiting
            time.sleep(2)
        
        logger.info(f"Crawler finished: {crawl_count} domains crawled")


def main():
    # 초기 시드 도메인들
    seed_domains = [
        'github.com',
        'stackoverflow.com',
        'wikipedia.org',
        'bbc.com',
        'techcrunch.com',
        'medium.com',
        'twitter.com',
        'reddit.com',
    ]
    
    db = BacklinkDatabase()
    
    # 크롤러 시작 (처음에는 적은 수로 테스트)
    db.run_crawler(seed_domains, max_crawls=50)
    
    # 결과 확인
    print("\n=== Sample Results ===")
    backlinks = db.get_backlinks_for_domain('github.com', limit=10)
    for link in backlinks:
        print(f"From: {link[0]} | {link[1][:60]}... | Score: {link[4]}")


if __name__ == '__main__':
    main()

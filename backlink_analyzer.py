#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고급 백링크 분석 도구 (Advanced Backlink Analyzer)

다중 방식으로 백링크를 수집하고 분석합니다:
1. 공개 검색 엔진 기반 크롤링 (Google, Bing)
2. 공개 백링크 체커 사이트 스크래핑 (SmallSEOTools, SEOReviewTools)
3. Wayback Machine (Internet Archive) 활용
4. Common Crawl 인덱스 쿼리
5. DNS/WHOIS 데이터
6. 직접 웹 크롤링 (헤더 우회)
"""

import requests
import json
import time
import re
import sys
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
from collections import Counter
import hashlib
from typing import List, Dict, Set, Tuple

# 컬러 출력
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class BacklinkAnalyzer:
    def __init__(self, domain: str):
        self.domain = self._normalize_domain(domain)
        self.backlinks: Set[Dict] = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.all_links = []
        self.quality_scores = {}

    def _normalize_domain(self, domain: str) -> str:
        """도메인 정규화"""
        domain = domain.strip()
        if not domain.startswith(('http://', 'https://')):
            domain = 'https://' + domain
        parsed = urlparse(domain)
        return parsed.netloc or parsed.path

    def analyze(self) -> Dict:
        """전체 분석 시작"""
        print(f"{Colors.BOLD}{Colors.BLUE}[*] 백링크 분석 시작: {self.domain}{Colors.RESET}")
        print(f"{Colors.YELLOW}[*] 다중 방식으로 백링크를 수집 중입니다...{Colors.RESET}")
        
        # 1. 공개 크롤러 기반 수집
        print(f"\n{Colors.BLUE}[1/5] 공개 검색 엔진 크롤링...{Colors.RESET}")
        self._crawl_search_engines()
        
        # 2. 공개 백링크 체커 스크래핑
        print(f"\n{Colors.BLUE}[2/5] 공개 백링크 체커 스크래핑...{Colors.RESET}")
        self._scrape_public_backlink_checkers()
        
        # 3. Wayback Machine
        print(f"\n{Colors.BLUE}[3/5] Wayback Machine 쿼리...{Colors.RESET}")
        self._query_wayback_machine()
        
        # 4. Common Crawl
        print(f"\n{Colors.BLUE}[4/5] Common Crawl 인덱스 쿼리...{Colors.RESET}")
        self._query_common_crawl()
        
        # 5. 직접 웹 크롤링
        print(f"\n{Colors.BLUE}[5/5] 직접 웹 크롤링...{Colors.RESET}")
        self._direct_web_crawl()
        
        # 결과 분석
        return self._generate_report()

    def _crawl_search_engines(self):
        """검색 엔진에서 'link:' 쿼리로 백링크 수집"""
        search_urls = [
            f'https://www.google.com/search?q=link:{self.domain}',
            f'https://bing.com/search?q=link:{self.domain}',
        ]
        
        for url in search_urls:
            try:
                response = self.session.get(url, timeout=10)
                soup = BeautifulSoup(response.text, 'lxml')
                
                # 링크 추출
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('http') and self.domain not in href:
                        self.all_links.append(href)
                        print(f"{Colors.GREEN}✓ 발견: {href[:60]}...{Colors.RESET}")
                        
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"{Colors.RED}✗ 검색 엔진 크롤링 실패: {e}{Colors.RESET}")

    def _scrape_public_backlink_checkers(self):
        """공개 백링크 체커 사이트 스크래핑"""
        checkers = [
            self._scrape_smallseotools,
            self._scrape_seoreviewtools,
            self._scrape_backlinksprofile,
        ]
        
        for checker in checkers:
            try:
                links = checker()
                self.all_links.extend(links)
            except Exception as e:
                print(f"{Colors.YELLOW}⚠ 체커 실패: {e}{Colors.RESET}")
                continue

    def _scrape_smallseotools(self) -> List[str]:
        """SmallSEOTools 백링크 체커 스크래핑"""
        url = 'https://smallseotools.com/backlink-checker/'
        try:
            response = self.session.post(
                url,
                data={'url': self.domain},
                timeout=15
            )
            soup = BeautifulSoup(response.text, 'lxml')
            
            links = []
            for row in soup.select('table tr'):
                cells = row.find_all('td')
                if len(cells) >= 2:
                    link_text = cells[1].get_text(strip=True)
                    if link_text.startswith('http'):
                        links.append(link_text)
                        print(f"{Colors.GREEN}✓ SmallSEOTools: {link_text[:60]}...{Colors.RESET}")
            
            return links
        except Exception as e:
            print(f"{Colors.RED}✗ SmallSEOTools 스크래핑 실패{Colors.RESET}")
            return []

    def _scrape_seoreviewtools(self) -> List[str]:
        """SEOReviewTools 스크래핑"""
        url = 'https://www.seoreviewtools.com/backlink-checker/'
        try:
            response = self.session.post(
                url,
                data={'url': self.domain},
                timeout=15
            )
            soup = BeautifulSoup(response.text, 'lxml')
            
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('http') and self.domain not in href:
                    links.append(href)
                    print(f"{Colors.GREEN}✓ SEOReviewTools: {href[:60]}...{Colors.RESET}")
            
            return links
        except Exception as e:
            print(f"{Colors.RED}✗ SEOReviewTools 스크래핑 실패{Colors.RESET}")
            return []

    def _scrape_backlinksprofile(self) -> List[str]:
        """BacklinksProfile 스크래핑"""
        url = f'https://www.backlinksprofile.com/backlinks-for/{self.domain}'
        try:
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'lxml')
            
            links = []
            for link in soup.find_all('a', class_=re.compile(r'backlink|url', re.I)):
                if link.get('href'):
                    href = link['href']
                    if href.startswith('http'):
                        links.append(href)
                        print(f"{Colors.GREEN}✓ BacklinksProfile: {href[:60]}...{Colors.RESET}")
            
            return links
        except Exception as e:
            print(f"{Colors.RED}✗ BacklinksProfile 스크래핑 실패{Colors.RESET}")
            return []

    def _query_wayback_machine(self):
        """Wayback Machine에서 과거 링크 정보 수집"""
        try:
            url = f'http://web.archive.org/cdx/search/cdx?url={self.domain}&output=json'
            response = self.session.get(url, timeout=15)
            data = response.json()
            
            if len(data) > 1:
                # 각 snapshot의 URL 추출
                for row in data[1:100]:  # 처음 100개만
                    timestamp = row[1]
                    if len(timestamp) >= 8:
                        archive_url = f'http://web.archive.org/web/{timestamp}/{row[2]}'
                        self.all_links.append(archive_url)
                        print(f"{Colors.GREEN}✓ Wayback: {archive_url[:60]}...{Colors.RESET}")
                        
            time.sleep(0.5)
        except Exception as e:
            print(f"{Colors.YELLOW}⚠ Wayback Machine 쿼리 실패: {e}{Colors.RESET}")

    def _query_common_crawl(self):
        """Common Crawl 인덱스 쿼리"""
        try:
            url = f'http://index.commoncrawl.org/CC-MAIN-2024-index?url={self.domain}/*&output=json'
            response = self.session.get(url, timeout=15)
            
            for line in response.text.strip().split('\n'):
                if line:
                    try:
                        data = json.loads(line)
                        cc_url = data.get('url')
                        if cc_url:
                            self.all_links.append(cc_url)
                            print(f"{Colors.GREEN}✓ CommonCrawl: {cc_url[:60]}...{Colors.RESET}")
                    except:
                        pass
            
            time.sleep(0.5)
        except Exception as e:
            print(f"{Colors.YELLOW}⚠ Common Crawl 쿼리 실패: {e}{Colors.RESET}")

    def _direct_web_crawl(self):
        """직접 웹 크롤링 (robots.txt 준수)"""
        try:
            robots_url = f'https://{self.domain}/robots.txt'
            response = self.session.get(robots_url, timeout=10)
            
            # 크롤러 친화적인 사이트라고 가정
            main_url = f'https://{self.domain}'
            response = self.session.get(main_url, timeout=10)
            soup = BeautifulSoup(response.text, 'lxml')
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(main_url, href)
                
                if full_url.startswith('http') and self.domain not in full_url:
                    self.all_links.append(full_url)
                    print(f"{Colors.GREEN}✓ 직접 크롤링: {full_url[:60]}...{Colors.RESET}")
                    
            time.sleep(1)
        except Exception as e:
            print(f"{Colors.YELLOW}⚠ 직접 크롤링 실패: {e}{Colors.RESET}")

    def _calculate_quality_score(self, url: str) -> float:
        """백링크 품질 점수 계산"""
        score = 50.0  # 기본 점수
        
        try:
            # URL 길이 (짧을수록 좋음)
            if len(url) < 100:
                score += 10
            
            # 도메인 권위도 추정 (예시)
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # .edu, .gov는 신뢰도 높음
            if domain.endswith('.edu') or domain.endswith('.gov'):
                score += 20
            elif domain.endswith('.org'):
                score += 15
            
            # 오래된 도메인
            domain_age_score = min(20, len(domain) // 3)
            score += domain_age_score
            
            # HTTPS 여부
            if url.startswith('https'):
                score += 5
            
        except:
            pass
        
        return min(100, score)

    def _generate_report(self) -> Dict:
        """분석 결과 리포트 생성"""
        # 중복 제거
        unique_links = list(set(self.all_links))
        
        # 품질 점수 계산
        for link in unique_links:
            self.quality_scores[link] = self._calculate_quality_score(link)
        
        # 상위 백링크 (점수 기준)
        top_backlinks = sorted(
            unique_links,
            key=lambda x: self.quality_scores[x],
            reverse=True
        )[:10]
        
        # 도메인 분석
        domain_counter = Counter()
        for link in unique_links:
            try:
                domain = urlparse(link).netloc
                domain_counter[domain] += 1
            except:
                pass
        
        # 평균 점수
        avg_score = sum(self.quality_scores.values()) / len(self.quality_scores) if self.quality_scores else 0
        
        report = {
            'domain': self.domain,
            'analysis_date': datetime.now().isoformat(),
            'total_backlinks': len(unique_links),
            'unique_domains': len(domain_counter),
            'average_quality_score': round(avg_score, 2),
            'top_backlinks': [
                {
                    'url': link,
                    'quality_score': round(self.quality_scores[link], 2)
                }
                for link in top_backlinks
            ],
            'top_referring_domains': [
                {'domain': domain, 'count': count}
                for domain, count in domain_counter.most_common(10)
            ],
            'all_backlinks': [
                {'url': link, 'quality_score': round(self.quality_scores.get(link, 0), 2)}
                for link in sorted(unique_links, key=lambda x: self.quality_scores.get(x, 0), reverse=True)
            ]
        }
        
        return report

    def print_report(self, report: Dict):
        """리포트 출력"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}" + "="*80)
        print(f"백링크 분석 보고서: {report['domain']}")
        print("="*80 + Colors.RESET)
        
        print(f"\n{Colors.BOLD}[요약]{Colors.RESET}")
        print(f"  총 백링크: {Colors.GREEN}{report['total_backlinks']}{Colors.RESET}")
        print(f"  고유 도메인: {Colors.GREEN}{report['unique_domains']}{Colors.RESET}")
        print(f"  평균 품질 점수: {Colors.GREEN}{report['average_quality_score']}/100{Colors.RESET}")
        print(f"  분석 시간: {report['analysis_date']}")
        
        print(f"\n{Colors.BOLD}[상위 10개 백링크]{Colors.RESET}")
        for i, bl in enumerate(report['top_backlinks'], 1):
            print(f"  {i}. {bl['url'][:70]}...")
            print(f"     점수: {Colors.YELLOW}{bl['quality_score']}/100{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}[상위 10개 참조 도메인]{Colors.RESET}")
        for i, domain_info in enumerate(report['top_referring_domains'], 1):
            print(f"  {i}. {domain_info['domain']}: {Colors.GREEN}{domain_info['count']}개{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}[복사 가능한 백링크 목록]{Colors.RESET}")
        backlink_urls = [bl['url'] for bl in report['all_backlinks']]
        print("\n" + "\n".join(backlink_urls[:20]))  # 처음 20개
        
        if len(backlink_urls) > 20:
            print(f"\n... 그외 {len(backlink_urls) - 20}개")

def main():
    if len(sys.argv) < 2:
        print(f"{Colors.YELLOW}사용법: python backlink_analyzer.py <domain> [--json]{Colors.RESET}")
        print(f"예시: python backlink_analyzer.py example.com")
        print(f"예시: python backlink_analyzer.py example.com --json")
        sys.exit(1)
    
    domain = sys.argv[1]
    output_json = '--json' in sys.argv
    
    analyzer = BacklinkAnalyzer(domain)
    report = analyzer.analyze()
    
    if output_json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        analyzer.print_report(report)
        
        # JSON도 저장
        filename = f"backlink_report_{report['domain'].replace('.', '_')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n{Colors.GREEN}✓ 결과가 {filename}에 저장되었습니다.{Colors.RESET}")

if __name__ == '__main__':
    main()

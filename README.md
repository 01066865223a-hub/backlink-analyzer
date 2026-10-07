# Ahrefs 수준의 백링크 데이터베이스

무료로 직접 만든 백링크 수집 및 분석 시스템

## 구조

### 1. 크롤러 (backlink_crawler.py)
- 초기 시드 도메인 시작
- 각 도메인 크롤링
- 발견된 새 도메인 자동 큐 추가
- 백링크 관계 저장
- 도메인 권위도(DA) 계산

### 2. 데이터베이스
- domains: 크롤링된 도메인
- backlinks: 도메인 간 링크 관계
- pages: 개별 페이지

### 3. API (api.py)
- /api/domain/{domain} - 도메인 정보
- /api/backlinks?domain=X - 백링크 조회
- /api/compare?domain1=X&domain2=Y - 도메인 비교
- /api/stats - 전체 통계

### 4. CLI (cli.py)
- crawl: 크롤러 실행
- query: 도메인 조회
- stats: 통계

## 실행

```bash
# 초기 크롤링 시작 (50개 도메인)
python crawler/cli.py crawl 50

# 통계 확인
python crawler/cli.py stats

# 특정 도메인 조회
python crawler/cli.py query github.com

# API 서버 시작
python crawler/api.py
```

## 특징

✅ **완전 무료**: 서버 비용 0원
✅ **자체 DB**: 자신의 컴퓨터에 저장
✅ **자동 발견**: 링크된 새 도메인 자동 크롤링
✅ **권위도 계산**: DA(Domain Authority) 계산
✅ **실시간 쿼리**: SQLite로 빠른 조회
✅ **확장 가능**: 계속 크롤링하면서 데이터 축적

## 시간표

- 처음 50개 도메인: ~2분
- 500개 도메인: ~20분
- 5,000개 도메인: ~3시간
- 50,000개 도메인: ~30시간
- 500,000개 도메인: ~2주

계속 실행하면 몇 개월~수년에 걸쳐 웹 전체를 인덱싱할 수 있습니다.

## 주의

- robots.txt 준수
- 각 사이트당 2초 딜레이 (polite crawling)
- 자신의 인프라에서만 실행
- 상업적 용도로 재판매 금지

## 결과

시간이 지날수록:
- 더 많은 도메인 발견
- 백링크 데이터 축적
- 더 정확한 권위도 계산
- Ahrefs 수준에 가까워짐

## 다음 단계

- Elasticsearch로 빠른 검색
- Redis로 캐싱
- 병렬 크롤링 (속도 10배)
- 이미지/PDF 인덱싱
- NLP로 페이지 내용 분석

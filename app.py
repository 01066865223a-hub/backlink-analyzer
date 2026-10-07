#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backlink Analyzer Web API

FastAPI 기반 웹 인터페이스
실행: uvicorn app:app --reload
접속: http://localhost:8000
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backlink_analyzer import BacklinkAnalyzer
import json
import os

app = FastAPI(
    title="Backlink Analyzer API",
    description="고급 백링크 분석 도구",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>백링크 분석기</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .content {
            padding: 40px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }
        
        input[type="text"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1em;
            transition: border-color 0.3s;
        }
        
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 14px 40px;
            border: none;
            border-radius: 8px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            width: 100%;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 40px;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .results {
            display: none;
            margin-top: 40px;
        }
        
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .metric-value {
            font-size: 2em;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .metric-label {
            color: #666;
            font-size: 0.9em;
        }
        
        .section {
            margin-bottom: 40px;
        }
        
        .section h3 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.3em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }
        
        th {
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
        }
        
        tr:hover {
            background: #f8f9fa;
        }
        
        .score {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 0.9em;
        }
        
        .score.high {
            background: #d4edda;
            color: #155724;
        }
        
        .score.medium {
            background: #fff3cd;
            color: #856404;
        }
        
        .score.low {
            background: #f8d7da;
            color: #721c24;
        }
        
        .copy-btn {
            background: #28a745;
            padding: 8px 16px;
            font-size: 0.9em;
            cursor: pointer;
            border-radius: 4px;
            width: auto;
        }
        
        .copy-btn:hover {
            background: #218838;
        }
        
        .error {
            display: none;
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 백링크 분석기</h1>
            <p>도메인의 모든 백링크를 분석하고 품질을 평가합니다</p>
        </div>
        
        <div class="content">
            <div class="form-group">
                <label for="domain">도메인 입력</label>
                <input 
                    type="text" 
                    id="domain" 
                    placeholder="예: example.com 또는 https://example.com"
                    onkeypress="if(event.key==='Enter') analyze()"
                >
            </div>
            
            <button onclick="analyze()">분석 시작</button>
            
            <div class="error" id="error"></div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>분석 중입니다... (약 1-2분 소요)</p>
            </div>
            
            <div class="results" id="results"></div>
        </div>
    </div>
    
    <script>
        async function analyze() {
            const domain = document.getElementById('domain').value.trim();
            
            if (!domain) {
                showError('도메인을 입력해주세요');
                return;
            }
            
            document.getElementById('error').style.display = 'none';
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').style.display = 'none';
            
            try {
                const response = await fetch(`/api/analyze?domain=${encodeURIComponent(domain)}`);
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.detail || '분석 실패');
                }
                
                displayResults(data);
            } catch (error) {
                showError(error.message);
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }
        
        function displayResults(report) {
            let html = `
                <div class="summary">
                    <div class="metric">
                        <div class="metric-value">${report.total_backlinks}</div>
                        <div class="metric-label">총 백링크</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${report.unique_domains}</div>
                        <div class="metric-label">고유 도메인</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${report.average_quality_score}</div>
                        <div class="metric-label">평균 품질 점수</div>
                    </div>
                </div>
                
                <div class="section">
                    <h3>상위 10개 백링크</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>URL</th>
                                <th>품질 점수</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            report.top_backlinks.forEach(bl => {
                const scoreClass = bl.quality_score >= 70 ? 'high' : bl.quality_score >= 50 ? 'medium' : 'low';
                html += `
                    <tr>
                        <td><a href="${bl.url}" target="_blank">${bl.url.substring(0, 80)}...</a></td>
                        <td><span class="score ${scoreClass}">${bl.quality_score}/100</span></td>
                    </tr>
                `;
            });
            
            html += `
                        </tbody>
                    </table>
                </div>
                
                <div class="section">
                    <h3>상위 참조 도메인</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>도메인</th>
                                <th>백링크 수</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            report.top_referring_domains.forEach(domain => {
                html += `
                    <tr>
                        <td>${domain.domain}</td>
                        <td><strong>${domain.count}</strong></td>
                    </tr>
                `;
            });
            
            html += `
                        </tbody>
                    </table>
                </div>
                
                <div class="section">
                    <h3>복사 가능한 백링크 목록</h3>
                    <button class="copy-btn" onclick="copyAllBacklinks()">모두 복사</button>
                    <textarea id="backlinks" readonly style="width:100%; height:300px; margin-top:10px; padding:10px; border:1px solid #ddd; border-radius:8px;">
            `;
            
            report.all_backlinks.forEach(bl => {
                html += bl.url + '\n';
            });
            
            html += `
                    </textarea>
                </div>
            `;
            
            document.getElementById('results').innerHTML = html;
            document.getElementById('results').style.display = 'block';
        }
        
        function showError(message) {
            const errorDiv = document.getElementById('error');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
        
        function copyAllBacklinks() {
            const textarea = document.getElementById('backlinks');
            textarea.select();
            document.execCommand('copy');
            alert('복사되었습니다!');
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTML_TEMPLATE

@app.get("/api/analyze")
async def analyze(domain: str):
    if not domain:
        raise HTTPException(status_code=400, detail="도메인을 입력해주세요")
    
    try:
        analyzer = BacklinkAnalyzer(domain)
        report = analyzer.analyze()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

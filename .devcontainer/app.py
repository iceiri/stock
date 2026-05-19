import datetime as dt
import html
import re
from typing import List, Dict

import numpy as np
import pandas as pd
import plotly.graph_objs as go
import streamlit as st
import yfinance as yf

import json
import os
import uuid
import scipy.stats as stats

PORTFOLIO_FILE = "portfolio.json"

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        try:
            with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
                cards = json.load(f)
                for c in cards:
                    if "id" not in c:
                        c["id"] = str(uuid.uuid4())
                return cards
        except:
            pass
    return None

def save_portfolio(cards):
    try:
        with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
            json.dump(cards, f, ensure_ascii=False, indent=2)
    except:
        pass

TAX_BADGE_CSS = """
<style>
/* Remove default margin/padding from markdown paragraphs */
div[data-testid="stMarkdownContainer"] p {
    margin: 0 !important;
    padding: 0 !important;
}

/* --- FLEX ROW LAYOUT FOR NAME + BADGE + SELECTBOX --- */
div[data-testid="stVerticalBlock"]:has(.tax-badge-row):not(:has(div[data-testid="stVerticalBlock"] .tax-badge-row)) {
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: flex-start !important;
    flex-wrap: nowrap !important;
    gap: 8px !important;
}
div[data-testid="stVerticalBlock"]:has(.tax-badge-row):not(:has(div[data-testid="stVerticalBlock"] .tax-badge-row)) > div {
    margin: 0 !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
}
div[data-testid="stVerticalBlock"]:has(.tax-badge-row):not(:has(div[data-testid="stVerticalBlock"] .tax-badge-row)) div[data-testid="element-container"] {
    margin: 0 !important;
    padding: 0 !important;
}
div[data-testid="stVerticalBlock"]:has(.tax-badge-row):not(:has(div[data-testid="stVerticalBlock"] .tax-badge-row)) > :nth-child(1) {
    flex: 0 1 auto !important;
    min-width: 0 !important;
    width: auto !important;
}
div[data-testid="stVerticalBlock"]:has(.tax-badge-row):not(:has(div[data-testid="stVerticalBlock"] .tax-badge-row)) > :nth-child(1) * {
    min-width: 0 !important;
}
div[data-testid="stVerticalBlock"]:has(.tax-badge-row):not(:has(div[data-testid="stVerticalBlock"] .tax-badge-row)) div[data-testid="stMarkdownContainer"] {
    margin: 0 !important;
    padding: 0 !important;
}
div[data-testid="stVerticalBlock"]:has(.tax-badge-row):not(:has(div[data-testid="stVerticalBlock"] .tax-badge-row)) > :nth-child(2) {
    flex: 0 0 auto !important;
    width: max-content !important;
}
div[data-testid="stVerticalBlock"]:has(.tax-badge-row):not(:has(div[data-testid="stVerticalBlock"] .tax-badge-row)) div[data-testid="stSelectbox"] {
    width: max-content !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}
div[data-testid="stVerticalBlock"]:has(.tax-badge-row):not(:has(div[data-testid="stVerticalBlock"] .tax-badge-row)) div[data-testid="stWidgetLabel"] {
    display: none !important;
}

/* Style the selectbox */

div[data-testid="stVerticalBlock"]:has(.tax-badge-row):not(:has(div[data-testid="stVerticalBlock"] .tax-badge-row)) div[data-baseweb="select"] > div:nth-child(1) {
    background-color: #fef3c7 !important;
    border: none !important;
    border-radius: 4px !important;
    padding: 0 6px !important;
    min-height: 28px !important;
    height: 28px !important;
    display: flex !important;
    align-items: center !important;
    box-sizing: border-box !important;
    cursor: pointer !important;
    box-shadow: none !important;
    outline: none !important;
}

div[data-testid="stVerticalBlock"]:has(.tax-badge-row):not(:has(div[data-testid="stVerticalBlock"] .tax-badge-row)) div[data-baseweb="select"] > div:nth-child(1) > div {
    color: #92400e !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    padding: 0 !important;
    margin: 0 !important;
}

div[data-testid="stVerticalBlock"]:has(.tax-badge-row):not(:has(div[data-testid="stVerticalBlock"] .tax-badge-row)) div[data-baseweb="select"] svg {
    fill: #92400e !important;
    width: 14px !important;
    height: 14px !important;
}

div[data-baseweb="popover"] ul {
    width: max-content !important;
    min-width: 140px !important;
}
div[data-baseweb="popover"] ul li {
    font-size: 0.8rem !important;
}
div[data-baseweb="popover"] ul li span {
    text-overflow: unset !important;
    white-space: nowrap !important;
    overflow: visible !important;
}
div[data-testid="stVerticalBlock"]:has(.tax-badge-row):not(:has(div[data-testid="stVerticalBlock"] .tax-badge-row)) div[data-baseweb="select"] input {
    caret-color: transparent !important;
}
</style>
"""

SETTINGS_FILE = "settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except:
        pass

def sync_settings():
    _settings = load_settings()
    keys_to_sync = [
        "cmp_1", "cmp_2", "cmp_3", "cmp_start", "cmp_end",
        "sim_t1", "sim_t2", "sim_t3", "sim_type", "sim_amount", "sim_start", "sim_end",
        "sim_apply_tax", "c_ind_ticker", "c_ind_sims"
    ]
    updated = False
    for k in keys_to_sync:
        if k in st.session_state:
            val = st.session_state[k]
            if isinstance(val, dt.date):
                val = val.isoformat()
            if _settings.get(k) != val:
                _settings[k] = val
                updated = True
    if updated:
        save_settings(_settings)


# -----------------------------
# 기본 티커 목록 / 한글 매핑
# -----------------------------

COMMON_TICKERS: List[str] = [
    # 미국 대형주 / ETF
    "AAPL",
    "MSFT",
    "TSLA",
    "AMZN",
    "GOOGL",
    "QQQ",
    "SPY",
    "SCHD",
    "VOO",
    # 한국 대표주
    "005930.KS",  # 삼성전자
    "000660.KS",  # SK하이닉스
    "035720.KS",  # 카카오
    "035420.KQ",  # 네이버(코스닥 예시)
]

KOREAN_TICKER_MAP: Dict[str, str] = {
    # 미국
    "애플": "AAPL",
    "마이크로소프트": "MSFT",
    "테슬라": "TSLA",
    "아마존": "AMZN",
    "구글": "GOOGL",
        "엔비디아": "NVDA",
        "메타": "META",
        "넷플릭스": "NFLX",
    "qqq": "QQQ",
    "QQQ": "QQQ",
    "나스닥100": "QQQ",
    "schd": "SCHD",
    "SCHD": "SCHD",
    # 한국
    "삼성전자": "005930.KS",
    "sk하이닉스": "000660.KS",
    "하이닉스": "000660.KS",
    "카카오": "035720.KS",
    "네이버": "035420.KS",
    "에코프로비엠": "247540.KQ",
    "kodex미국나스닥100(h)": "449190.KS",
    "kodex미국나스닥100h": "449190.KS",
    "449190": "449190.KS",
    # 지수
    "코스피": "^KS11",
    "코스닥": "^KQ11",
    "나스닥": "^IXIC",
    "다우": "^DJI",
    "다우지수": "^DJI",
    "s&p500": "^GSPC",
    "S&P500": "^GSPC",
    "sp500": "^GSPC",
}

DISPLAY_NAME_MAP: Dict[str, str] = {
    "^KS11": "코스피",
    "^KQ11": "코스닥",
    "^IXIC": "나스닥",
    "^NDX": "나스닥 100",
    "^DJI": "다우지수",
    "^GSPC": "S&P 500",
    "USDKRW=X": "원/달러 환율",
    "GC=F": "금 (Gold)",
    "CL=F": "WTI 원유",
}


@st.cache_data(ttl=3600)
def search_naver_stock_code(name: str) -> str:
    """한글 종목명으로 네이버 금융 검색을 통해 6자리 티커 코드 또는 미국 주식 티커 찾기."""
    import requests
    import urllib.parse
    import re
    from bs4 import BeautifulSoup
    try:
        url = f"https://finance.naver.com/search/search.naver?query={urllib.parse.quote(name.encode('euc-kr'))}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=3)
        
        # 1. URL 리다이렉트 (정확히 일치하는 경우 바로 종목 페이지로 이동)
        if 'code=' in res.url:
            match = re.search(r'code=(\d{6})', res.url)
            if match:
                return f"{match.group(1)}.KS"
            if 'symbol=' in res.url:
                match = re.search(r'symbol=([A-Za-z0-9\-\.]+)', res.url)
                if match:
                    return match.group(1).upper()

        # JS 리다이렉트 (HTML 내 스크립트로 리다이렉트 하는 경우)
        match = re.search(r"<SCRIPT>parent\.location\.href='/item/main\.naver\?code=(\d{6})';</SCRIPT>", res.text, re.IGNORECASE)
        if match:
            return f"{match.group(1)}.KS"

            match_us = re.search(r"<SCRIPT>parent\.location\.href='/world/item/main\.naver\?symbol=([A-Za-z0-9\-\.]+)';</SCRIPT>", res.text, re.IGNORECASE)
            if match_us:
                return match_us.group(1).upper()

        # 2. 검색 결과 목록 페이지 파싱
        soup = BeautifulSoup(res.text, 'html.parser')
        links = soup.select('td.tit > a')
        target_name = name.replace(' ', '').lower()
        
        # 1순위: 검색어와 종목명이 정확히 일치하는 결과 우선 탐색
        for l in links:
            text = l.text.strip().replace(' ', '').lower()
            href = l.get('href', '')
            if text == target_name:
                m_kr = re.search(r'code=(\d{6})', href)
                if m_kr:
                    return f"{m_kr.group(1)}.KS"
                m_us = re.search(r'symbol=([A-Za-z0-9\-\.]+)', href)
                if m_us:
                    return m_us.group(1).upper()
                    
        # 2순위: 정확히 일치하지 않더라도 가장 처음 검색된 결과 반환 (검색 유연성 확대)
        if links:
            for l in links:
                href = l.get('href', '')
                m_kr = re.search(r'code=(\d{6})', href)
                if m_kr:
                    return f"{m_kr.group(1)}.KS"
                m_us = re.search(r'symbol=([A-Za-z0-9\-\.]+)', href)
                if m_us:
                    return m_us.group(1).upper()
            
    except Exception:
        pass
    return ""


def normalize_ticker(user_input: str) -> str:
    """사용자 입력을 yfinance용 티커로 정규화."""
    if not user_input:
        return ""
    raw = user_input.strip()
    if not raw:
        return ""

    key = raw.replace(" ", "")
    lower = key.lower()

    # 한글/별칭 매핑 우선
    if key in KOREAN_TICKER_MAP:
        return KOREAN_TICKER_MAP[key]
    if lower in KOREAN_TICKER_MAP:
        return KOREAN_TICKER_MAP[lower]

    # "KODEX 미국나스닥100(H) 449190" 같이 숫자 코드가 포함된 입력 처리
    m = re.search(r"(\d{6})", key)
    if m:
        return f"{m.group(1)}.KS"

    # 알파벳/숫자만 있고 . 이 없으면 미국 종목으로 보고 대문자
    if "." not in key and all(ord(c) < 128 for c in key):
        return key.upper()

    # 한글이 포함된 경우 네이버 검색 시도
    if re.search(r'[가-힣]', key):
        code = search_naver_stock_code(key)
        if code:
            return code

    # 그 외는 그대로 사용 (이미 .KS / .KQ 등이 붙은 경우 등)
    return key


def ticker_candidates(user_input: str) -> List[str]:
    """입력값으로 시도할 티커 후보 목록 생성."""
    base = normalize_ticker(user_input)
    if not base:
        return []

    cands = [base]
    # 6자리 숫자 코드는 .KS/.KQ를 순차 시도
    pure = re.sub(r"\D", "", user_input or "")
    if len(pure) != 6:
        pure = re.sub(r"\D", "", base or "")
        
    if len(pure) == 6:
        for s in [f"{pure}.KS", f"{pure}.KQ"]:
            if s not in cands:
                cands.append(s)
    return cands


# -----------------------------
# 유틸 함수들
# -----------------------------

@st.cache_data(ttl=300)
def fetch_price_history(ticker: str, start: dt.date, end: dt.date) -> pd.DataFrame:
    """yfinance로 가격 데이터 가져오기 (일봉 종가 기준)."""
    for cand in ticker_candidates(ticker):
        try:
            data = yf.download(
                cand,
                start=start,
                end=end,
                interval="1d",
                auto_adjust=True,
                progress=False,
            )
        except Exception:
            continue
            
        if data.empty:
            continue

        # yfinance 버전에 따라 단일 티커도 MultiIndex 컬럼일 수 있음.
        close_series = None
        if "Close" in data.columns:
            close_series = data["Close"]
        elif isinstance(data.columns, pd.MultiIndex):
            for col in data.columns:
                if col[0] == "Close":
                    close_series = data[col]
                    break

        if close_series is not None:
            if isinstance(close_series, pd.Series):
                close_df = close_series.to_frame(name="close")
            elif isinstance(close_series, pd.DataFrame):
                close_df = close_series.iloc[:, [0]].copy()
                close_df.columns = ["close"]
            else:
                close_df = pd.DataFrame({"close": close_series}, index=data.index)
            return close_df.dropna()
    return pd.DataFrame()


@st.cache_data(ttl=60)
def fetch_latest_quote(ticker: str) -> Dict:
    """현재가 및 전일 대비 정보 (실시간)."""
    for cand in ticker_candidates(ticker):
        ticker_obj = yf.Ticker(cand)
        
        # 1. fast_info를 통한 실시간 가격 조회 시도
        try:
            f_info = ticker_obj.fast_info
            latest = float(f_info['lastPrice'])
            prev = float(f_info['previousClose'])
            if latest > 0 and prev > 0:
                change = latest - prev
                change_pct = (change / prev * 100)
                return {
                    "symbol": cand,
                    "price": latest,
                    "change": change,
                    "change_pct": change_pct,
                }
        except Exception:
            pass

        # 2. 실패시 history를 통한 일봉 데이터 조회 (대체 수단)
        try:
            # 일부 한국 ETF/종목은 2일 데이터가 비어오는 경우가 있어 기간을 넉넉히 조회
            info = ticker_obj.history(period="1mo", interval="1d", auto_adjust=True)
        except Exception:
            continue
        if info.empty or "Close" not in info.columns:
            continue
        close = info["Close"].dropna()
        if close.empty:
            continue
        latest = float(close.iloc[-1])
        prev = float(close.iloc[-2]) if len(close) > 1 else latest
        change = latest - prev
        change_pct = (change / prev * 100) if prev != 0 else 0.0
        return {
            "symbol": cand,
            "price": latest,
            "change": change,
            "change_pct": change_pct,
        }
    return {}


def get_naver_stock_name(ticker: str) -> str:
    """네이버 금융에서 한글 종목명을 가져옵니다."""
    pure_code = re.sub(r"\D", "", str(ticker))
    if len(pure_code) != 6:
        return ""
    try:
        import requests
        from bs4 import BeautifulSoup
        url = f"https://finance.naver.com/item/main.naver?code={pure_code}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=3)
        soup = BeautifulSoup(res.text, "html.parser")
        name_tag = soup.select_one("div.wrap_company h2 a")
        if name_tag:
            return name_tag.text.strip()
    except Exception:
        pass
    return ""

@st.cache_data(ttl=3600)
def fetch_symbol_name(ticker: str) -> str:
    """가능하면 사람이 읽기 쉬운 종목명 반환 (한국=종목명, 미국=티커)."""
    norm = normalize_ticker(ticker)
    if not norm:
        return ticker
        
    if norm.upper() in DISPLAY_NAME_MAP:
        return DISPLAY_NAME_MAP[norm.upper()]
        
    # 한국 종목(6자리 숫자)인 경우 네이버에서 조회
    if re.search(r"\d{6}", norm):
        kr_name = get_naver_stock_name(norm)
        if kr_name:
            return kr_name
            
    # 그 외(주로 미국 주식)는 티커 앞부분만 반환
    return norm.split('.')[0] if norm else ticker


def compute_cumulative_return(prices: pd.Series) -> pd.Series:
    """누적 수익률 (첫날을 0% 기준)."""
    if prices.empty:
        return prices
    return prices / prices.iloc[0] - 1.0


def compute_drawdown(prices: pd.Series) -> pd.Series:
    """드로우다운 시계열 계산."""
    if prices.empty:
        return prices
    running_max = prices.cummax()
    drawdown = prices / running_max - 1.0
    return drawdown


def calculate_c_indicator(raw_ticker: str = "^NDX") -> dict:
    """CI 지수 계산"""
    norm_ticker = normalize_ticker(raw_ticker)
    if not norm_ticker:
        return {"error": "올바른 종목을 입력해주세요."}
    display_name = fetch_symbol_name(norm_ticker)
    
    data = yf.download(norm_ticker, period="max", progress=False)
    
    if not data.empty:
        start_date = data.index[0].date()
    else:
        start_date = dt.date.today()
    if data.empty or "Close" not in data.columns:
        return {"error": f"'{display_name}' ({norm_ticker}) 데이터를 불러올 수 없습니다."}
        
    close = data["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close = close.dropna()
    
    if len(close) < 2:
        return {"error": "데이터가 충분하지 않습니다."}

    log_returns = np.log(close / close.shift(1)).dropna()
    sigma = float(log_returns.std())
    
    t_array = np.arange(1, len(close) + 1)
    log_prices = np.log(close.values)
    slope, intercept, r_value, p_value, std_err = stats.linregress(t_array, log_prices)
    residuals = log_prices - (intercept + slope * t_array)
    sigma_reg = float(np.std(residuals))

    # 사용자의 지적대로 첫 날의 가격(폭락/폭등장일 수 있음)을 기준(S0)으로 잡는 오류를 방지하기 위해,
    # 30년 전체의 '중앙 추세선'이 가리키는 이론적 시작점(Fitted S0)을 복리 시뮬레이션의 기준일로 설정합니다.
    S0 = float(np.exp(intercept))
    # 추세선(Median)과의 오차를 없애기 위해 기하평균수익률(mu)도 회귀 기울기(slope)로 일치시킵니다.
    mu = float(slope)

    current_price = float(close.iloc[-1])
    t = len(close)
    
    # 몬테카를로 시뮬레이션 대신 수학적 엄밀해(정규분포 CDF)를 사용하여 오차 제거 및 속도 최적화
    median_price = float(S0 * np.exp(mu * t))
    Z_current = (np.log(current_price / S0) - mu * t) / (sigma * np.sqrt(t))
    percentile = float(stats.norm.cdf(Z_current) * 100)
    ci_val = 100.0 - percentile
    
    if ci_val <= 25:
        status = "초고위험"
        color = "#d32f2f"
    elif ci_val <= 37.5:
        status = "지나친 고평가 구간"
        color = "#ef5350"
    elif ci_val <= 45:
        status = "약간의 고평가 구간"
        color = "#e57373"
    elif ci_val <= 55:
        status = "확률상 적정범위"
        color = "#2e7d32"
    elif ci_val <= 62.5:
        status = "약간의 저평가 구간"
        color = "#64b5f6"
    elif ci_val <= 75:
        status = "지나친 저평가 구간"
        color = "#1e88e5"
    else:
        status = "초저평가"
        color = "#1976d2"
        
    t_fut = t + 21
    gbm_fut = S0 * np.exp(mu * t_fut)
    reg_fut = np.exp(intercept + slope * t_fut)
        
    t_future = np.log(current_price / S0) / mu
    wait_years = float((t_future - t) / 252.0) # 1년을 252 거래일로 가정

    return {
        "display_name": display_name,
        "norm_ticker": norm_ticker,
        "current_price": current_price,
        "median_price": median_price,
        "percentile": percentile,
        "ci_val": ci_val,
        "status": status,
        "color": color,
        "S0": S0,
        "mu": mu,
        "sigma": sigma,
        "t": int(t),
        "start_date": start_date,
        "slope": float(slope),
        "intercept": float(intercept),
        "sigma_reg": sigma_reg,
        "reg_fut": float(reg_fut),
        "wait_years": wait_years
    }


def format_change_text(change: float, change_pct: float) -> str:
    arrow = "▲" if change > 0 else "▼" if change < 0 else "-"
    return f"{arrow} {change:,.2f} ({change_pct:+.2f}%)"


def is_korean_listed_ticker(ticker: str) -> bool:
    """코스피/코스닥 등 한국 상장으로 간주 (yfinance 티커 규칙)."""
    t = ticker.upper()
    return t.endswith(".KS") or t.endswith(".KQ")


def infer_tax_type(ticker: str, display_name: str = "") -> str:
    """yfinance 정보와 종목명을 기반으로 세금 유형을 자동 추론합니다."""
    kr = is_korean_listed_ticker(ticker)
    if not kr:
        return "미국직투(22%)"
        
    try:
        # fast_info is faster but doesn't have quoteType. We need info.
        info = yf.Ticker(ticker).info
        q_type = info.get('quoteType', 'EQUITY')
    except Exception:
        q_type = 'EQUITY'
        
    if q_type == 'ETF':
        name_lower = display_name.lower()
        # 해외 지수나 자산 추종 ETF 키워드
        overseas_keywords = ['미국', '나스닥', 's&p', '글로벌', '차이나', '인도', '베트남', '유로', '일본', '항셍', '다우']
        if any(kw in name_lower for kw in overseas_keywords):
            return "해외ETF(15.4%)"
        return "국내주식(비과세)"
        
    return "국내주식(비과세)"


def fmt_dollar(value: float) -> str:
    return f"{value:,.2f} 달러"


def _cell(text: str, *, align: str = "right", color: str = "#111827", weight: int = 400) -> str:
    """보유자산 표 셀: 높이·정렬 통일."""
    safe = html.escape(str(text))
    return (
        f"<div style='min-height:44px;display:flex;align-items:center;justify-content:{align};"
        f"font-size:0.95rem;line-height:1.25;color:{color};font-weight:{weight};'>{safe}</div>"
    )


def _hdr(text: str, *, align: str = "center") -> str:
    safe = html.escape(str(text))
    return (
        f"<div style='min-height:24px;display:flex;align-items:center;justify-content:{align};"
        f"font-size:0.82rem;color:#6b7280;font-weight:600;letter-spacing:0.02em;'>{safe}</div>"
    )


def _input_like_box(text: str, *, align: str = "right", color: str = "#111827", weight: int = 400) -> str:
    safe = html.escape(str(text))
    return (
        "<div style='height:38px;display:block;line-height:36px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;"
        f"text-align:{align};padding:0 10px;border:1px solid #d1d5db;border-radius:8px;"
        f"background:#f8fafc;font-size:0.95rem;color:{color};font-weight:{weight};' title='{safe}'>{safe}</div>"
    )


# -----------------------------
# 레이아웃 / 컴포넌트 함수들
# -----------------------------

def render_market_dashboard():
    st.markdown("### 📈 주요 시장 지표")

    indices = [
        ("^GSPC", "S&P 500"),
        ("^NDX", "NASDAQ 100"),
        ("NQ=F", "NASDAQ 100 선물"),
        ("^KS11", "KOSPI"),
        ("^KQ11", "KOSDAQ"),
        ("USDKRW=X", "원/달러 환율"),
        ("GC=F", "금 (Gold)"),
        ("CL=F", "WTI 원유"),
    ]

    cols = st.columns(4)
    for idx, (ticker, name) in enumerate(indices):
        quote = fetch_latest_quote(ticker)
        col = cols[idx % 4]
        with col:
            with st.container(border=True):
                if not quote:
                    st.markdown(f"<div style='font-size:0.875rem; color:#6b7280; font-weight:600;'>{name}</div>", unsafe_allow_html=True)
                    st.markdown("<div style='font-size:1.5rem; font-weight:700;'>데이터 없음</div>", unsafe_allow_html=True)
                else:
                    price = quote["price"]
                    change = quote["change"]
                    change_pct = quote["change_pct"]
                    
                    if ticker == "USDKRW=X":
                        price_str = f"{price:,.2f}원"
                    elif ticker in ["GC=F", "CL=F"]:
                        price_str = f"${price:,.2f}"
                    elif ticker == "NQ=F":
                        price_str = f"{price:,.2f}"
                    else:
                        price_str = f"{price:,.2f}"
                        
                    color = "#d32f2f" if change > 0 else "#1976d2" if change < 0 else "gray"
                    arrow = "▲" if change > 0 else "▼" if change < 0 else "-"
                    
                    st.markdown(f"<div style='font-size:0.875rem; color:#6b7280; font-weight:600;'>{name}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size:1.5rem; font-weight:700;'>{price_str}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size:1rem; font-weight:600; color:{color};'>{arrow} {abs(change):,.2f} ({change_pct:+.2f}%)</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)


@st.fragment
def render_portfolio_section():
    st.markdown("### 💰 실시간 내 자산 요약")
    st.caption("보유 자산을 입력하면 현재가와 수익률을 실시간으로 확인하고, 전체 자산의 원화 기준 합계를 계산해 줍니다.")

    fx_q = fetch_latest_quote("USDKRW=X")
    usd_krw = float(fx_q["price"]) if fx_q else 0.0

    if "portfolio_cards" not in st.session_state:
        import uuid
        loaded = load_portfolio()
        if loaded is not None:
            st.session_state.portfolio_cards = loaded
        else:
            st.session_state.portfolio_cards = [
                {"id": str(uuid.uuid4()), "종목": "QQQ", "평단가": 200.0, "수량": 10.0, "buy_fx": usd_krw if usd_krw > 0 else 1300.0}
            ]

    # Input Section
    with st.container(border=True):
        st.markdown("#### 📝 보유 자산 입력")
        
        next_cards = []
        delete_index = None

        for i, item in enumerate(st.session_state.portfolio_cards):
            card_id = item.get("id")
            if not card_id:
                import uuid
                card_id = str(uuid.uuid4())
                item["id"] = card_id

            cols = st.columns([2, 3, 2, 2, 1])
            with cols[0]:
                if i == 0:
                    st.markdown("<div style='font-size:0.875rem; color:#6b7280; font-weight:600; margin-bottom:5px;'>별명(선택)</div>", unsafe_allow_html=True)
                nickname = st.text_input(
                    "별명",
                    value=str(item.get("별명", "")),
                    key=f"card_nick_{card_id}",
                    placeholder="예: 내 연금",
                    label_visibility="collapsed"
                )
            with cols[1]:
                if i == 0:
                    st.markdown("<div style='font-size:0.875rem; color:#6b7280; font-weight:600; margin-bottom:5px;'>종목</div>", unsafe_allow_html=True)
                raw_symbol = st.text_input(
                    "종목",
                    value=str(item.get("종목", "")),
                    key=f"card_symbol_{card_id}",
                    placeholder="예: QQQ, 삼성전자",
                    label_visibility="collapsed"
                )
                
            with cols[2]:
                if i == 0:
                    st.markdown("<div style='font-size:0.875rem; color:#6b7280; font-weight:600; margin-bottom:5px;'>평단가</div>", unsafe_allow_html=True)
                avg = st.number_input(
                    "평단가",
                    min_value=0.0,
                    value=float(item.get("평단가", 0.0)),
                    step=0.1,
                    format="%g",
                    key=f"card_avg_{card_id}",
                    label_visibility="collapsed"
                )
            with cols[3]:
                if i == 0:
                    st.markdown("<div style='font-size:0.875rem; color:#6b7280; font-weight:600; margin-bottom:5px;'>수량</div>", unsafe_allow_html=True)
                qty = st.number_input(
                    "수량",
                    min_value=0.0,
                    value=float(item.get("수량", 0.0)),
                    step=1.0,
                    format="%g",
                    key=f"card_qty_{card_id}",
                    label_visibility="collapsed"
                )
            with cols[4]:
                if i == 0:
                    st.markdown("<div style='font-size:0.875rem; color:#6b7280; font-weight:600; margin-bottom:5px;'>&nbsp;</div>", unsafe_allow_html=True)
                if st.button("삭제", key=f"card_del_{card_id}", use_container_width=True):
                    delete_index = i
            
            prev_symbol = str(item.get("종목", "") or "")
            prev_buy_fx = float(item.get("buy_fx", usd_krw if usd_krw > 0 else 1300.0))
            norm_prev = normalize_ticker(prev_symbol)
            norm_now = normalize_ticker(raw_symbol)
            buy_fx = prev_buy_fx
            if norm_now and norm_now != norm_prev and usd_krw > 0:
                buy_fx = usd_krw

            next_cards.append({"id": card_id, "별명": nickname, "종목": raw_symbol, "평단가": float(avg), "수량": float(qty), "buy_fx": buy_fx})
        
        if delete_index is not None:
            deleted_card = next_cards.pop(delete_index)
            for key in [f"card_nick_{deleted_card['id']}", f"card_symbol_{deleted_card['id']}", f"card_tax_{deleted_card['id']}", f"card_avg_{deleted_card['id']}", f"card_qty_{deleted_card['id']}", f"card_del_{deleted_card['id']}"]:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.session_state.portfolio_cards = next_cards
            save_portfolio(next_cards)
            st.rerun()

        if st.session_state.portfolio_cards != next_cards:
            st.session_state.portfolio_cards = next_cards
            save_portfolio(next_cards)

        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        
        # Add & Clear Buttons
        btn_cols = st.columns([2, 2, 6])
        with btn_cols[0]:
            if st.button("➕ 자산 추가", use_container_width=True):
                import uuid
                st.session_state.portfolio_cards.append(
                    {"id": str(uuid.uuid4()), "별명": "", "종목": "", "평단가": 0.0, "수량": 0.0, "buy_fx": usd_krw if usd_krw > 0 else 1300.0}
                )
                save_portfolio(st.session_state.portfolio_cards)
                st.rerun()
        with btn_cols[1]:
            if st.button("🗑️ 전체 삭제", use_container_width=True):
                for card in st.session_state.portfolio_cards:
                    card_id = card.get("id")
                    for key in [f"card_nick_{card_id}", f"card_symbol_{card_id}", f"card_tax_{card_id}", f"card_avg_{card_id}", f"card_qty_{card_id}", f"card_del_{card_id}"]:
                        if key in st.session_state:
                            del st.session_state[key]
                st.session_state.portfolio_cards = []
                save_portfolio([])
                st.rerun()

    if not st.session_state.portfolio_cards:
        st.info("자산이 없습니다. `자산 추가` 버튼으로 자산을 등록해 주세요.")
        return

    # Process and Summary Section
    rows = [(c["id"], c.get("별명", "").strip(), c["종목"].strip(), c["평단가"], c["수량"], c["buy_fx"]) for c in st.session_state.portfolio_cards if c["종목"].strip() and c["평단가"] > 0 and c["수량"] > 0]

    if not rows:
        st.info("종목 이름, 평단가, 수량을 올바르게 입력해 주세요.")
        return

    if usd_krw <= 0:
        st.warning("원/달러 환율(USDKRW)을 가져오지 못했습니다. 미국 자산의 원화 환산·총합이 부정확할 수 있습니다.")

    sum_cost_krw = 0.0
    sum_value_krw = 0.0
    sum_us_profit_krw = 0.0
    total_tax_krw = 0.0
    asset_results = []
    error_messages = []

    for card_id, nickname, raw, avg, qty, buy_fx in rows:
        sym = normalize_ticker(raw)
        quote = fetch_latest_quote(sym) if sym else {}
        if not quote:
            error_messages.append(raw)
            continue

        resolved_symbol = quote.get("symbol", sym)
        display_name = fetch_symbol_name(resolved_symbol)
        if nickname:
            display_name = f"{nickname} - {display_name}"
        
        user_tax_type = st.session_state.get(f"card_tax_override_{card_id}", "자동 추론")
        actual_tax_type = infer_tax_type(resolved_symbol, display_name) if user_tax_type == "자동 추론" else user_tax_type

        cur = float(quote["price"])
        kr = is_korean_listed_ticker(resolved_symbol)

        cost_native = avg * qty
        val_native = cur * qty
        pnl_native = val_native - cost_native
        
        if kr:
            cost_krw = cost_native
            val_krw = val_native
            pnl_krw = pnl_native
        else:
            buy_fx_eff = buy_fx if buy_fx > 0 else usd_krw
            cost_krw = cost_native * buy_fx_eff
            val_krw = val_native * usd_krw
            pnl_krw = val_krw - cost_krw

        sum_cost_krw += cost_krw
        sum_value_krw += val_krw
        
        indiv_tax = 0.0
        if actual_tax_type == "해외ETF(15.4%)" and pnl_krw > 0:
            indiv_tax = pnl_krw * 0.154
            total_tax_krw += indiv_tax
        elif actual_tax_type == "미국직투(22%)":
            sum_us_profit_krw += pnl_krw
            
        asset_results.append({
            "name": display_name,
            "kr": kr,
            "avg": avg,
            "qty": qty,
            "cur": cur,
            "val_krw": val_krw,
            "pnl_krw": pnl_krw,
            "pnl_pct": (pnl_krw / cost_krw * 100) if cost_krw else 0.0,
            "tax_type": actual_tax_type,
            "indiv_tax": indiv_tax,
            "card_id": card_id
        })

    if error_messages:
        for err in error_messages:
            st.warning(f"'{err}': 가격 데이터를 가져오지 못했습니다. 종목 이름이나 코드를 확인해 주세요.")

    if not asset_results:
        return

    # Calculate US tax
    us_tax = (sum_us_profit_krw - 2500000) * 0.22 if sum_us_profit_krw > 2500000 else 0.0
    
    apply_tax = st.session_state.get("port_apply_tax", True)
    if apply_tax:
        total_tax_krw += us_tax
    else:
        total_tax_krw = 0.0

    # Portfolio Summary Display
    total_pnl_krw = sum_value_krw - sum_cost_krw
    total_pct = (total_pnl_krw / sum_cost_krw * 100) if sum_cost_krw > 0 else 0.0
    
    total_after_tax_pnl = total_pnl_krw - total_tax_krw
    total_after_tax_pct = (total_after_tax_pnl / sum_cost_krw * 100) if sum_cost_krw > 0 else 0.0

    st.markdown("<br>", unsafe_allow_html=True)
    hdr_c1, hdr_c2 = st.columns([3, 1])
    with hdr_c1:
        st.markdown("#### 📊 내 포트폴리오 결과 요약")
    with hdr_c2:
        st.checkbox("세금 계산 적용", value=apply_tax, key="port_apply_tax")
    
    color = "#d32f2f" if total_after_tax_pnl > 0 else "#1976d2" if total_after_tax_pnl < 0 else "inherit"
    with st.container(border=True):
        if apply_tax:
            display_eval_krw = sum_value_krw - total_tax_krw
            st.markdown(f"<div style='font-size:1.1rem; color:#6b7280; font-weight:600; margin-bottom:10px;'>총 평가 자산 (세후 원화 기준)</div>", unsafe_allow_html=True)
            t_c1, t_c2, t_c3, t_c4, t_c5 = st.columns(5)
            with t_c1:
                st.markdown(f"<div style='font-size:0.9rem; color:#6b7280;'>총 매수 금액</div><div style='font-size:1.4rem; font-weight:700;'>{sum_cost_krw:,.0f}원</div>", unsafe_allow_html=True)
            with t_c2:
                st.markdown(f"<div style='font-size:0.9rem; color:#6b7280;'>총 평가 금액</div><div style='font-size:1.4rem; font-weight:700;'>{display_eval_krw:,.0f}원</div>", unsafe_allow_html=True)
            with t_c3:
                p_color = "#d32f2f" if total_pnl_krw > 0 else "#1976d2" if total_pnl_krw < 0 else "inherit"
                st.markdown(f"<div style='font-size:0.9rem; color:#6b7280;'>세전 수익금</div><div style='font-size:1.4rem; font-weight:700; color:{p_color};'>{total_pnl_krw:+,.0f}원 ({total_pct:+.2f}%)</div>", unsafe_allow_html=True)
            with t_c4:
                tax_str = f"-{total_tax_krw:,.0f}원" if total_tax_krw > 0 else "0원"
                st.markdown(f"<div style='font-size:0.9rem; color:#6b7280;'>예상 세금</div><div style='font-size:1.4rem; font-weight:700; color:#eab308;'>{tax_str}</div>", unsafe_allow_html=True)
            with t_c5:
                st.markdown(f"<div style='font-size:0.9rem; color:#6b7280;'>세후 수익금</div><div style='font-size:1.4rem; font-weight:700; color:{color};'>{total_after_tax_pnl:+,.0f}원 ({total_after_tax_pct:+.2f}%)</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='font-size:1.1rem; color:#6b7280; font-weight:600; margin-bottom:10px;'>총 평가 자산 (원화 기준)</div>", unsafe_allow_html=True)
            t_c1, t_c2, t_c3, t_c4 = st.columns(4)
            with t_c1:
                st.markdown(f"<div style='font-size:0.9rem; color:#6b7280;'>총 매수 금액</div><div style='font-size:1.4rem; font-weight:700;'>{sum_cost_krw:,.0f}원</div>", unsafe_allow_html=True)
            with t_c2:
                st.markdown(f"<div style='font-size:0.9rem; color:#6b7280;'>총 평가 금액</div><div style='font-size:1.4rem; font-weight:700;'>{sum_value_krw:,.0f}원</div>", unsafe_allow_html=True)
            with t_c3:
                st.markdown(f"<div style='font-size:0.9rem; color:#6b7280;'>총 수익금</div><div style='font-size:1.4rem; font-weight:700; color:{color};'>{total_pnl_krw:+,.0f}원</div>", unsafe_allow_html=True)
            with t_c4:
                st.markdown(f"<div style='font-size:0.9rem; color:#6b7280;'>총 수익률</div><div style='font-size:1.4rem; font-weight:700; color:{color};'>{total_pct:+.2f}%</div>", unsafe_allow_html=True)

    if usd_krw > 0:
        st.caption(f"적용 환율: 1 USD = {usd_krw:,.2f} KRW (자산별 매수 시점 환율 별도 적용) | 미국직투 합산 수익금: {sum_us_profit_krw:,.0f}원 (250만원 공제 대상)")

    if asset_results:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### 개별 자산 상세")
        for res in asset_results:
            p_color = "#d32f2f" if res['pnl_krw'] > 0 else "#1976d2" if res['pnl_krw'] < 0 else "inherit"
            with st.container(border=True):
                asset_tax = 0.0
                if apply_tax:
                    if res['tax_type'] == "해외ETF(15.4%)":
                        asset_tax = res['indiv_tax'] if res['indiv_tax'] > 0 else 0.0
                    elif res['tax_type'] == "미국직투(22%)":
                        asset_tax = res['pnl_krw'] * 0.22 if res['pnl_krw'] > 0 else 0.0
                    elif res['tax_type'] == "ISA(9.9%)":
                        asset_tax = res['pnl_krw'] * 0.099 if res['pnl_krw'] > 0 else 0.0

                after_tax_pnl = res['pnl_krw'] - asset_tax
                after_tax_val_krw = res['val_krw'] - asset_tax

                if apply_tax:
                    d_c1, d_c2, d_c3, d_c4, d_c5 = st.columns([2.5, 1, 1, 1, 1])
                else:
                    d_c1, d_c2, d_c3, d_c4 = st.columns([2.5, 1, 1, 1])
                    
                with d_c1:
                    type_badge = "🇰🇷 한국" if res['kr'] else "🇺🇸 미국"
                    with st.container():
                        html = f"""
                        <div class="tax-badge-row" style='display:flex; align-items:center; gap:8px; height: 28px; width:100%; min-width:0;'>
                            <div style='flex: 0 1 auto; min-width: 0; font-weight:700; font-size:1.05rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; line-height: normal; padding-top: 2px;' title='{res['name']}'>{res['name']}</div>
                            <div style='flex-shrink:0; font-size:0.75rem; background:#e5e7eb; padding:0 6px; border-radius:4px; white-space:nowrap; display:flex; align-items:center; justify-content:center; height:22px; color:#374151; font-weight:600;'>{type_badge}</div>
                        </div>
                        """
                        st.markdown(html, unsafe_allow_html=True)
                        if apply_tax:
                            tax_options = ["미국직투(22%)", "해외ETF(15.4%)", "국내주식(비과세)", "ISA(9.9%)"]
                            st.selectbox("세금 유형", tax_options, index=tax_options.index(res['tax_type']) if res['tax_type'] in tax_options else 0, key=f"card_tax_override_{res['card_id']}", label_visibility="collapsed")
                    
                    if res['kr']:
                        st.markdown(f"<div style='font-size:0.85rem; color:#6b7280; margin-top: 4px;'>평단가 {res['avg']:,.0f}원 / 현재가 {res['cur']:,.0f}원 / {res['qty']:g}주</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='font-size:0.85rem; color:#6b7280; margin-top: 4px;'>평단가 ${res['avg']:,.2f} / 현재가 ${res['cur']:,.2f} / {res['qty']:g}주</div>", unsafe_allow_html=True)
                with d_c2:
                    if apply_tax:
                        st.markdown(f"<div style='font-size:0.85rem; color:#6b7280; text-align:right;'>세후 평가액 (원화)</div><div style='font-size:1.1rem; font-weight:600; text-align:right;'>{after_tax_val_krw:,.0f}원</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='font-size:0.85rem; color:#6b7280; text-align:right;'>평가액 (원화)</div><div style='font-size:1.1rem; font-weight:600; text-align:right;'>{res['val_krw']:,.0f}원</div>", unsafe_allow_html=True)
                with d_c3:
                    if apply_tax:
                        st.markdown(f"<div style='font-size:0.85rem; color:#6b7280; text-align:right;'>세전 수익금</div><div style='font-size:1.1rem; font-weight:600; color:{p_color}; text-align:right;'>{res['pnl_krw']:+,.0f}원</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='font-size:0.85rem; color:#6b7280; text-align:right;'>총 수익금</div><div style='font-size:1.1rem; font-weight:600; color:{p_color}; text-align:right;'>{res['pnl_krw']:+,.0f}원</div>", unsafe_allow_html=True)
                
                if apply_tax:
                    with d_c4:
                        tax_str = f"-{asset_tax:,.0f}원" if asset_tax > 0 else "0원"
                        st.markdown(f"<div style='font-size:0.85rem; color:#6b7280; text-align:right;'>예상 세금</div><div style='font-size:1.1rem; font-weight:600; color:#eab308; text-align:right;'>{tax_str}</div>", unsafe_allow_html=True)
                    with d_c5:
                        after_tax_pct = (after_tax_pnl / (res['val_krw'] - res['pnl_krw']) * 100) if (res['val_krw'] - res['pnl_krw']) > 0 else 0.0
                        a_color = "#d32f2f" if after_tax_pnl > 0 else "#1976d2" if after_tax_pnl < 0 else "inherit"
                        st.markdown(f"<div style='font-size:0.85rem; color:#6b7280; text-align:right;'>세후 수익률</div><div style='font-size:1.1rem; font-weight:600; color:{a_color}; text-align:right;'>{after_tax_pct:+.2f}%</div>", unsafe_allow_html=True)
                else:
                    with d_c4:
                        st.markdown(f"<div style='font-size:0.85rem; color:#6b7280; text-align:right;'>총 수익률</div><div style='font-size:1.1rem; font-weight:600; color:{p_color}; text-align:right;'>{res['pnl_pct']:+.2f}%</div>", unsafe_allow_html=True)


def run_comparison_analysis(tickers_in: List[str], start_date: dt.date, end_date: dt.date) -> None:
    valid_raw_tickers = [t.strip() for t in tickers_in if t.strip()]
    if not valid_raw_tickers:
        return

    if start_date >= end_date:
        st.error("시작일은 종료일보다 빠른 날짜여야 합니다.")
        return

    series_list = []
    col_to_symbol = {}
    
    for raw_t in valid_raw_tickers:
        sym = normalize_ticker(raw_t)
        if not sym:
            continue
            
        # 보유자산과 동일하게 현재가 조회를 통해 정확한 심볼과 이름 확보
        quote = fetch_latest_quote(sym)
        resolved_symbol = quote.get("symbol", sym) if quote else sym
        display_name = fetch_symbol_name(resolved_symbol)
        
        # 이름 조회가 안된 경우 입력값 기반으로 폴백
        if not display_name or display_name == resolved_symbol:
            if re.match(r'^[a-zA-Z]+$', raw_t):
                display_name = raw_t.upper()
            else:
                display_name = resolved_symbol

        # 중복된 이름 처리
        col_name = display_name
        counter = 1
        while any(s.name == col_name for s in series_list):
            col_name = f"{display_name} ({counter})"
            counter += 1

        data = fetch_price_history(resolved_symbol, start_date, end_date)
        if data.empty:
            st.warning(f"'{raw_t}' ({resolved_symbol}): 가격 데이터를 가져오지 못했습니다.")
            continue
            
        s = data["close"].rename(col_name)
        series_list.append(s)
        col_to_symbol[col_name] = resolved_symbol

    if not series_list:
        st.error("가져온 가격 데이터가 없습니다. 종목 이름이나 코드를 확인해 주세요.")
        return
    # 날짜 정렬 및 병합 (pandas 3.0 호환)
    price_df = pd.concat(series_list, axis=1).sort_index()

    # 누적 수익률 계산
    cumret_df = pd.DataFrame(
        {col: compute_cumulative_return(price_df[col].dropna()) for col in price_df.columns}
    )

    # MDD 계산
    dd_df = pd.DataFrame(
        {col: compute_drawdown(price_df[col].dropna()) for col in price_df.columns}
    )

    # ---------------- 누적 수익률 그래프 ----------------
    ret_fig = go.Figure()
    final_rets = []
    DEFAULT_COLORS = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692']
    for idx, col in enumerate(cumret_df.columns):
        series = cumret_df[col].dropna()
        if series.empty:
            continue
        final_ret = series.iloc[-1] * 100
        line_color = DEFAULT_COLORS[idx % len(DEFAULT_COLORS)]
        final_rets.append((col, final_ret, line_color))
        
        y_vals = series.values * 100
        custom_text = [f"<span style=\"color:{'#d32f2f' if v > 0 else '#1976d2' if v < 0 else 'inherit'}\">{v:+.2f}%</span>" for v in y_vals]
        
        ret_fig.add_trace(
            go.Scatter(
                x=series.index,
                y=y_vals,
                mode="lines",
                name=col,
                line=dict(color=line_color),
                customdata=custom_text,
                hovertemplate=f'{col}: %{{customdata}}<extra></extra>',
            )
        )
    ret_fig.update_layout(
        title="누적 수익률 비교",
        xaxis_title=None,
        xaxis_hoverformat="%Y-%m-%d",
        yaxis_title="누적 수익률 (%)",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
        showlegend=True # 단일 종목일 때도 범례 표시
    )
    st.plotly_chart(ret_fig, use_container_width=True)

    if final_rets:
        st.markdown("#### 📈 종목별 최종 누적 수익률")
        cols = st.columns(len(final_rets))
        for col_idx, (col, ret, line_color) in enumerate(final_rets):
            color = "#d32f2f" if ret > 0 else "#1976d2" if ret < 0 else "inherit"
            with cols[col_idx]:
                with st.container(border=True):
                    st.markdown(f"**<span style='color:{line_color};'>■</span> {col}**", unsafe_allow_html=True)
                    st.markdown(f"<h3 style='color: {color}; margin-top: 0; padding-top: 0;'>{ret:+.2f}%</h3>", unsafe_allow_html=True)

    # ---------------- 드로우다운 / MDD 그래프 ----------------
    dd_fig = go.Figure()
    mdd_info = []
    DEFAULT_COLORS = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692']
    for idx, col in enumerate(dd_df.columns):
        series = dd_df[col].dropna()
        if series.empty:
            continue
        mdd = series.min()  # 가장 큰 음수 값
        current_dd = series.iloc[-1]
        line_color = DEFAULT_COLORS[idx % len(DEFAULT_COLORS)]
        mdd_info.append((col, mdd, current_dd, line_color, col_to_symbol.get(col, col)))
        
        y_vals = series.values * 100
        custom_text = [f"<span style=\"color:{'#d32f2f' if v > 0 else '#1976d2' if v < 0 else 'inherit'}\">{v:+.2f}%</span>" for v in y_vals]
        
        dd_fig.add_trace(
            go.Scatter(
                x=series.index,
                y=y_vals,
                mode="lines",
                name=col,
                line=dict(color=line_color),
                customdata=custom_text,
                hovertemplate=f'{col}: %{{customdata}}<extra></extra>',
            )
        )
    dd_fig.update_layout(
        title="드로우다운 (MDD) 비교",
        xaxis_title=None,
        xaxis_hoverformat="%Y-%m-%d",
        yaxis_title="드로우다운 (%)",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
        showlegend=True # 단일 종목일 때도 범례 표시
    )
    st.plotly_chart(dd_fig, use_container_width=True)

    if mdd_info:
        # ---------------- 통합 비교용 MDD 버킷 계산 ----------------
        global_min_dd = dd_df.min().min() if not dd_df.empty else 0
        max_mdd_abs = abs(global_min_dd * 100) if not pd.isna(global_min_dd) else 0
        max_bin = int(np.ceil(max_mdd_abs / 5) * 5)
        bins_pos = list(range(0, max_bin + 5, 5))

        st.markdown("#### 📉 종목별 최대 낙폭(MDD) 및 현재 하락률")
        cols = st.columns(len(mdd_info))
        for col_idx, (col, mdd, current_dd, line_color, resolved_sym) in enumerate(mdd_info):
            mdd_val = mdd * 100
            cur_val = current_dd * 100
            mdd_color = "#d32f2f" if mdd_val > 0 else "#1976d2" if mdd_val < 0 else "inherit"
            cur_color = "#d32f2f" if cur_val > 0 else "#1976d2" if cur_val < 0 else "inherit"
            
            with cols[col_idx]:
                with st.container(border=True):
                    # 현재 낙폭 기준의 정확한 회복률(%) 선행 계산
                    series = dd_df[col].dropna()
                    total_days = len(series)
                    
                    cond_days_cur = (series >= current_dd).sum()
                    rec_rate_cur = cond_days_cur / total_days * 100 if total_days > 0 else 0
                    
                    # 회복률 구간에 따른 색상 지정 (직관성 강화)
                    if rec_rate_cur >= 90:
                        rec_color = "#3b82f6"  # Blue (매우 안전)
                    elif rec_rate_cur >= 80:
                        rec_color = "#10b981"  # Green (안전)
                    else:
                        rec_color = "#f59e0b"  # Orange (주의)

                    st.markdown(f"**<span style='color:{line_color};'>■</span> {col}**", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size:0.875rem; color:#6b7280; margin-bottom:0.1rem;'>최대 낙폭 (MDD)</div><div style='font-size:1.5rem; font-weight:600; color:{mdd_color}; margin-bottom:0.5rem;'>{mdd_val:+.2f}%</div>", unsafe_allow_html=True)
                    
                    html_cur = f"""
                    <div style='display: flex; justify-content: space-between; align-items: flex-end; margin-bottom:0.5rem;'>
                        <div>
                            <div style='font-size:0.875rem; color:#6b7280; margin-bottom:0.1rem;'>현재 고점 대비 하락률</div>
                            <div style='font-size:1.5rem; font-weight:600; color:{cur_color};'>{cur_val:+.2f}%</div>
                        </div>
                        <div style='text-align: right;'>
                            <div style='font-size:0.875rem; color:#6b7280; margin-bottom:0.1rem;'>현재 회복률</div>
                            <div style='font-size:1.5rem; font-weight:600; color:{rec_color};'>{rec_rate_cur:.1f}%</div>
                        </div>
                    </div>
                    """
                    st.markdown(html_cur, unsafe_allow_html=True)

                    # --- Recovery Table Start ---

                    html = "<div style='display: flex; flex-direction: column; gap: 6px; margin-top: 10px; font-size: 0.9rem;'>"
                    html += "<div style='display: flex; justify-content: space-between; padding: 0 16px 4px 16px; font-size: 0.8rem; color: #64748b; font-weight: 600;'>"
                    html += "<span>MDD</span><span>회복률</span></div>"

                    # Find current MDD bucket for highlighting
                    current_bucket_idx = -1
                    if -cur_val >= bins_pos[-1]:
                        current_bucket_idx = len(bins_pos) - 1
                    else:
                        for i in range(len(bins_pos)-1):
                            if bins_pos[i] <= -cur_val < bins_pos[i+1]:
                                current_bucket_idx = i
                                break

                    for i, th_val in enumerate(bins_pos):
                        th = -th_val / 100.0
                        cond_days = (series >= th).sum()
                        rec_rate = cond_days / total_days * 100 if total_days > 0 else 0

                        label = f"{-th_val}%"

                        # 저점매수를 위한 회복률 기준 (Slate 계열 농도)
                        if rec_rate >= 90:
                            bg_color = "#94a3b8"  # Slate-400 (개별종목 매수 신호) - 더 진하게
                            val_color_override = "#ffffff"
                            label_color_override = "#f8fafc"
                        elif rec_rate >= 80:
                            bg_color = "#e2e8f0"  # Slate-200 (ETF 매수 신호)
                            val_color_override = None
                            label_color_override = None
                        else:
                            bg_color = "transparent"  # 기준 미달은 투명하게
                            val_color_override = None
                            label_color_override = None

                        is_current = (i == current_bucket_idx)

                        # 현재 구간 하이라이트 효과
                        if is_current:
                            current_style = "border: 1.5px solid #3b82f6; box-shadow: 0 2px 4px rgba(59, 130, 246, 0.15);"
                            val_color = "#1d4ed8"  # Blue-700
                            label_color = "#1e3a8a" # Blue-900
                        else:
                            current_style = "border: 1.5px solid transparent;"
                            val_color = val_color_override if val_color_override else "#0f172a"  # Slate-900
                            label_color = label_color_override if label_color_override else "#475569" # Slate-600

                        html += f"<div style='display: flex; justify-content: space-between; align-items: center; background-color: {bg_color}; padding: 8px 16px; border-radius: 8px; transition: all 0.2s; {current_style}'>"
                        html += f"<span style='font-weight: 500; color: {label_color};'>{label}</span>"

                        font_weight = "700" if rec_rate >= 80 else "400"
                        html += f"<span style='font-weight: {font_weight}; color: {val_color};'>{rec_rate:.1f}%</span>"
                        html += "</div>"

                    html += "</div>"
                    st.markdown(html, unsafe_allow_html=True)
                    # --- Recovery Table End ---        
        # Summary description
        st.markdown("""
        <div style='margin-top:20px; padding: 16px; background-color: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;'>
            <div style='font-size: 1rem; color: #0f172a; font-weight: 700; margin-bottom: 8px;'>💡 현재 하락 회복 확률 (과거 데이터 기준)</div>
            <div style='font-size: 0.95rem; color: #334155; margin-bottom: 4px;'>과거 전체 기간 동안 주가가 지금보다 더 크게 하락했던 적이 얼만큼 있었는지를 백분율로 나타냅니다.</div>
            <div style='font-size: 0.85rem; color: #64748b; line-height: 1.4;'>
                * <strong>회복률 수치가 높을수록:</strong> 주가가 역사적인 바닥권에 근접하여 저점 매수에 유리함을 뜻합니다.<br>
                * 파란색 테두리는 현재의 낙폭 상태를 의미합니다. (권장 매수 기준: 개별종목 90% 이상 / ETF 80% 이상)
            </div>
        </div>
        """, unsafe_allow_html=True)



def render_comparison_section():
    st.markdown("### 📊 종목 비교 분석 (수익률 & MDD)")

    st.markdown(
        "최초 투자 원금이 현재까지 어떻게 변동되었는지(누적 수익률), 그리고 그 과정에서 최대 어느 정도의 손실(MDD)을 겪었는지 비교합니다.  \n"
        "- 종목명(한글/영어) 또는 티커를 입력하세요. (최대 3개 입력 가능/1개 입력 시 단독 분석 지원)  \n"
        "- 💡 **주의:** 해외 주식의 수익률은 환율 변동이 배제된 순수 달러(USD) 주가 상승률 기준입니다."
    )

    cols = st.columns(3)
    with cols[0]:
        t1_raw = st.text_input(
            "종목 1",
            value=st.session_state.get("cmp_1", "QQQ"),
            key="cmp_1",
            placeholder="예: aapl"
        )
    with cols[1]:
        t2_raw = st.text_input(
            "종목 2 (선택)",
            value=st.session_state.get("cmp_2", ""),
            key="cmp_2",
            placeholder="예: 삼성전자"
        )
    with cols[2]:
        t3_raw = st.text_input(
            "종목 3 (선택)",
            value=st.session_state.get("cmp_3", ""),
            key="cmp_3",
            placeholder="예: QQQ"
        )

    today = dt.date.today()
    default_start = today - dt.timedelta(days=365*10)
    min_allowed_date = dt.date(1920, 1, 1)

    col_s, col_e = st.columns(2)
    with col_s:
        start_date = st.date_input("시작일", value=st.session_state.get("cmp_start", default_start), min_value=min_allowed_date, max_value=today, key="cmp_start")
    with col_e:
        end_date = st.date_input("종료일", value=st.session_state.get("cmp_end", today), min_value=min_allowed_date, max_value=today, key="cmp_end")

    st.session_state.cmp_state = {
        "tickers": [t1_raw, t2_raw, t3_raw],
        "start": start_date,
        "end": end_date
    }
    state = st.session_state.cmp_state
    run_comparison_analysis(state["tickers"], state["start"], state["end"])


def run_investment_simulation(tickers_with_id: List[tuple], start_date: dt.date, end_date: dt.date, sim_type: str, amount: float):
    fig = go.Figure()
    results = []
    valid_df_for_plot = None
    for sim_id, raw_t in tickers_with_id:
        norm_ticker = normalize_ticker(raw_t)
        if not norm_ticker:
            continue
            
        quote = fetch_latest_quote(norm_ticker)
        resolved_symbol = quote.get("symbol", norm_ticker) if quote else norm_ticker
        display_name = fetch_symbol_name(resolved_symbol)
        
        if not display_name or display_name == resolved_symbol:
            if re.match(r'^[a-zA-Z]+$', raw_t):
                display_name = raw_t.upper()
            else:
                display_name = resolved_symbol

        df = fetch_price_history(resolved_symbol, start_date, end_date)
        if df.empty:
            st.warning(f"'{raw_t}' ({resolved_symbol}): 가격 데이터를 가져오지 못했습니다.")
            continue

        df = df.sort_index()
        kr = is_korean_listed_ticker(resolved_symbol)

        # 원화 계산을 위해 환율 데이터 가져오기 (미국 주식인 경우)
        if not kr:
            fx_df = fetch_price_history("USDKRW=X", start_date, end_date)
            if fx_df.empty:
                fx_q = fetch_latest_quote("USDKRW=X")
                usd_krw_current = float(fx_q["price"]) if fx_q else 1300.0
                df['fx'] = usd_krw_current
            else:
                fx_df = fx_df.sort_index()
                df = df.join(fx_df['close'].rename('fx'), how='left')
                df['fx'] = df['fx'].ffill().bfill()
        else:
            df['fx'] = 1.0

        # 원화 기준 가격 계산
        df['price_krw'] = df['close'] * df['fx']
        
        buy_series = pd.Series(0.0, index=df.index)
        invest_series = pd.Series(0.0, index=df.index)
        
        if sim_type == "거치식 (Lump Sum)":
            first_idx = df.index[0]
            buy_series.loc[first_idx] = amount / df.loc[first_idx, 'price_krw']
            invest_series.loc[first_idx] = amount
        elif sim_type == "적립식 (매일/DCA)":
            for idx in df.index:
                buy_series.loc[idx] = amount / df.loc[idx, 'price_krw']
                invest_series.loc[idx] = amount
        elif sim_type == "적립식 (매월/DCA)":
            monthly_first_days = df.groupby([df.index.year, df.index.month]).head(1)
            for idx in monthly_first_days.index:
                buy_series.loc[idx] = amount / df.loc[idx, 'price_krw']
                invest_series.loc[idx] = amount
        elif sim_type == "적립식 (매년/DCA)":
            yearly_first_days = df.groupby(df.index.year).head(1)
            for idx in yearly_first_days.index:
                buy_series.loc[idx] = amount / df.loc[idx, 'price_krw']
                invest_series.loc[idx] = amount
                
        cum_shares = buy_series.cumsum()
        cum_invested = invest_series.cumsum()
        
        df['Total Invested'] = cum_invested
        df['Portfolio Value'] = cum_shares * df['price_krw']
        df['Profit'] = df['Portfolio Value'] - df['Total Invested']
        total_invested = df['Total Invested'].iloc[-1]
        final_value = df['Portfolio Value'].iloc[-1]
        profit = final_value - total_invested
        
        user_tax_type = st.session_state.get(f"sim_tax_override_{sim_id}", "자동 추론")
        actual_tax_type = infer_tax_type(resolved_symbol, display_name) if user_tax_type == "자동 추론" else user_tax_type
        
        tax_amount = 0.0
        if st.session_state.get("sim_apply_tax", True):
            if actual_tax_type == "미국직투(22%)" and profit > 2500000:
                tax_amount = (profit - 2500000) * 0.22
            elif actual_tax_type == "해외ETF(15.4%)" and profit > 0:
                tax_amount = profit * 0.154
            elif actual_tax_type == "ISA(9.9%)" and profit > 0:
                tax_amount = profit * 0.099
            
        profit_after_tax = profit - tax_amount
        final_value_after_tax = final_value - tax_amount
        profit_pct_after_tax = (profit_after_tax / total_invested) * 100 if total_invested > 0 else 0
        
        DEFAULT_COLORS = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692']
        line_color = DEFAULT_COLORS[len(results) % len(DEFAULT_COLORS)]
        
        results.append({
            "name": display_name,
            "total_invested": total_invested,
            "final_value": final_value,
            "profit": profit,
            "tax_amount": tax_amount,
            "profit_after_tax": profit_after_tax,
            "final_value_after_tax": final_value_after_tax,
            "profit_pct": profit_pct_after_tax,
            "line_color": line_color,
            "kr": kr,
            "tax_type": actual_tax_type,
            "sim_id": sim_id
        })
        
        df['ROI'] = np.where(df['Total Invested'] > 0, (df['Profit'] / df['Total Invested']) * 100, 0.0)
        custom_html = [
            f"<span style=\"color:{'#d32f2f' if r > 0 else '#1976d2' if r < 0 else 'inherit'}\">{r:+.2f}%</span>"
            for r in df['ROI']
        ]
        
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['Portfolio Value'].round(0),
                mode='lines',
                name=f'{display_name}',
                line=dict(color=line_color),
                hovertemplate=f'{display_name}: %{{customdata}}<extra></extra>',
                customdata=custom_html
            )
        )
        valid_df_for_plot = df

    if not results:
        return

    st.markdown("<br>", unsafe_allow_html=True)
    hdr_c1, hdr_c2 = st.columns([3, 1])
    with hdr_c1:
        st.markdown("#### 💰 시뮬레이션 결과 요약 (원화 기준)")
    with hdr_c2:
        apply_tax = st.checkbox("세금 계산 적용", value=st.session_state.get("sim_apply_tax", True), key="sim_apply_tax")
        
    for res in results:
        color = "#d32f2f" if res['profit_after_tax'] > 0 else "#1976d2" if res['profit_after_tax'] < 0 else "inherit"
        with st.container(border=True):
            line_color = res.get('line_color', '#111827')
            kr_badge = "🇰🇷 한국" if res.get('kr') else "🇺🇸 미국"
            
            with st.container():
                html = f"""
                <div class="tax-badge-row" style='display:flex; align-items:center; gap:8px; height: 28px; width:100%; min-width:0;'>
                    <div style='flex: 0 1 auto; min-width: 0; font-weight:700; font-size:1.05rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; line-height: normal; padding-top: 2px;' title='{res['name']}'><span style='color:{line_color};'>■</span> {res['name']}</div>
                    <div style='flex-shrink:0; font-size:0.75rem; background:#e5e7eb; padding:0 6px; border-radius:4px; white-space:nowrap; display:flex; align-items:center; justify-content:center; height:22px; color:#374151; font-weight:600;'>{kr_badge}</div>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)
                if apply_tax:
                    tax_options = ["미국직투(22%)", "해외ETF(15.4%)", "국내주식(비과세)", "ISA(9.9%)"]
                    st.selectbox("세금 유형", tax_options, index=tax_options.index(res['tax_type']) if res['tax_type'] in tax_options else 0, key=f"sim_tax_override_{res['sim_id']}", label_visibility="collapsed")
            
            if apply_tax:
                col1, col2, col3, col4, col5 = st.columns(5)
            else:
                col1, col2, col3, col4 = st.columns(4)
                
            with col1:
                st.markdown(f"<div style='font-size:0.875rem; color:#6b7280; margin-bottom:0.1rem;'>총 투자 원금</div><div style='font-size:1.5rem; font-weight:600;'>{res['total_invested']:,.0f}원</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div style='font-size:0.875rem; color:#6b7280; margin-bottom:0.1rem;'>최종 평가액</div><div style='font-size:1.5rem; font-weight:600;'>{res['final_value_after_tax']:,.0f}원</div>", unsafe_allow_html=True)
            with col3:
                p_color = "#d32f2f" if res['profit'] > 0 else "#1976d2" if res['profit'] < 0 else "inherit"
                if apply_tax:
                    st.markdown(f"<div style='font-size:0.875rem; color:#6b7280; margin-bottom:0.1rem;'>세전 수익금</div><div style='font-size:1.5rem; font-weight:600; color:{p_color};'>{res['profit']:+,.0f}원</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='font-size:0.875rem; color:#6b7280; margin-bottom:0.1rem;'>총 수익금</div><div style='font-size:1.5rem; font-weight:600; color:{p_color};'>{res['profit']:+,.0f}원</div>", unsafe_allow_html=True)
            
            if apply_tax:
                with col4:
                    tax_str = f"-{res['tax_amount']:,.0f}원" if res['tax_amount'] > 0 else "0원"
                    if res['tax_type'] == "미국직투(22%)":
                        tax_title = "예상 세금(22%)"
                    elif res['tax_type'] == "해외ETF(15.4%)":
                        tax_title = "예상 세금(15.4%)"
                    elif res['tax_type'] == "ISA(9.9%)":
                        tax_title = "예상 세금(9.9%)"
                    else:
                        tax_title = "예상 세금"
                    st.markdown(f"<div style='font-size:0.875rem; color:#6b7280; margin-bottom:0.1rem;'>{tax_title}</div><div style='font-size:1.5rem; font-weight:600; color:#eab308;'>{tax_str}</div>", unsafe_allow_html=True)
                with col5:
                    st.markdown(f"<div style='font-size:0.875rem; color:#6b7280; margin-bottom:0.1rem;'>세후 수익률</div><div style='font-size:1.5rem; font-weight:600; color:{color};'>{res['profit_pct']:+.2f}%</div>", unsafe_allow_html=True)
            else:
                with col4:
                    st.markdown(f"<div style='font-size:0.875rem; color:#6b7280; margin-bottom:0.1rem;'>총 수익률</div><div style='font-size:1.5rem; font-weight:600; color:{p_color};'>{res['profit_pct']:+.2f}%</div>", unsafe_allow_html=True)
        
    if valid_df_for_plot is not None:
        fig.add_trace(go.Scatter(x=valid_df_for_plot.index, y=valid_df_for_plot['Total Invested'].round(0), mode='lines', name='누적 투자금', line=dict(dash='dash', color='#9e9e9e'), hovertemplate='누적 투자금: %{y:,.0f}원<extra></extra>'))
    fig.update_layout(
        title=f"투자 시뮬레이션 결과 ({sim_type}) - 원화(KRW)", 
        xaxis_title=None,
        xaxis_hoverformat="%Y-%m-%d", 
        yaxis_title="금액 (원)", 
        hovermode="x unified", 
        template="plotly_white",
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
        showlegend=True # 단일 종목일 때도 범례 표시
    )
    st.plotly_chart(fig, use_container_width=True)


@st.fragment
def render_simulation_section():
    st.markdown("### ⏳ 과거 투자 시뮬레이션 (백테스팅)")
    st.markdown("과거 특정 시점에 투자했다면 현재 얼마가 되었을지 **원화(KRW)** 기준으로 계산합니다. (미국 주식은 과거 환율 자동 적용)")
    st.markdown("최대 **3개 종목**을 입력하여 투자 결과를 비교해볼 수 있습니다.")
    
    cols = st.columns(3)
    with cols[0]:
        sim_t1 = st.text_input("종목 1", value=st.session_state.get("sim_t1", "QQQ"), key="sim_t1")
    with cols[1]:
        sim_t2 = st.text_input("종목 2 (선택)", value=st.session_state.get("sim_t2", ""), key="sim_t2")
    with cols[2]:
        sim_t3 = st.text_input("종목 3 (선택)", value=st.session_state.get("sim_t3", ""), key="sim_t3")

    cols2 = st.columns([1.5, 1.5, 1.5, 1.5])
    with cols2[0]:
        sim_type = st.selectbox("투자 방식", [
            "거치식 (Lump Sum)", 
            "적립식 (매일/DCA)", 
            "적립식 (매월/DCA)", 
            "적립식 (매년/DCA)"
        ], key="sim_type")
    with cols2[1]:
        amount = st.number_input("1회 투자금 (원)", min_value=1000, value=st.session_state.get("sim_amount", 1000000), step=100000, key="sim_amount")
        
    today = dt.date.today()
    min_allowed_date = dt.date(1920, 1, 1)
    
    with cols2[2]:
        sim_start = st.date_input("시작일", value=st.session_state.get("sim_start", today - dt.timedelta(days=365*10)), min_value=min_allowed_date, max_value=today, key="sim_start") # 기본 시작일을 10년 전으로 변경
    with cols2[3]:
        sim_end = st.date_input("종료일", value=st.session_state.get("sim_end", today), min_value=min_allowed_date, max_value=today, key="sim_end")
        
    if sim_start >= sim_end:
        st.error("시작일은 종료일보다 빨라야 합니다.")
        return
        
    sim_tickers = [("sim_1", sim_t1), ("sim_2", sim_t2), ("sim_3", sim_t3)]
    valid_sim_tickers = [(sid, t.strip()) for sid, t in sim_tickers if t.strip()]
    
    if valid_sim_tickers:
        run_investment_simulation(valid_sim_tickers, sim_start, sim_end, sim_type, amount)


def calculate_c_indicator_history(ticker: str, S0: float, mu: float, sigma: float, start_date: dt.date) -> pd.DataFrame:
    data = yf.download(ticker, period="max", progress=False)
    if data.empty or "Close" not in data.columns:
        return pd.DataFrame()
    
    close = data["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close = close.dropna()
    
    plot_data = close
    if plot_data.empty:
        return pd.DataFrame()
        
    t_series = pd.Series(np.arange(1, len(close) + 1), index=close.index)
    plot_t = t_series[plot_data.index]
    
    z_scores = (np.log(plot_data / S0) - mu * plot_t) / (sigma * np.sqrt(plot_t))
    percentiles = stats.norm.cdf(z_scores) * 100
    
    z_99 = stats.norm.ppf(0.99)   # CI ~0%
    z_75 = stats.norm.ppf(0.75)   # CI 25%
    z_625 = stats.norm.ppf(0.625) # CI 37.5%
    z_55 = stats.norm.ppf(0.55)   # CI 45%
    z_45 = stats.norm.ppf(0.45)   # CI 55%
    z_375 = stats.norm.ppf(0.375) # CI 62.5%
    z_25 = stats.norm.ppf(0.25)   # CI 75%
    z_01 = stats.norm.ppf(0.01)   # CI ~100%
    
    return pd.DataFrame({
        "Date": plot_data.index,
        "Price": plot_data.values,
        "CI_Percentile": 100.0 - percentiles,
        "Median": S0 * np.exp(mu * plot_t),
        "Band_99": S0 * np.exp(mu * plot_t + sigma * np.sqrt(plot_t) * z_99),
        "Band_75": S0 * np.exp(mu * plot_t + sigma * np.sqrt(plot_t) * z_75),
        "Band_625": S0 * np.exp(mu * plot_t + sigma * np.sqrt(plot_t) * z_625),
        "Band_55": S0 * np.exp(mu * plot_t + sigma * np.sqrt(plot_t) * z_55),
        "Band_45": S0 * np.exp(mu * plot_t + sigma * np.sqrt(plot_t) * z_45),
        "Band_375": S0 * np.exp(mu * plot_t + sigma * np.sqrt(plot_t) * z_375),
        "Band_25": S0 * np.exp(mu * plot_t + sigma * np.sqrt(plot_t) * z_25),
        "Band_01": S0 * np.exp(mu * plot_t + sigma * np.sqrt(plot_t) * z_01)
    })

def fetch_vkospi_from_public_api() -> float:
    """공공데이터포털 API 또는 인베스팅닷컴에서 VKOSPI(코스피200 변동성지수)를 가져옵니다."""
    import requests
    import os
    import re
    from dotenv import load_dotenv

    load_dotenv()
    
    # 1. 공공데이터포털 API 시도
    service_key = os.environ.get("DATA_GO_KR_KEY", "")
    if service_key:
        try:
            url = "http://apis.data.go.kr/1160100/service/GetMarketIndexInfoService/getStockMarketIndex"
            params = {
                "serviceKey": requests.utils.unquote(service_key), # URL 인코딩 이슈 방지
                "numOfRows": "1",
                "pageNo": "1",
                "resultType": "json",
                "idxNm": "코스피 200 변동성지수"
            }
            res = requests.get(url, params=params, timeout=3, verify=False)
            if res.status_code == 200:
                data = res.json()
                items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
                if items:
                    return float(items[0].get("clpr", 0.0))
        except Exception:
            pass

    # 2. 인베스팅닷컴 폴백 (매우 안정적)
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        url = "https://kr.investing.com/indices/kospi-volatility"
        res = requests.get(url, headers=headers, timeout=3)
        match = re.search(r'data-test="instrument-price-last">([\d,.]+)', res.text)
        if match:
            return float(match.group(1).replace(',', ''))
    except Exception:
        pass
        
    return 0.0

def fetch_vkospi_history(days: int = 100) -> dict:
    """공공데이터포털 API를 통해 VKOSPI 최근 히스토리 데이터를 가져옵니다."""
    import requests
    import os
    import pandas as pd
    from dotenv import load_dotenv

    load_dotenv()
    vk_dict = {}
    
    service_key = os.environ.get("DATA_GO_KR_KEY", "")
    if service_key:
        try:
            url = "http://apis.data.go.kr/1160100/service/GetMarketIndexInfoService/getStockMarketIndex"
            params = {
                "serviceKey": requests.utils.unquote(service_key),
                "numOfRows": str(days),
                "pageNo": "1",
                "resultType": "json",
                "idxNm": "코스피 200 변동성지수"
            }
            res = requests.get(url, params=params, timeout=5, verify=False)
            if res.status_code == 200:
                data = res.json()
                items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
                for item in items:
                    dt_str = item.get("basDt", "")
                    clpr = item.get("clpr", "0")
                    if dt_str and clpr:
                        # Timestamp 대신 순수 date 객체로 저장하여 매칭 불일치 해결
                        dt_obj = pd.to_datetime(dt_str).date()
                        vk_dict[dt_obj] = float(clpr)
        except Exception:
            pass
            
    return vk_dict


def calculate_rsi_ema(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def evaluate_timing_state(mdd, ma_diff, vix, rsi, is_tail_vol_spike, th, recovery_rate):
    """
    th: dict containing 'mdd1', 'mdd2', 'mdd3', 'mdd_tail', 'rec_th'
    """
    # 역사적 회복률(바닥권 통계) 인증 마크 부여 여부
    is_rec_hit = recovery_rate >= th['rec_th']
    badge = " [바닥 확인 ✅]" if is_rec_hit else ""
    
    # 3단계: 시스템 붕괴급 투매 (VIX 35 이상 초공포 OR 큰 하락 중 투매 꼬리 발생)
    if (mdd <= th['mdd3'] and vix >= 35) or (mdd <= th['mdd_tail'] and is_tail_vol_spike):
        return 3, f"🔴 3단계: 찐 저점 포착 (시스템 투매 국면){badge}", "#ef4444", "역사적 바닥일 확률이 높습니다! 예비 현금을 4배수 이상 적극적으로 투입해 주력 ETF 비중을 늘리고, 레버리지 자산의 신규 진입을 진지하게 고려해 볼 수 있는 공격적 매수 시점입니다."
    # 2단계: 본격 약세장 속 투매 (MDD 기준치 이상 하락 중 VIX 30 이상 또는 RSI 극저점)
    elif mdd <= th['mdd2'] and (vix >= 30 or rsi <= 30):
        return 2, f"🟠 2단계: 약세장 투매 구간 (비중 대폭 확대){badge}", "#f97316", "본격적인 공포 구간입니다. 주력 ETF 매수 금액을 2.5배로 과감히 증액하세요. 레버리지 예비 자금의 30%를 투입해 포트폴리오를 재구축할 타이밍입니다."
    # 1단계: 단기 조정 중 과매도 (MDD 기준치 이상 하락 중 공포 심리 확대 또는 RSI 과매도)
    elif mdd <= th['mdd1'] and (vix >= 22 or rsi <= 40):
        return 1, f"🟡 1단계: 단기 조정 구간 (비중 일부 확대){badge}", "#eab308", "주력 ETF 매수 금액을 1.5배로 늘리세요. 예비 자금의 10%를 활용해 소량 진입해 볼 수 있습니다."
    else:
        return 0, "💤 관망 / 정기 매수 구간", "#94a3b8", "현재는 특별한 저점 매수 구간이 아닙니다. 설정한 정기 매수 금액(1.0배수)만 적립식으로 유지하세요."

def render_timing_section():
    st.markdown("### 🎯 매수 시점 판별 (타이밍 포착)")
    st.markdown("현재 지표(MDD, VIX, RSI, 장기 추세선, 캔들 패턴)를 복합적으로 분석해 기계적인 저점 매수 타이밍과 행동 지침을 진단합니다.")

    col1, col2 = st.columns([1, 2])
    with col1:
        t_ticker = st.text_input("타이밍 진단 종목", value=st.session_state.get("timing_ticker", "QQQ"), key="timing_ticker")
    with col2:
        history_period = st.radio("과거 차트 조회 기간", ["1년", "3년", "5년", "최대"], horizontal=True, index=0)
    
    if t_ticker.strip():
        with st.spinner("타이밍 지표 및 히스토리를 연산하는 중입니다..."):
            norm_t = normalize_ticker(t_ticker)
            if not norm_t:
                st.error("잘못된 종목 코드입니다.")
                return
            
            buffer_days = 400
            if history_period == "1년":
                query_days = 365
            elif history_period == "3년":
                query_days = 365 * 3
            elif history_period == "5년":
                query_days = 365 * 5
            else:
                query_days = 365 * 10
                
            end_d = dt.date.today()
            start_d = end_d - dt.timedelta(days=query_days + buffer_days)
            df = yf.download(norm_t, start=start_d, end=end_d, progress=False)
            vix_df = yf.download("^VIX", start=start_d, end=end_d, progress=False)

            if df.empty or "Close" not in df.columns:
                st.error("종목 데이터를 가져오지 못했습니다.")
                return
                
            close_s = df["Close"].iloc[:, 0] if isinstance(df["Close"], pd.DataFrame) else df["Close"]
            open_s = df["Open"].iloc[:, 0] if isinstance(df["Open"], pd.DataFrame) else df["Open"]
            low_s = df["Low"].iloc[:, 0] if isinstance(df["Low"], pd.DataFrame) else df["Low"]
            vol_s = df["Volume"].iloc[:, 0] if isinstance(df["Volume"], pd.DataFrame) else df["Volume"]
            
            close_s = close_s.dropna()
            if len(close_s) < 20:
                st.error("데이터 기간이 너무 짧습니다.")
                return
                
            cur_price = close_s.iloc[-1]
            high_52w = close_s.tail(252).max()
            mdd = (cur_price - high_52w) / high_52w * 100
            
            try:
                info = yf.Ticker(norm_t).info
                quote_type = info.get("quoteType", "EQUITY")
                long_name = info.get("longName", "").upper()
            except Exception:
                quote_type = "EQUITY"
                long_name = ""
            
            # 한국 개별 종목 예외 처리 (6자리 숫자 티커인 경우 EQUITY 강제 적용)
            import re
            is_kr_ticker = bool(re.match(r'^\d{6}\.(KS|KQ)$', norm_t))
            if is_kr_ticker:
                # 레버리지 키워드가 없으면 개별 종목으로 간주 (데이터 제공처의 오류 방지)
                if quote_type != "EQUITY":
                    quote_type = "EQUITY"

                
            # 자산군 분류 로직
            leverage_keywords = ["2X", "3X", "LEVERAGED", "BULL", "ULTRA", "PROSHARES TRUST ULTRA", "DIREXION DAILY"]
            is_leverage = any(kw in long_name for kw in leverage_keywords) or \
                          any(tk in norm_t.upper() for tk in ["TQQQ", "QLD", "SOXL", "UPRO", "BULL", "LABU", "TECL", "FAS"])
            
            if is_leverage:
                asset_cat = "LEVERAGE"
                cat_name = "레버리지 ETF (2x/3x)"
                th = {"mdd1": -20, "mdd2": -35, "mdd3": -50, "mdd_tail": -25, "rec_th": 85}
            elif quote_type == "EQUITY":
                asset_cat = "EQUITY"
                cat_name = "개별 종목"
                th = {"mdd1": -15, "mdd2": -25, "mdd3": -35, "mdd_tail": -20, "rec_th": 90}
            else:
                asset_cat = "ETF_INDEX"
                cat_name = "지수 및 일반 ETF"
                th = {"mdd1": -10, "mdd2": -15, "mdd3": -20, "mdd_tail": -15, "rec_th": 80}
            
            # (원래 여기 있던 st.info 안내 박스는 가독성을 위해 하단으로 이동됨)

            ma_days = 200 if quote_type in ["ETF", "INDEX", "MUTUALFUND"] else 120
            
            ma_val = close_s.rolling(ma_days).mean().iloc[-1]
            ma_diff = (cur_price - ma_val) / ma_val * 100 if not np.isnan(ma_val) else 0
            
            # 히스토리 MDD 계산 (전체 기간 기준 통계 산출)
            full_high_52w = close_s.rolling(252).max()
            full_mdd_series = (close_s - full_high_52w) / full_high_52w
            
            mdd_for_stat = full_mdd_series.dropna()
            current_dd = mdd / 100.0
            total_stat_days = len(mdd_for_stat)
            recovery_rate_now = (mdd_for_stat >= current_dd).sum() / total_stat_days * 100 if total_stat_days > 0 else 0
            
            rsi_s = calculate_rsi_ema(close_s)
            rsi = rsi_s.iloc[-1] if not rsi_s.dropna().empty else 50
            
            # 공포 지수 선택 (US -> VIX, KR -> VKOSPI)
            is_korean = norm_t.endswith(".KS") or norm_t.endswith(".KQ")
            fear_idx_name = "VKOSPI" if is_korean else "VIX"
            fear_val = 20.0
            
            if is_korean:
                fear_val = fetch_vkospi_from_public_api()
                # VKOSPI가 0이면(실패 시) VIX로 폴백
                if fear_val <= 0:
                    if not vix_df.empty and "Close" in vix_df.columns:
                        v_s = vix_df["Close"].iloc[:, 0] if isinstance(vix_df["Close"], pd.DataFrame) else vix_df["Close"]
                        v_s = v_s.dropna()
                        if not v_s.empty:
                            fear_val = v_s.iloc[-1]
            else:
                if not vix_df.empty and "Close" in vix_df.columns:
                    v_s = vix_df["Close"].iloc[:, 0] if isinstance(vix_df["Close"], pd.DataFrame) else vix_df["Close"]
                    v_s = v_s.dropna()
                    if not v_s.empty:
                        fear_val = v_s.iloc[-1]
                    
            vol_20ma = vol_s.rolling(20).mean().iloc[-1]
            cur_vol = vol_s.iloc[-1]
            
            cur_open = open_s.iloc[-1]
            cur_low = low_s.iloc[-1]
            body = abs(cur_price - cur_open)
            lower_tail = min(cur_price, cur_open) - cur_low
            
            # 거래량 폭증 + 투매 클라이막스 캔들(아랫꼬리가 몸통의 2배 초과)
            is_tail_vol_spike = (cur_vol > vol_20ma * 2) and (lower_tail > body * 2) and (body > 0)
            
            state_idx, state_title, state_color, guide_txt = evaluate_timing_state(mdd, ma_diff, fear_val, rsi, is_tail_vol_spike, th, recovery_rate_now)
            
            st.markdown(f"#### <span style='color:{state_color};'>{state_title}</span>", unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='background-color:{state_color}; color:white; padding:20px 24px; border-radius:12px; margin-bottom:24px; font-size:1.15rem; font-weight:600; line-height:1.6; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);'>
                {guide_txt}
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                with st.container(border=True):
                    val_color = "#ef4444" if mdd <= -20 else "#eab308" if mdd <= -10 else "#334155"
                    st.markdown(f"<div title='고점 대비 하락률(Maximum Drawdown). 수치가 낮을수록 바닥에 근접했음을 의미합니다.' style='font-size:0.875rem; color:#6b7280; font-weight:600;'>MDD 하락률 <span style='font-size:0.7rem; color:#9ba3af;'>ⓘ</span></div><div title='고점 대비 하락률' style='font-size:1.4rem; font-weight:800; color:{val_color};'>{mdd:.1f}%</div>", unsafe_allow_html=True)
            with c2:
                with st.container(border=True):
                    val_color = "#ef4444" if fear_val >= 30 else "#eab308" if fear_val >= 20 else "#334155"
                    st.markdown(f"<div title='시장 변동성/공포 지수. 30~40 이상이면 극도의 공포 상태(단기 바닥 및 매수 기회)로 봅니다.' style='font-size:0.875rem; color:#6b7280; font-weight:600;'>현재 {fear_idx_name} 지수 <span style='font-size:0.7rem; color:#9ba3af;'>ⓘ</span></div><div title='공포/변동성 지수' style='font-size:1.4rem; font-weight:800; color:{val_color};'>{fear_val:.1f}</div>", unsafe_allow_html=True)
            with c3:
                with st.container(border=True):
                    val_color = "#ef4444" if rsi <= 30 else "#10b981" if rsi >= 70 else "#334155"
                    st.markdown(f"<div title='상대강도지수(14일). 30 이하면 과매도(바닥권), 70 이상이면 과매수(천장권) 상태입니다.' style='font-size:0.875rem; color:#6b7280; font-weight:600;'>RSI (14일) <span style='font-size:0.7rem; color:#9ba3af;'>ⓘ</span></div><div title='RSI 지수' style='font-size:1.4rem; font-weight:800; color:{val_color};'>{rsi:.1f}</div>", unsafe_allow_html=True)
            with c4:
                with st.container(border=True):
                    val_color = "#ef4444" if ma_diff < 0 else "#10b981"
                    st.markdown(f"<div title='{ma_days}일 장기 이동평균선 확인. 주가가 이보다 아래에 있으면 역배열(하락 추세)일 확률이 높습니다. ETF/지수는 200일, 개별종목은 120일 기준.' style='font-size:0.875rem; color:#6b7280; font-weight:600;'>{ma_days}일선 위치 <span style='font-size:0.7rem; color:#9ba3af;'>ⓘ</span></div><div title='장기 이평선 기준 위치' style='font-size:1.4rem; font-weight:800; color:{val_color};'>{'하향 이탈' if ma_diff < 0 else '안정 (상단)'}</div>", unsafe_allow_html=True)
            with c5:
                # 역사적 회복률 수치만 심플하게 표시
                with st.container(border=True):
                    is_rec_hit = recovery_rate_now >= th['rec_th']
                    val_color = "#ef4444" if is_rec_hit else "#334155"
                    st.markdown(f"<div title='과거 전체 데이터 대비 현재의 낙폭이 얼마나 깊은 바닥인지 통계로 나타낸 수치. 수치가 높을수록 역사적 저점에 가깝습니다.' style='font-size:0.875rem; color:#6b7280; font-weight:600;'>역사적 회복률 <span style='font-size:0.7rem; color:#9ba3af;'>ⓘ</span></div><div style='font-size:1.4rem; font-weight:800; color:{val_color};'>{recovery_rate_now:.1f}%</div>", unsafe_allow_html=True)
                     
            # --- Historical State Evaluation & Graph ---
            ma_val_series = close_s.rolling(ma_days).mean()
            ma_diff_series = (close_s - ma_val_series) / ma_val_series * 100
            high_52w_series = close_s.rolling(252).max()
            mdd_series = (close_s - high_52w_series) / high_52w_series * 100
            
            vol_20ma_series = vol_s.rolling(20).mean()
            body_series = (close_s - open_s).abs()
            lower_tail_series = pd.concat([open_s, close_s], axis=1).min(axis=1) - low_s
            is_tail_vol_spike_series = (vol_s > vol_20ma_series * 2) & (lower_tail_series > body_series * 2) & (body_series > 0)
            
            fear_series = pd.Series(20.0, index=close_s.index)
            if not vix_df.empty and "Close" in vix_df.columns:
                v_s = vix_df["Close"].iloc[:, 0] if isinstance(vix_df["Close"], pd.DataFrame) else vix_df["Close"]
                fear_series = v_s.reindex(close_s.index).ffill().fillna(20.0)
                
            # 한국 종목일 경우 최근 VKOSPI 히스토리 가져오기 (최근 약 100일)
            vk_history = {}
            if is_korean:
                vk_history = fetch_vkospi_history(100)
                
            state_history = []
            # Calculate rolling recovery rate history
            for dt_idx in close_s.index:
                c_mdd = mdd_series.loc[dt_idx]
                c_ma = ma_diff_series.loc[dt_idx]
                c_feat = fear_series.loc[dt_idx] # 기본값: VIX (Proxy)
                c_rsi = rsi_s.loc[dt_idx]
                c_tail = is_tail_vol_spike_series.loc[dt_idx]
                
                # 한국 종목이고 해당 날짜의 VKOSPI가 있다면 우선 적용 (표준화된 date 비교)
                if is_korean and vk_history and dt_idx.date() in vk_history:
                    c_feat = vk_history[dt_idx.date()]
                
                # 실시간 진단과 그래프 동기화: 마지막 날의 공포 지수는 실시간 fetch된 fear_val 사용 (최신성 우선)
                if dt_idx == close_s.index[-1]:
                    c_feat = fear_val
                
                # Historical Recovery Rate at that moment (using full history)
                c_mdd_val = c_mdd/100.0
                c_rec_rate = (mdd_for_stat >= c_mdd_val).sum() / total_stat_days * 100 if total_stat_days > 0 else 0
                
                if pd.isna(c_mdd) or pd.isna(c_ma):
                    state_history.append(0)
                else:
                    s_idx, _, _, _ = evaluate_timing_state(c_mdd, c_ma, c_feat, c_rsi, c_tail, th, c_rec_rate)
                    state_history.append(s_idx)
            
            state_series = pd.Series(state_history, index=close_s.index)
            
            # Determine how many trading days to plot
            if history_period == "1년":
                dt_days = 252
            elif history_period == "3년":
                dt_days = 252 * 3
            elif history_period == "5년":
                dt_days = 252 * 5
            else:
                dt_days = 252 * 10
                
            plot_df = pd.DataFrame({"Price": close_s, "State": state_series}).dropna().tail(dt_days)
            # Format index to string to avoid weekend gaps in Plotly category axis
            plot_df.index = plot_df.index.strftime('%Y-%m-%d')
            
            fig = go.Figure()
            # Changed opacity to make the colors much more vivid and visible against the background
            color_map = {0: 'rgba(255, 255, 255, 0.0)', 1: 'rgba(234, 179, 8, 0.6)', 2: 'rgba(249, 115, 22, 0.8)', 3: 'rgba(220, 38, 38, 1.0)'}
            colors = plot_df['State'].map(color_map).tolist()
            
            # Uniform height bars (background feeling)
            fig.add_trace(go.Bar(
                x=plot_df.index, y=[1] * len(plot_df),
                marker_color=colors, name="매수 구간", yaxis="y1",
                width=1.0, marker_line_width=0, # Removes tiny white space gaps between contiguous blocks
                hovertemplate="날짜: %{x}<br>매수 등급: %{customdata}단계<extra></extra>",
                customdata=plot_df['State'].tolist()
            ))
            
            fig.add_trace(go.Scatter(
                x=plot_df.index, y=plot_df['Price'],
                mode='lines', name='주가',
                line=dict(color='#1e3a8a', width=2), yaxis="y2",
                hovertemplate="주가: %{y:,.2f}<extra></extra>"
            ))
            
            fig.update_layout(
                title=f"📈 {history_period} 타이밍 등급 히스토리 차트",
                yaxis=dict(range=[0, 1], showticklabels=False, fixedrange=True, side="left"),
                yaxis2=dict(title="주가", overlaying="y", side="right", showgrid=False),
                xaxis=dict(type='category', tickmode='auto', nticks=12),
                bargap=0, # Removes the gap between bars
                hovermode="x unified", template="plotly_white", height=350,
                margin=dict(l=20, r=40, t=50, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            if is_korean:
                if not vk_history:
                    st.warning("⚠️ 최근 VKOSPI 히스토리 데이터를 가져오지 못해 과거 차트 분석에 VIX 지수를 대신 사용했습니다. (오늘 수치는 정상 반영)")
                st.caption("※ 안내: 분석을 위한 과거 변동성/공포 지표는 미국 VIX 지수가 대용으로 일괄 매핑되었습니다.")
            
            # 하단에 자산군 판별 상세 정보 안내 (요청에 따라 상세 내용 복구)
            st.info(f"🔍 **자동 판별 알림**: 이 종목은 **[{cat_name}]** 자산군입니다. (기준: MDD {th['mdd3']}% / 회복률 {th['rec_th']}% 이상 시 3단계 진단)")

            with st.expander("📖 매수 시점 판별 기준 및 지표 상세 설명 보기"):
                st.markdown(f"""
                <div style='line-height: 1.7; font-size: 0.95rem;'>
                <b>1️⃣ 개별 지표 상세 기준 (현재 자산군: {cat_name})</b><br>
                <ul>
                    <li><b>역사적 회복률 (통계적 바닥)</b>: 과거 전체 데이터 중 현재보다 낙폭이 적었던 비율. <br>
                        <span style='color:#ef4444; font-weight:bold;'>🔴 {th['rec_th']}% 이상</span> (역사적 하위 10~20% 수준의 강력한 바닥 인증)</li>
                    <li><b>MDD (최대 낙폭)</b>: 52주 최고점 대비 하락률. <br>
                        <span style='color:#ef4444; font-weight:bold;'>🔴 {th['mdd3']}% 이하</span> (강한 약세장) / <span style='color:#eab308; font-weight:bold;'>🟡 {th['mdd1']}% 이하</span> (단기 조정)</li>
                    <li><b>{fear_idx_name} 지수 (변동성)</b>: 시장의 공포 심리. <br>
                        <span style='color:#ef4444; font-weight:bold;'>🔴 35 이상</span> (패닉 셀링 구간) / <span style='color:#eab308; font-weight:bold;'>🟡 22 이상</span> (변동성 확대)</li>
                    <li><b>RSI (14일)</b>: 주가 매수/매도 강도. <br>
                        <span style='color:#ef4444; font-weight:bold;'>🔴 30 이하</span> (강력 과매도) / <span style='color:#eab308; font-weight:bold;'>🟡 40 이하</span> (단기 과매도)</li>
                    <li><b>장기 추세선 ({ma_days}일선)</b>: 큰 추세의 꺾임 여부 확인. <br>
                        <span style='color:#ef4444; font-weight:bold;'>🔴 하향 이탈</span> (역배열 진입) / <span style='color:#10b981; font-weight:bold;'>🟢 안정 유지</span> (상승 추세)</li>
                </ul>
                <br>
                <b>2️⃣ 시스템 매수 구간 단계별 판별 조합 (역사적 회복률 충족 시 인증마크 부여)</b><br>
                <div style='background-color:#fee2e2; padding:10px; border-radius:8px; margin-bottom:8px;'>
                <span style='color:#ef4444; font-weight:bold;'>🔴 3단계 (시스템 투매 국면) - "찐 저점 포착"</span><br>
                조건: (<b>MDD {th['mdd3']}% 이하</b> AND <b>VIX 35 이상</b>) OR (<b>MDD {th['mdd_tail']}% 이하</b> AND <b>투매용 꼬리 거래량 발생</b>)
                </div>
                <div style='background-color:#ffedd5; padding:10px; border-radius:8px; margin-bottom:8px;'>
                <span style='color:#f97316; font-weight:bold;'>🟠 2단계 (약세장 투매 구간) - "비중 대폭 확대"</span><br>
                조건: <b>MDD {th['mdd2']}% 이하</b> AND (<b>VIX 30 이상</b> OR <b>RSI 30 이하</b>)
                </div>
                <div style='background-color:#fef9c3; padding:10px; border-radius:8px; margin-bottom:8px;'>
                <span style='color:#eab308; font-weight:bold;'>🟡 1단계 (단기 조정 구간) - "비중 일부 확대"</span><br>
                조건: <b>MDD {th['mdd1']}% 이하</b> AND (<b>VIX 22 이상</b> OR <b>RSI 40 이하</b>)
                </div>
                <div style='background-color:#f1f5f9; padding:10px; border-radius:8px;'>
                <span style='color:#64748b; font-weight:bold;'>💤 0단계 (관망/정기 매수 구간)</span><br>
                조건: 위 조건에 해당하지 않는 평시 상태. (역사적 회복률 {th['rec_th']}% 미달 시에도 매수 신호는 정상 출력되나 인증마크는 제외됨)
                </div>
                </div>
                """, unsafe_allow_html=True)

def render_c_indicator_section():
    st.markdown("### 📊 CI 지수")
    st.markdown("현재 주가가 과거 장기 성장 추세에 비추어 볼 때 어느 정도의 고평가 또는 저평가 상태인지 직관적으로 보여주는 지표입니다.")

    col1, col2 = st.columns([1, 3])
    with col1:
        ticker = st.text_input("종목", value=st.session_state.get("c_ind_ticker", "나스닥"), key="c_ind_ticker")

    if ticker.strip():
        with st.spinner("지표를 계산하고 통계를 불러오는 중입니다..."):
            res = calculate_c_indicator(ticker)
            
        if "error" in res:
            st.error(res["error"])
        else:
            display_name = res["display_name"]
            norm_ticker = res["norm_ticker"]
            
            # 과거 시계열 확률 밴드 데이터 계산
            df_plot = calculate_c_indicator_history(norm_ticker, res["S0"], res["mu"], res["sigma"], res["start_date"])

            years_approx = res['t'] // 252
            
            st.markdown(f"#### {display_name} CI 가격 밴드 차트 (전체 {years_approx}년 상장 기간)")
            fig_ci = go.Figure()
            if not df_plot.empty:
                # 7단계 색상 설정 (유저 요청: 이전처럼 예전 채도 낮고 매끄러운 3원색 트랜지션)
                colors = {
                    "75_100": {"fill": "rgba(33, 150, 243, 0.35)", "line": "rgba(33, 150, 243, 0.70)"}, # 초저평가 (파랑 강하게)
                    "625_75": {"fill": "rgba(33, 150, 243, 0.20)", "line": "rgba(33, 150, 243, 0.50)"}, # 지나친 저평가
                    "55_625": {"fill": "rgba(33, 150, 243, 0.08)", "line": "rgba(33, 150, 243, 0.30)"}, # 약간의 저평가
                    "45_55":  {"fill": "rgba(76, 175, 80, 0.15)",  "line": "rgba(76, 175, 80, 0.40)"},  # 적정 (초록)
                    "375_45": {"fill": "rgba(244, 67, 54, 0.08)", "line": "rgba(244, 67, 54, 0.30)"}, # 약간의 고평가
                    "25_375": {"fill": "rgba(244, 67, 54, 0.20)", "line": "rgba(244, 67, 54, 0.50)"}, # 지나친 고평가
                    "0_25":   {"fill": "rgba(244, 67, 54, 0.35)", "line": "rgba(244, 67, 54, 0.70)"}  # 초고위험 (빨강 강하게)
                }
                
                fig_ci.add_trace(go.Scatter(x=df_plot["Date"], y=df_plot["Band_01"], mode="lines", line=dict(width=1, color=colors["75_100"]["line"]), showlegend=False, hoverinfo="skip"))
                fig_ci.add_trace(go.Scatter(x=df_plot["Date"], y=df_plot["Band_25"], mode="lines", fill="tonexty", fillcolor=colors["75_100"]["fill"], line=dict(width=1, color=colors["75_100"]["line"]), name="75~100% (초저평가)", hoverinfo="skip"))
                fig_ci.add_trace(go.Scatter(x=df_plot["Date"], y=df_plot["Band_375"], mode="lines", fill="tonexty", fillcolor=colors["625_75"]["fill"], line=dict(width=1, color=colors["625_75"]["line"]), name="62.5~75% (지나친 저평가)", hoverinfo="skip"))
                fig_ci.add_trace(go.Scatter(x=df_plot["Date"], y=df_plot["Band_45"], mode="lines", fill="tonexty", fillcolor=colors["55_625"]["fill"], line=dict(width=1, color=colors["55_625"]["line"]), name="55~62.5% (약간의 저평가)", hoverinfo="skip"))
                fig_ci.add_trace(go.Scatter(x=df_plot["Date"], y=df_plot["Band_55"], mode="lines", fill="tonexty", fillcolor=colors["45_55"]["fill"], line=dict(width=1, color=colors["45_55"]["line"]), name="45~55% (확률상 적정범위)", hoverinfo="skip"))
                fig_ci.add_trace(go.Scatter(x=df_plot["Date"], y=df_plot["Band_625"], mode="lines", fill="tonexty", fillcolor=colors["375_45"]["fill"], line=dict(width=1, color=colors["375_45"]["line"]), name="37.5~45% (약간의 고평가)", hoverinfo="skip"))
                fig_ci.add_trace(go.Scatter(x=df_plot["Date"], y=df_plot["Band_75"], mode="lines", fill="tonexty", fillcolor=colors["25_375"]["fill"], line=dict(width=1, color=colors["25_375"]["line"]), name="25~37.5% (지나친 고평가)", hoverinfo="skip"))
                fig_ci.add_trace(go.Scatter(x=df_plot["Date"], y=df_plot["Band_99"], mode="lines", fill="tonexty", fillcolor=colors["0_25"]["fill"], line=dict(width=1, color=colors["0_25"]["line"]), name="0~25% (초고위험)", hoverinfo="skip"))
                
                fig_ci.add_trace(go.Scatter(x=df_plot["Date"], y=df_plot["Median"], mode="lines", line=dict(color="#059669", width=2, dash="dash"), name="장기 중앙 추세선", hoverinfo="skip"))
                fig_ci.add_trace(go.Scatter(x=df_plot["Date"], y=df_plot["Price"], mode="lines", line=dict(color="#111827", width=2), name="실제 주가", customdata=df_plot["CI_Percentile"], hovertemplate="주가: %{y:,.0f}<br>CI 지수: %{customdata:.1f}%<extra></extra>"))

                import math
                # 오른쪽 끝 밴드 선에 맞춰 퍼센트만 심플하게 텍스트로 표시 (자석 정렬)
                bands = [
                    (math.log10(df_plot["Band_99"].iloc[-1]), "0%"),
                    (math.log10(df_plot["Band_75"].iloc[-1]), "25%"),
                    (math.log10(df_plot["Band_625"].iloc[-1]), "37.5%"),
                    (math.log10(df_plot["Band_55"].iloc[-1]), "45%"),
                    (math.log10(df_plot["Band_45"].iloc[-1]), "55%"),
                    (math.log10(df_plot["Band_375"].iloc[-1]), "62.5%"),
                    (math.log10(df_plot["Band_25"].iloc[-1]), "75%"),
                    (math.log10(df_plot["Band_01"].iloc[-1]), "100%")
                ]
                for y_val, text in bands:
                    fig_ci.add_annotation(
                        x=1.01, y=y_val, xref="paper", yref="y", text=text,
                        xanchor="left", yanchor="middle", showarrow=False, 
                        font=dict(size=11, color="#64748b")
                    )
            
            fig_ci.update_layout(
                height=650, margin=dict(l=0, r=40, t=30, b=10), # 퍼센트 텍스트(예: 37.5%)가 들어갈 만큼만 우측 여백 최소화
                yaxis=dict(title="주가 (Log Scale)", type="log", tickformat=",.0f"),
                xaxis=dict(
                    hoverformat="%Y-%m-%d",
                    rangeselector=dict(
                        buttons=list([
                            dict(count=1, label="1년", step="year", stepmode="backward"),
                            dict(count=3, label="3년", step="year", stepmode="backward"),
                            dict(count=5, label="5년", step="year", stepmode="backward"),
                            dict(count=10, label="10년", step="year", stepmode="backward"),
                            dict(step="all", label="전체(Max)")
                        ])
                    ),
                    rangeslider=dict(
                        visible=True,
                        thickness=0.08,
                        bgcolor="rgba(240, 244, 248, 0.5)",
                        bordercolor="rgba(200, 200, 200, 0.3)"
                    ),
                    type="date"
                ),
                template="plotly_white",
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.3,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=12),
                    traceorder="reversed" # 위험도가 가장 큰 부분부터 순서대로
                ),
                hovermode="x unified"
            )
            st.plotly_chart(fig_ci, use_container_width=True)

            st.markdown("#### 🧭 요약 및 지표")
            sum_cols = st.columns(4)
            with sum_cols[0]:
                with st.container(border=True):
                    st.markdown(f"<div style='font-size:0.875rem; color:#6b7280; margin-bottom:0.1rem;'>{display_name} 현재가</div><div style='font-size:1.5rem; font-weight:700;'>{res['current_price']:,.2f}</div>", unsafe_allow_html=True)
            with sum_cols[1]:
                with st.container(border=True):
                    st.markdown(f"<div style='font-size:0.875rem; color:#6b7280; margin-bottom:0.1rem;'>현재 중앙 적정가</div><div style='font-size:1.5rem; font-weight:700;'>{res['median_price']:,.2f}</div>", unsafe_allow_html=True)
            with sum_cols[2]:
                with st.container(border=True):
                    st.markdown(f"<div style='font-size:0.875rem; color:#6b7280; margin-bottom:0.1rem;'>CI 지수</div><div style='font-size:1.5rem; font-weight:700; color:{res['color']};'>{res['ci_val']:.1f} <span style='font-size:1rem; font-weight:600;'>({res['status']})</span></div>", unsafe_allow_html=True)
            with sum_cols[3]:
                with st.container(border=True):
                    wait_y = res.get('wait_years', 0)
                    wait_text = f"약 {wait_y:.1f}년 소요" if wait_y > 0 else "저평가 (대기 불필요)"
                    tooltip = "현재 주가가 중앙 적정가 수준으로 하락할 경우, 장기 성장 복리를 통해 원금을 회복할 때까지 걸리는 예상 시간입니다."
                    st.markdown(f"<div style='font-size:0.875rem; color:#6b7280; margin-bottom:0.1rem;' title='{tooltip}'>원금 회복 대기 기간</div><div style='font-size:1.5rem; font-weight:700;'>{wait_text}</div>", unsafe_allow_html=True)
            
            ci_v = res['ci_val']
            if ci_v <= 25:
                s_ratio, c_ratio, action_txt = 20, 80, "적극적 이익 실현 및 현금 확보 (리스크 관리)"
            elif ci_v <= 37.5:
                s_ratio, c_ratio, action_txt = 30, 70, "주식 비중 축소 및 보수적 대응"
            elif ci_v <= 45:
                s_ratio, c_ratio, action_txt = 40, 60, "신규 매수 자제, 보유 종목 관망"
            elif ci_v <= 55:
                s_ratio, c_ratio, action_txt = 50, 50, "중립 (정기적인 적립식 매수 유지)"
            elif ci_v <= 62.5:
                s_ratio, c_ratio, action_txt = 65, 35, "점진적인 주식 비중 확대"
            elif ci_v <= 75:
                s_ratio, c_ratio, action_txt = 85, 15, "적극적인 분할 매수 (저점 매수 기회)"
            else:
                s_ratio, c_ratio, action_txt = 100, 0, "강력 매수 (공포 장세에서의 과감한 진입)"
                
            st.markdown(f"""
            <div style='margin-top:15px; padding: 16px; background-color: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;'>
                <div style='font-size: 1.05rem; color: #0f172a; font-weight: 700; margin-bottom: 12px;'>🤖 CI 지수 기반 맞춤형 자산 배분 가이드</div>
                <div style='display: flex; height: 28px; border-radius: 6px; overflow: hidden; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);'>
                    <div style='width: {s_ratio}%; background-color: #3b82f6; display: flex; align-items: center; justify-content: center; color: white; font-size: 0.85rem; font-weight: 700;'>📈 주식 {s_ratio}%</div>
                    <div style='width: {c_ratio}%; background-color: #10b981; display: flex; align-items: center; justify-content: center; color: white; font-size: 0.85rem; font-weight: 700;'>💵 현금 {c_ratio}%</div>
                </div>
                <div style='font-size: 0.95rem; color: #334155;'><strong>💡 추천 전략:</strong> {action_txt}</div>
            </div>
            """, unsafe_allow_html=True)

            st.caption(f"* 분석 기간: 전체 상장 기간 {res['t']:,} 거래일 (약 {res['t'] // 252}년) | 기준가(S0): {res['S0']:,.2f} | 일일 평균수익률(μ): {res['mu']:.6f} | 일일 변동성(σ): {res['sigma']:.6f}")


# -----------------------------
# 메인 앱
# -----------------------------

def main():
    st.set_page_config(
        page_title="주식 분석 & 포트폴리오 대시보드",
        layout="wide",
    )

    if "settings_loaded" not in st.session_state:
        _settings = load_settings()
        for k, v in _settings.items():
            if k in ["cmp_start", "cmp_end", "sim_start", "sim_end"]:
                try:
                    st.session_state[k] = dt.date.fromisoformat(v)
                except:
                    pass
            else:
                st.session_state[k] = v
        st.session_state.settings_loaded = True

    st.markdown(TAX_BADGE_CSS, unsafe_allow_html=True)

    st.title("📊 주식 분석 & 포트폴리오 대시보드")
    st.caption(
        "파이썬 + Streamlit + yfinance 기반으로 시장 지표, 내 자산, 종목 비교 분석을 한 번에 보는 대시보드입니다."
    )

    render_market_dashboard()
    st.markdown("---")
    render_portfolio_section()
    st.markdown("---")
    render_comparison_section()
    st.markdown("---")
    render_simulation_section()
    st.markdown("---")
    render_timing_section()
    st.markdown("---")
    render_c_indicator_section()
    
    sync_settings()


if __name__ == "__main__":
    main()

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
    "네이버": "035420.KQ",
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
    """현재가 및 전일 대비 정보."""
    for cand in ticker_candidates(ticker):
        ticker_obj = yf.Ticker(cand)
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
    
    end_date = dt.date.today()
    start_date = end_date - dt.timedelta(days=int(50 * 365.25))
    
    data = yf.download(norm_ticker, start=start_date, end=end_date, progress=False)
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

            cols = st.columns([3, 2, 2, 1])
            with cols[0]:
                if i == 0:
                    st.markdown("<div style='font-size:0.875rem; color:#6b7280; font-weight:600; margin-bottom:5px;'>종목</div>", unsafe_allow_html=True)
                raw_symbol = st.text_input(
                    "종목",
                    value=str(item.get("종목", "")),
                    key=f"card_symbol_{card_id}",
                    placeholder="예: QQQ, 삼성전자, 005930",
                    label_visibility="collapsed"
                )
            with cols[1]:
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
            with cols[2]:
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
            with cols[3]:
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

            next_cards.append({"id": card_id, "종목": raw_symbol, "평단가": float(avg), "수량": float(qty), "buy_fx": buy_fx})
        
        if delete_index is not None:
            deleted_card = next_cards.pop(delete_index)
            for key in [f"card_symbol_{deleted_card['id']}", f"card_avg_{deleted_card['id']}", f"card_qty_{deleted_card['id']}", f"card_del_{deleted_card['id']}"]:
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
                    {"id": str(uuid.uuid4()), "종목": "", "평단가": 0.0, "수량": 0.0, "buy_fx": usd_krw if usd_krw > 0 else 1300.0}
                )
                save_portfolio(st.session_state.portfolio_cards)
                st.rerun()
        with btn_cols[1]:
            if st.button("🗑️ 전체 삭제", use_container_width=True):
                for card in st.session_state.portfolio_cards:
                    card_id = card.get("id")
                    for key in [f"card_symbol_{card_id}", f"card_avg_{card_id}", f"card_qty_{card_id}", f"card_del_{card_id}"]:
                        if key in st.session_state:
                            del st.session_state[key]
                st.session_state.portfolio_cards = []
                save_portfolio([])
                st.rerun()

    if not st.session_state.portfolio_cards:
        st.info("자산이 없습니다. `자산 추가` 버튼으로 자산을 등록해 주세요.")
        return

    # Process and Summary Section
    rows = [(c["종목"].strip(), c["평단가"], c["수량"], c["buy_fx"]) for c in st.session_state.portfolio_cards if c["종목"].strip() and c["평단가"] > 0 and c["수량"] > 0]

    if not rows:
        st.info("종목 이름, 평단가, 수량을 올바르게 입력해 주세요.")
        return

    if usd_krw <= 0:
        st.warning("원/달러 환율(USDKRW)을 가져오지 못했습니다. 미국 자산의 원화 환산·총합이 부정확할 수 있습니다.")

    sum_cost_krw = 0.0
    sum_value_krw = 0.0
    asset_results = []
    error_messages = []

    for raw, avg, qty, buy_fx in rows:
        sym = normalize_ticker(raw)
        quote = fetch_latest_quote(sym) if sym else {}
        if not quote:
            error_messages.append(raw)
            continue

        resolved_symbol = quote.get("symbol", sym)
        display_name = fetch_symbol_name(resolved_symbol)
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
        
        asset_results.append({
            "name": display_name,
            "kr": kr,
            "avg": avg,
            "qty": qty,
            "cur": cur,
            "val_krw": val_krw,
            "pnl_krw": pnl_krw,
            "pnl_pct": (pnl_krw / cost_krw * 100) if cost_krw else 0.0
        })

    if error_messages:
        for err in error_messages:
            st.warning(f"'{err}': 가격 데이터를 가져오지 못했습니다. 종목 이름이나 코드를 확인해 주세요.")

    if not asset_results:
        return

    # Portfolio Summary Display
    total_pnl_krw = sum_value_krw - sum_cost_krw
    total_pct = (total_pnl_krw / sum_cost_krw * 100) if sum_cost_krw > 0 else 0.0

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📊 내 포트폴리오 결과 요약")
    
    color = "#d32f2f" if total_pnl_krw > 0 else "#1976d2" if total_pnl_krw < 0 else "inherit"
    with st.container(border=True):
        st.markdown(f"<div style='font-size:1.1rem; color:#6b7280; font-weight:600; margin-bottom:10px;'>총 평가 자산 (원화 기준)</div>", unsafe_allow_html=True)
        t_c1, t_c2, t_c3 = st.columns(3)
        with t_c1:
            st.markdown(f"<div style='font-size:0.9rem; color:#6b7280;'>총 매수 금액</div><div style='font-size:1.6rem; font-weight:700;'>{sum_cost_krw:,.0f}원</div>", unsafe_allow_html=True)
        with t_c2:
            st.markdown(f"<div style='font-size:0.9rem; color:#6b7280;'>총 평가 금액</div><div style='font-size:1.6rem; font-weight:700;'>{sum_value_krw:,.0f}원</div>", unsafe_allow_html=True)
        with t_c3:
            st.markdown(f"<div style='font-size:0.9rem; color:#6b7280;'>총 수익</div><div style='font-size:1.6rem; font-weight:700; color:{color};'>{total_pnl_krw:+,.0f}원 ({total_pct:+.2f}%)</div>", unsafe_allow_html=True)

    if usd_krw > 0:
        st.caption(f"적용 환율: 1 USD = {usd_krw:,.2f} KRW (자산별 매수 시점 환율 별도 적용)")

    if asset_results:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### 개별 자산 상세")
        for res in asset_results:
            p_color = "#d32f2f" if res['pnl_krw'] > 0 else "#1976d2" if res['pnl_krw'] < 0 else "inherit"
            with st.container(border=True):
                d_c1, d_c2, d_c3, d_c4 = st.columns([1.5, 1, 1, 1])
                with d_c1:
                    type_badge = "🇰🇷 한국" if res['kr'] else "🇺🇸 미국"
                    st.markdown(f"**{res['name']}** <span style='font-size:0.8rem; background:#e5e7eb; padding:2px 6px; border-radius:4px;'>{type_badge}</span>", unsafe_allow_html=True)
                    if res['kr']:
                        st.markdown(f"<div style='font-size:0.85rem; color:#6b7280;'>평단가 {res['avg']:,.0f}원 / 현재가 {res['cur']:,.0f}원 / {res['qty']:g}주</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='font-size:0.85rem; color:#6b7280;'>평단가 ${res['avg']:,.2f} / 현재가 ${res['cur']:,.2f} / {res['qty']:g}주</div>", unsafe_allow_html=True)
                with d_c2:
                    st.markdown(f"<div style='font-size:0.85rem; color:#6b7280; text-align:right;'>평가액 (원화)</div><div style='font-size:1.1rem; font-weight:600; text-align:right;'>{res['val_krw']:,.0f}원</div>", unsafe_allow_html=True)
                with d_c3:
                    st.markdown(f"<div style='font-size:0.85rem; color:#6b7280; text-align:right;'>수익금 (원화)</div><div style='font-size:1.1rem; font-weight:600; color:{p_color}; text-align:right;'>{res['pnl_krw']:+,.0f}원</div>", unsafe_allow_html=True)
                with d_c4:
                    st.markdown(f"<div style='font-size:0.85rem; color:#6b7280; text-align:right;'>수익률 (원화)</div><div style='font-size:1.1rem; font-weight:600; color:{p_color}; text-align:right;'>{res['pnl_pct']:+.2f}%</div>", unsafe_allow_html=True)


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
            <div style='font-size: 1rem; color: #0f172a; font-weight: 700; margin-bottom: 8px;'>💡 저점매수를 위한 회복률 기준</div>
            <div style='font-size: 0.95rem; color: #334155; margin-bottom: 8px;'>개별종목 <strong>90%</strong> | ETF <strong>80%</strong></div>
            <div style='font-size: 0.85rem; color: #64748b; line-height: 1.4;'>
                * 위 표의 회복률은 조회하신 기간 동안 주가가 해당 MDD(최대낙폭)보다 <strong>상단(덜 하락한 상태)에 머무른 누적 확률 분포(CDF)</strong>를 의미합니다.<br>
                * 현재 낙폭 구간은 초록색 테두리로 표시됩니다. 회복률이 높은 구간일수록 저점매수의 신뢰도가 높아집니다.
            </div>
        </div>
        """, unsafe_allow_html=True)



def render_comparison_section():
    st.markdown("### 📊 종목 비교 분석 (수익률 & MDD)")

    st.markdown(
        "최대 **3개 종목**을 선택해 기간별 **누적 수익률**과 **최대 낙폭(MDD)**을 비교합니다.  \n"
        "- 한글 종목명(삼성전자, 애플 등) 또는 티커(AAPL, 005930)를 자유롭게 입력해 주세요.  \n"
        "- **소문자(aapl, msft 등)로 입력해도** 자동으로 인식됩니다.  \n"
        "- **1개 종목만 입력해도** 정상적으로 단독 분석 그래프가 표시됩니다.  \n"
        "- 💡 **참고:** 해외 주식(예: QQQ)의 비교 수익률은 환율 변동이 배제된 **달러(USD) 기준 순수 주가 상승률**입니다."
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


def run_investment_simulation(tickers_in: List[str], start_date: dt.date, end_date: dt.date, sim_type: str, amount: float, apply_tax: bool = False):
    fig = go.Figure()
    results = []
    valid_df_for_plot = None
    for raw_t in tickers_in:
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
        
        tax_amount = 0.0
        if apply_tax and not kr and profit > 2500000:
            tax_amount = (profit - 2500000) * 0.22
            
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
            "kr": kr
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
    col_title, col_chk = st.columns([0.7, 0.3])
    with col_title:
        st.markdown("#### 💰 시뮬레이션 결과 요약 (원화 기준)")
    with col_chk:
        st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
        st.checkbox("해외주식 양도소득세(22%) 적용", key="sim_apply_tax")
        
    for res in results:
        color = "#d32f2f" if res['profit_after_tax'] > 0 else "#1976d2" if res['profit_after_tax'] < 0 else "inherit"
        with st.container(border=True):
            line_color = res.get('line_color', '#111827')
            kr_badge = "🇰🇷 한국" if res.get('kr') else "🇺🇸 미국"
            st.markdown(f"**<span style='color:{line_color};'>■</span> {res['name']}** <span style='font-size:0.8rem; background:#e5e7eb; padding:2px 6px; border-radius:4px;'>{kr_badge}</span>", unsafe_allow_html=True)
            
            if apply_tax:
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.markdown(f"<div style='font-size:0.875rem; color:#6b7280; margin-bottom:0.1rem;'>총 투자 원금</div><div style='font-size:1.5rem; font-weight:600;'>{res['total_invested']:,.0f}원</div>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<div style='font-size:0.875rem; color:#6b7280; margin-bottom:0.1rem;'>최종 평가액</div><div style='font-size:1.5rem; font-weight:600;'>{res['final_value_after_tax']:,.0f}원</div>", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"<div style='font-size:0.875rem; color:#6b7280; margin-bottom:0.1rem;'>세전 수익금</div><div style='font-size:1.5rem; font-weight:600; color:{color};'>{res['profit']:+,.0f}원</div>", unsafe_allow_html=True)
                with col4:
                    tax_str = f"-{res['tax_amount']:,.0f}원" if res['tax_amount'] > 0 else "0원"
                    st.markdown(f"<div style='font-size:0.875rem; color:#6b7280; margin-bottom:0.1rem;'>예상 세금(22%)</div><div style='font-size:1.5rem; font-weight:600; color:#eab308;'>{tax_str}</div>", unsafe_allow_html=True)
                with col5:
                    st.markdown(f"<div style='font-size:0.875rem; color:#6b7280; margin-bottom:0.1rem;'>세후 수익률</div><div style='font-size:1.5rem; font-weight:600; color:{color};'>{res['profit_pct']:+.2f}%</div>", unsafe_allow_html=True)
            else:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"<div style='font-size:0.875rem; color:#6b7280; margin-bottom:0.1rem;'>총 투자 원금</div><div style='font-size:1.5rem; font-weight:600;'>{res['total_invested']:,.0f}원</div>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<div style='font-size:0.875rem; color:#6b7280; margin-bottom:0.1rem;'>최종 평가액</div><div style='font-size:1.5rem; font-weight:600;'>{res['final_value']:,.0f}원</div>", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"<div style='font-size:0.875rem; color:#6b7280; margin-bottom:0.1rem;'>수익금</div><div style='font-size:1.5rem; font-weight:600; color:{color};'>{res['profit_after_tax']:+,.0f}원</div>", unsafe_allow_html=True)
                with col4:
                    st.markdown(f"<div style='font-size:0.875rem; color:#6b7280; margin-bottom:0.1rem;'>수익률</div><div style='font-size:1.5rem; font-weight:600; color:{color};'>{res['profit_pct']:+.2f}%</div>", unsafe_allow_html=True)
        
    if valid_df_for_plot is not None:
        fig.add_trace(go.Scatter(x=valid_df_for_plot.index, y=valid_df_for_plot['Total Invested'].round(0), mode='lines', name='누적 투자금', line=dict(dash='dash', color='#9e9e9e'), hovertemplate='%{y:,.0f}원<extra></extra>'))
    fig.update_layout(
        title=f"투자 시뮬레이션 결과 ({sim_type}) - 원화(KRW)", 
        xaxis_title=None, 
        yaxis_title="금액 (원)", 
        hovermode="x unified", 
        template="plotly_white",
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
        showlegend=True # 단일 종목일 때도 범례 표시
    )
    st.plotly_chart(fig, use_container_width=True)


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
        
    sim_tickers = [sim_t1, sim_t2, sim_t3]
    valid_sim_tickers = [t.strip() for t in sim_tickers if t.strip()]
    
    apply_tax = st.session_state.get("sim_apply_tax", False)
    if valid_sim_tickers:
        run_investment_simulation(valid_sim_tickers, sim_start, sim_end, sim_type, amount, apply_tax)


def calculate_c_indicator_history(ticker: str, S0: float, mu: float, sigma: float, start_date: dt.date, years=5) -> pd.DataFrame:
    end_date = dt.date.today()
    plot_start = end_date - dt.timedelta(days=int(years * 365.25))
    data = yf.download(ticker, start=start_date, end=end_date, progress=False)
    if data.empty or "Close" not in data.columns:
        return pd.DataFrame()
    
    close = data["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close = close.dropna()
    
    plot_data = close[close.index >= pd.Timestamp(plot_start)]
    if plot_data.empty:
        return pd.DataFrame()
        
    t_series = pd.Series(np.arange(1, len(close) + 1), index=close.index)
    plot_t = t_series[plot_data.index]
    
    z_scores = (np.log(plot_data / S0) - mu * plot_t) / (sigma * np.sqrt(plot_t))
    percentiles = stats.norm.cdf(z_scores) * 100
    
    z_99 = stats.norm.ppf(0.99)
    z_75 = stats.norm.ppf(0.75)
    z_55 = stats.norm.ppf(0.55)
    z_45 = stats.norm.ppf(0.45)
    z_25 = stats.norm.ppf(0.25)
    z_01 = stats.norm.ppf(0.01)
    
    return pd.DataFrame({
        "Date": plot_data.index,
        "Price": plot_data.values,
        "CI_Percentile": 100.0 - percentiles,
        "Median": S0 * np.exp(mu * plot_t),
        "Band_99": S0 * np.exp(mu * plot_t + sigma * np.sqrt(plot_t) * z_99),
        "Band_75": S0 * np.exp(mu * plot_t + sigma * np.sqrt(plot_t) * z_75),
        "Band_55": S0 * np.exp(mu * plot_t + sigma * np.sqrt(plot_t) * z_55),
        "Band_45": S0 * np.exp(mu * plot_t + sigma * np.sqrt(plot_t) * z_45),
        "Band_25": S0 * np.exp(mu * plot_t + sigma * np.sqrt(plot_t) * z_25),
        "Band_01": S0 * np.exp(mu * plot_t + sigma * np.sqrt(plot_t) * z_01)
    })


def render_c_indicator_section():
    st.markdown("### 📊 CI 지수")
    st.markdown("나스닥 종합지수(^NDX)의 일일 종가를 몬테카를로 시뮬레이션 결과 중 하나로 가정하였을 때, 백분율 순위로 계량화한 것으로, 현재 시장의 확률상 적정성 평가에 활용할 수 있습니다.")

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
            df_plot = calculate_c_indicator_history(norm_ticker, res["S0"], res["mu"], res["sigma"], res["start_date"], years=50)

            st.markdown(f"#### {display_name} CI 지수 차트 (최근 50년)")
            fig_ci = go.Figure()
            if not df_plot.empty:
                # 옅은 반투명 배경 밴드 추가
                fig_ci.add_hrect(y0=45, y1=55, fillcolor="rgba(76, 175, 80, 0.15)", line_width=0, layer="below")
                fig_ci.add_hrect(y0=37.5, y1=45, fillcolor="rgba(244, 67, 54, 0.15)", line_width=0, layer="below")
                fig_ci.add_hrect(y0=55, y1=62.5, fillcolor="rgba(33, 150, 243, 0.15)", line_width=0, layer="below")

                # 3대 기준 실선 (상단: 빨강, 중앙: 초록, 하단: 파랑)
                fig_ci.add_hline(y=25, line_width=2.5, line_color="#d32f2f", opacity=0.8, layer="below")
                fig_ci.add_hline(y=50, line_width=2.5, line_color="#2e7d32", opacity=0.8, layer="below")
                fig_ci.add_hline(y=75, line_width=2.5, line_color="#1976d2", opacity=0.8, layer="below")

                # 실제 CI 지수 선 추가
                fig_ci.add_trace(go.Scatter(
                    x=df_plot["Date"], y=df_plot["CI_Percentile"],
                    mode="lines", line=dict(color="#111827", width=1.5),
                    name="CI 지수",
                    hovertemplate="%{x|%Y-%m-%d}<br>CI 지수: %{y:.1f}%<extra></extra>"
                ))
                
                # 우측 스택 바 레전드 (Shapes & Annotations)
                right_legend = [
                    (0, 25, '#d32f2f', '초고위험'),
                    (25, 37.5, '#ef5350', '지나친 고평가 구간'),
                    (37.5, 45, '#ffebee', '약간의 고평가 구간'),
                    (45, 55, '#e8f5e9', '확률상 적정범위'),
                    (55, 62.5, '#e3f2fd', '약간의 저평가 구간'),
                    (62.5, 75, '#64b5f6', '지나친 저평가 구간'),
                    (75, 100, '#1976d2', '초저평가')
                ]
                for y0, y1, color, text in right_legend:
                    fig_ci.add_shape(
                        type="rect", xref="paper", yref="y",
                        x0=1.01, x1=1.025, y0=y0, y1=y1, fillcolor=color, line=dict(width=0)
                    )
                    fig_ci.add_annotation(
                        x=1.035, y=(y0+y1)/2, xref="paper", yref="y", text=text,
                        xanchor="left", showarrow=False, font=dict(size=11, color="#475569")
                    )

            fig_ci.update_layout(
                height=550, margin=dict(l=0, r=160, t=30, b=0), # 우측 레전드를 위해 여백(r) 확보
                yaxis=dict(
                    title="CI 지수 (%)", range=[100, 0], 
                    tickvals=[0, 25, 37.5, 45, 55, 62.5, 75, 100],
                    ticktext=["0%", "25%", "37.5%", "45%", "55%", "62.5%", "75%", "100%"]
                ),
                template="plotly_white",
                showlegend=False
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
                    tooltip = "현재가로 매수 후 주가가 폭락하여 중앙 추세선으로 회귀하더라도, 시장의 장기 성장률에 의해 본전을 찾을 때까지 걸리는 시간입니다. 즉 미래의 수익을 몇 년치 미리 지불하고 있는지를 나타냅니다."
                    st.markdown(f"<div style='font-size:0.875rem; color:#6b7280; margin-bottom:0.1rem;' title='{tooltip}'>장기 추세선 도달 기간</div><div style='font-size:1.5rem; font-weight:700;'>{wait_text}</div>", unsafe_allow_html=True)
            
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

            st.caption(f"* 분석 기간: 최근 {res['t']:,} 거래일 (약 50년) | 기준가(S0): {res['S0']:,.2f} | 일일 평균수익률(μ): {res['mu']:.6f} | 일일 변동성(σ): {res['sigma']:.6f}")


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
    render_c_indicator_section()
    
    sync_settings()


if __name__ == "__main__":
    main()

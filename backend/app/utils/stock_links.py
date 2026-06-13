"""Build external platform links for stock codes."""


def get_market_prefix(code: str) -> str:
    """Determine market prefix for external URLs.

    Shanghai: codes starting with 6, 5
    Shenzhen: codes starting with 0, 3, 2
    Beijing:  codes starting with 4, 8, 9
    """
    if code.startswith(("6", "5")):
        return "sh"
    if code.startswith(("4", "8", "9")):
        return "bj"
    return "sz"


def get_stock_links(code: str) -> dict:
    """Get external platform URLs for a given stock code."""
    market = get_market_prefix(code)
    return {
        "eastmoney": f"https://quote.eastmoney.com/{market}{code}.html",
        "tonghuashun_web": f"https://stockpage.10jqka.com.cn/{code}/",
        "xueqiu": f"https://xueqiu.com/S/{market.upper()}{code}",
        "eastmoney_app": f"emqqstock://stock?code={market}{code}",
        "tonghuashun_app": f"ths://stock?code={code}",
        "xueqiu_app": f"xueqiu://stock/{market.upper()}{code}",
    }

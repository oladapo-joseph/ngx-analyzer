# analysis/recommender.py — Gemini-powered recommendation engine

from datetime import datetime
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os 

load_dotenv(".env")

_TEMPLATE = """
You are a financial analyst specialising in African equity markets.

Stock: {stock_details}
Buy Signals: {buy_signal}
Sell Signals: {sell_signal}
Date: {today}

Rules:
- Stock trades on NGX in NGN
- Signals from technical indicators (MACD/RSI/SMA)
- Assume no existing position

Respond in exactly this format (max 80 words):
Recommendation: [BUY / SELL]
Reason: <brief explanation>
"""


def generate_recommendation(
    buy_signal: dict,
    sell_signal: dict,
    stock_details: dict,
) -> str:
    prompt = PromptTemplate(
        input_variables=["buy_signal", "sell_signal", "stock_details", "today"],
        template=_TEMPLATE,
    )
    llm   = ChatAnthropic(temperature=0, model="claude-sonnet-4-6")
    chain = prompt | llm | StrOutputParser()

    return chain.invoke({
        "buy_signal":    buy_signal,
        "sell_signal":   sell_signal,
        "stock_details": stock_details,
        "today":         datetime.now().date(),
    })


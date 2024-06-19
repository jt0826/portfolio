import time
import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime
from pulldata import PullData, InvalidTickerException


def get_ticker_symbols():
    ticker_symbols = []
    position_matrix = []
    i = 0
    while True:
        i += 1
        ticker = input(f'Enter ticker symbol {i}: ')
        if not ticker:
            break
        position = float(input(f'Enter number of shares for ticker {i}: '))
        ticker_symbols.append(ticker)
        position_matrix.append(position)
        print(ticker_symbols, position_matrix)
    return ticker_symbols, position_matrix


def initialize_portfolio(ticker_symbols, position_matrix):
    initial_value = 0
    for ticker, position in zip(ticker_symbols, position_matrix):
        try:
            data = PullData(ticker)
            position_value = data.latest_price * position * data.foreignto_sgd
            initial_value += position_value
        except InvalidTickerException as e:
            print(e)
            st.write(e)
    return initial_value


def update_portfolio(ticker_symbols, position_matrix):
    portfolio_value = 0
    for ticker, position in zip(ticker_symbols, position_matrix):
        try:
            data = PullData(ticker)
            position_value = data.latest_price * position * data.foreignto_sgd
            portfolio_value += position_value
        except InvalidTickerException as e:
            print(e)
            st.write(e)
    return portfolio_value



def main():
    ticker_symbols, position_matrix = get_ticker_symbols()

    initial_value = initialize_portfolio(ticker_symbols, position_matrix)
    portfolio = 0
    timedata = []
    valuedata = []

    portfolio_value_display = st.empty()
    percent_change_display = st.empty()
    total_pl_display = st.empty()
    raw_pl_display = st.empty()
    plot_display = st.empty()
    ticker_displays = [st.empty() for _ in ticker_symbols]

    interval = 1

    while True:
        portfolio_old = portfolio
        portfolio = update_portfolio(ticker_symbols, position_matrix)

        if portfolio_old == 0:
            percent = 0
        else:
            percent = 100 * ((portfolio - portfolio_old) / portfolio_old)

        total_pl_percent = 100 * ((portfolio - initial_value) / initial_value)
        raw_pl = portfolio - initial_value

        total_pl_display.write(f"Total P/L %: {total_pl_percent:.2f}")
        raw_pl_display.write(f"Raw P/L: {raw_pl:.2f} SGD")

        if portfolio_old != portfolio:
            for i, (ticker, position) in enumerate(zip(ticker_symbols, position_matrix)):
                data = PullData(ticker)
                currency = data.currency
                ticker_displays[i].write(
                    f"Latest Price of {ticker} ({data.latest_time}): {data.latest_price:.2f} {currency}")
            portfolio_value_display.write(f"Portfolio Value: {portfolio:.2f} SGD")
            percent_change_display.write(f"Change: {percent:.2f} %")

        timedata.append(datetime.now().strftime("%H:%M:%S"))
        valuedata.append(portfolio)
        if len(timedata) > 60:
            timedata.pop(0)
            valuedata.pop(0)

        fig = px.line(pd.DataFrame(list(zip(timedata, valuedata)), columns=['time', 'value(SGD)']), x="time",
                      y="value(SGD)")

        plot_display.plotly_chart(fig, use_container_width=True)

        time.sleep(interval)


if __name__ == "__main__":
    main()

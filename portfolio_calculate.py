import time
import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime
from pulldata import PullData, InvalidTickerException
import subprocess


class NoInternetException(Exception):
    """Exception raised for no internet."""
    pass


def check_internet_connection():
    try:
        subprocess.check_output(["ping", "-c", "1", "8.8.8.8"])
        return True
    except subprocess.CalledProcessError:
        return False


def get_ticker_symbols():
    ticker_symbols = []
    position_matrix = []
    average_prices = []
    use_avg_price = input("Do you want to enter average prices for the tickers? (yes/no): ").strip().lower() == 'yes'
    timeperiod = int(input("Enter graph time period in seconds: ").strip())

    i = 0
    while True:
        i += 1
        ticker = input(f'Enter ticker symbol {i}: ')
        if not ticker:
            break
        while True:
            try:
                position = float(input(f'Enter number of shares for ticker {i}: '))
                ticker_symbols.append(ticker)
                position_matrix.append(position)
                if use_avg_price:
                    average_price = float(input(f'Enter average price for ticker {i}: '))
                    average_prices.append(average_price)
                else:
                    average_prices.append(None)
                break  # break out of the loop if input is valid
            except ValueError:
                print("Invalid input. Please enter valid numbers for shares and average price.")
                st.write("Invalid input. Please enter valid numbers for shares and average price.")

    return ticker_symbols, position_matrix, average_prices, use_avg_price, timeperiod


def initialize_portfolio(ticker_symbols, position_matrix, average_prices, use_avg_price):
    initial_value = 0
    for ticker, position, avg_price in zip(ticker_symbols, position_matrix, average_prices):
        try:
            data = PullData(ticker)
            if use_avg_price and avg_price is not None:
                position_value = avg_price * position * data.foreignto_sgd
            else:
                position_value = data.latest_price * position * data.foreignto_sgd
            initial_value += position_value
        except InvalidTickerException as e:
            print(e)
            st.write(e)
    return initial_value


def update_portfolio(ticker_symbols, position_matrix, average_prices, use_avg_price):
    portfolio_value = 0
    ticker_data = []
    for ticker, position, avg_price in zip(ticker_symbols, position_matrix, average_prices):
        try:
            data = PullData(ticker)
            current_value = data.latest_price * position * data.foreignto_sgd
            if use_avg_price and avg_price is not None:
                initial_investment = avg_price * position * data.foreignto_sgd
            else:
                initial_investment = data.latest_price * position * data.foreignto_sgd
            ticker_data.append((ticker, data.latest_price, data.currency, data.latest_time))
            portfolio_value += current_value
        except InvalidTickerException as e:
            print(e)
            st.write(e)
    return portfolio_value, ticker_data


def calculate_percent_change(new_value, old_value):
    if old_value == 0:
        return 0
    return 100 * ((new_value - old_value) / old_value)


def calculate_current_session_pl(portfolio, session_start_value):
    current_session_raw_pl = portfolio - session_start_value
    current_session_pl_percent = calculate_percent_change(portfolio, session_start_value)
    return current_session_raw_pl, current_session_pl_percent


def calculate_overall_pl(ticker_symbols, position_matrix, average_prices, use_avg_price):
    overall_pl_raw = 0
    overall_pl_percent = 0
    for ticker, position, avg_price in zip(ticker_symbols, position_matrix, average_prices):
        try:
            data = PullData(ticker)
            current_value = data.latest_price * position * data.foreignto_sgd
            if use_avg_price and avg_price is not None:
                initial_investment = avg_price * position * data.foreignto_sgd
            else:
                initial_investment = data.latest_price * position * data.foreignto_sgd
            overall_pl_raw += (current_value - initial_investment)
            overall_pl_percent += calculate_percent_change(current_value, initial_investment)
        except InvalidTickerException as e:
            print(e)
            st.write(e)
    return overall_pl_raw, overall_pl_percent


def display_streamlit_updates(portfolio, percent, current_session_raw_pl, current_session_pl_percent, total_pl_percent,
                              raw_pl, overall_pl_raw, overall_pl_percent, ticker_data, elements):
    elements['overall_pl_display'].write(f"Overall P/L (raw): {overall_pl_raw:.2f} SGD")
    elements['overall_percent_display'].write(f"Overall P/L (%): {overall_pl_percent:.2f} %")
    elements['total_pl_display'].write(f"Current Session P/L %: {current_session_pl_percent:.2f}")
    elements['raw_pl_display'].write(f"Current Session Raw P/L: {current_session_raw_pl:.2f} SGD")
    elements['portfolio_value_display'].write(f"Portfolio Value: {portfolio:.2f} SGD")
    elements['percent_change_display'].write(f"Change: {percent:.2f} %")

    for i, (ticker, latest_price, currency, latest_time) in enumerate(ticker_data):
        elements['ticker_displays'][i].write(f"Latest Price of {ticker} ({latest_time}): {latest_price:.2f} {currency}")


def main():
    if not check_internet_connection():
        raise NoInternetException("Check internet connection")

    ticker_symbols, position_matrix, average_prices, use_avg_price, timeperiod = get_ticker_symbols()

    initial_value = initialize_portfolio(ticker_symbols, position_matrix, average_prices, use_avg_price)
    session_start_value = update_portfolio(ticker_symbols, position_matrix, average_prices, use_avg_price)[0]
    portfolio = session_start_value
    timedata = []
    valuedata = []

    elements = {
        'overall_pl_display': st.empty(),
        'overall_percent_display': st.empty(),
        'total_pl_display': st.empty(),
        'raw_pl_display': st.empty(),
        'portfolio_value_display': st.empty(),
        'percent_change_display': st.empty(),
        'ticker_displays': [st.empty() for _ in ticker_symbols],
        'plot_display': st.empty()
    }

    interval = 1

    while True:
        portfolio_old = portfolio
        portfolio, ticker_data = update_portfolio(ticker_symbols, position_matrix, average_prices, use_avg_price)

        percent = calculate_percent_change(portfolio, portfolio_old)
        current_session_raw_pl, current_session_pl_percent = calculate_current_session_pl(portfolio,
                                                                                          session_start_value)
        total_pl_percent = calculate_percent_change(portfolio, initial_value)
        raw_pl = portfolio - initial_value
        overall_pl_raw, overall_pl_percent = calculate_overall_pl(ticker_symbols, position_matrix, average_prices,
                                                                  use_avg_price)

        display_streamlit_updates(portfolio, percent, current_session_raw_pl, current_session_pl_percent,
                                  total_pl_percent, raw_pl, overall_pl_raw, overall_pl_percent, ticker_data, elements)

        timedata.append(datetime.now().strftime("%H:%M:%S"))
        valuedata.append(portfolio)
        if len(timedata) > 600:
            timedata.pop(0)
            valuedata.pop(0)

        fig = px.line(pd.DataFrame(list(zip(timedata, valuedata)), columns=['time', 'value(SGD)']), x="time",
                      y="value(SGD)")
        elements['plot_display'].plotly_chart(fig, use_container_width=True)

        time.sleep(timeperiod)


if __name__ == "__main__":
    main()

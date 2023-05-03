import pandas as pd
import numpy as np
import yfinance as yf
import datetime
import streamlit as st

def read_stock_list(file):
    stock_list = pd.read_excel(file)
    return stock_list.iloc[:, 0].tolist()

def fetch_data(stock_list, index_ticker, start_date, interval="1mo"):
    stock_data = yf.download(stock_list, start=start_date, interval=interval)['Adj Close']
    index_data = yf.download(index_ticker, start=start_date, interval=interval)['Adj Close']
    return stock_data, index_data

def clean_data(stock_data):
    stock_returns = stock_data.pct_change()
    stock_returns = stock_returns.dropna(how='all')
    stock_returns = stock_returns.dropna(axis=1, how='any')
    return stock_returns

def calculate_beta(stock_returns, index_returns):
    beta_values = {}
    tickers = stock_returns.columns if isinstance(stock_returns, pd.DataFrame) else [stock_returns.name]

    for ticker in tickers:
        ticker_returns = stock_returns[ticker] if isinstance(stock_returns, pd.DataFrame) else stock_returns
        cov_matrix = np.cov(ticker_returns, index_returns)
        beta = cov_matrix[0][1] / cov_matrix[1][1]
        beta_values[ticker] = beta
    return beta_values

def get_bulk_stock_beta(stock_list, years_before, interval):
    index_ticker = '^GSPC'  # S&P 500 Index

    today = datetime.datetime.today()
    start_date = (today - datetime.timedelta(days=365 * years_before)).strftime('%Y-%m-%d')

    with st.spinner("Loading data..."):
        stock_data, index_data = fetch_data(stock_list, index_ticker, start_date, interval)
    stock_returns = clean_data(stock_data)
    index_returns = index_data.pct_change().dropna()
    beta_values = calculate_beta(stock_returns, index_returns)

    stock_beta = pd.DataFrame.from_dict(beta_values, orient='index', columns=['Beta'])
    st.write(f"Stocks upload: {len(stock_list)}")
    st.write(f"Sucess beta find: {stock_beta.shape[0]}")
    st.write("Beta values for the selected stocks:")
    st.dataframe(stock_beta)

    # Convert the DataFrame to CSV format
    csv = stock_beta.to_csv(index=True)

    st.download_button(label="Download data as CSV",
                        data=csv,
                        file_name='stock_beta.csv',
                        mime='text/csv',
                        )

def get_single_stock_beta(stock_ticker, years_before, interval):
    index_ticker = '^GSPC'  # S&P 500 Index

    today = datetime.datetime.today()
    start_date = (today - datetime.timedelta(days=365 * years_before)).strftime('%Y-%m-%d')

    with st.spinner("Loading data..."):
        stock_data, index_data = fetch_data(stock_ticker, index_ticker, start_date, interval)
    stock_returns = stock_data.pct_change().dropna()
    index_returns = index_data.pct_change().dropna()
    cov_matrix = np.cov(stock_returns, index_returns)
    beta = round((cov_matrix[0][1] / cov_matrix[1][1]),2)

    st.write(f"Beta value for the selected stock: {beta}")




def main():
    st.title("Stock Beta Calculator")
    
    option = st.sidebar.radio("Choose input method:", ("Single stock", "Excel upload"))

    years_before = 5
    interval = "1mo"

    if option == "Single stock":
        stock_ticker = st.text_input("Enter the stock ticker symbol:")
        if stock_ticker:
            get_single_stock_beta(stock_ticker, years_before, interval)

    elif option == "Excel upload":
        uploaded_file = st.file_uploader("Upload your stock list Excel file", type=["xlsx"])
        if uploaded_file is not None:
            stock_list = read_stock_list(uploaded_file)
            get_bulk_stock_beta(stock_list, years_before, interval)

    st.write("#Beta is compare with S&P 500 5 years data, only show beta value for the stock over 5 years")

if __name__ == "__main__":
    main()
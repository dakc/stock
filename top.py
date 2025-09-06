import matplotlib
# Set Japanese font before importing pyplot to avoid garbled text in plots
#matplotlib.rcParams['font.family'] = 'MS Gothic'

import numpy as np
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

def read_company_list(csv_path):
    """
    Read the CSV file containing all TSE companies and return codes and names.
    """
    df_csv = pd.read_csv(csv_path, encoding="utf-8-sig")
    codes = df_csv['コード'].astype(str).str.zfill(4)
    names = df_csv['銘柄名']
    return codes, names

def fetch_stock_data(codes, names):
    """
    Fetch stock data for each company and calculate required metrics.
    Returns a list of dictionaries (one per company).
    """
    results = []
    for code, name in zip(codes, names):
        ticker = f"{code}.T"
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="7d")
            hist = hist[hist['Volume'] > 0]
            hist = hist.tail(4)
            if len(hist) < 4:
                continue

            dates = hist.index.strftime('%Y-%m-%d').tolist()
            opens = hist['Open'].tolist()
            closes = hist['Close'].tolist()

            today_open = opens[-1]
            yesterday_close = closes[-2]
            diff1 = closes[-1] - opens[-2]
            diff2 = closes[-2] - opens[-3]
            diff3 = closes[-3] - opens[-4]
            percent_change = (diff1 / opens[-1]) * 100

            row = {
                'Stock Code': ticker,
                'Company Name': name,
                'today open price': today_open,
                'yesterday close price': yesterday_close,
                'Diff1': diff1,
                'Diff2': diff2,
                'Diff3': diff3,
                'Percent Change (last close vs first open)': percent_change,
                'Diff1_dates': f"close {dates[-1]} - open {dates[-2]}",
                'Diff2_dates': f"close {dates[-2]} - open {dates[-3]}",
                'Diff3_dates': f"close {dates[-3]} - open {dates[-4]}",
            }
            results.append(row)
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
    return results

def save_table_image(df, table_cols, out_path):
    """
    Save a DataFrame as a table image.
    """
    fig, ax = plt.subplots(figsize=(16, 4))
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)
    ax.axis('off')
    table = ax.table(
        cellText=df[table_cols].values,
        colLabels=df[table_cols].columns,
        cellLoc='center',
        loc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.auto_set_column_width(col=list(range(len(table_cols))))
    plt.tight_layout()
    plt.savefig(out_path, bbox_inches='tight')
    plt.close(fig)

def plot_diff_and_percent(df_top10, out_path):
    """
    Plot bar chart for Diff1/2/3 and line for percent change, with diff dates annotated.
    """
    # Create x_label for x-axis
    df_top10['x_label'] = df_top10['Stock Code'].str.replace('.T', '') + ' ' + df_top10['Company Name'].str[:3]
    diff_cols = ['Diff1', 'Diff2', 'Diff3']
    df_plot = df_top10.set_index('x_label')[diff_cols]

    fig, ax = plt.subplots(figsize=(12, 6))
    df_plot.plot(kind='bar', ax=ax)
    plt.title('Recent 3-Day Diff (Close - Previous Open) for Top 10 TSE Companies by Percent Change')
    plt.ylabel('Price Difference (JPY)')
    plt.xlabel('Company (Code + Name)')
    plt.xticks(rotation=45, ha='right')
    plt.legend(title='Diff')

    # Add percent change line (secondary y-axis)
    percent_change_float = df_top10['Percent Change (last close vs first open)'].astype(str).str.replace('%', '').astype(float)
    ax2 = ax.twinx()
    ax2.plot(df_top10['x_label'], percent_change_float, color='red', marker='o', label='Percent Change (%)', linewidth=2)
    ax2.set_ylabel('Percent Change (%)', color='red')
    ax2.tick_params(axis='y', labelcolor='red')

    # Remove duplicate legend
    if ax.get_legend() is not None:
        ax.get_legend().remove()
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper left')

    plt.tight_layout()
    plt.savefig(out_path)
    plt.show()

def main():
    # --- 1. Read company list ---
    csv_path = r"data.csv"
    codes, names = read_company_list(csv_path)

    # --- 2. Fetch stock data ---
    results = fetch_stock_data(codes, names)

    # --- 3. Convert to DataFrame and save all results ---
    df = pd.DataFrame(results)
    df.to_csv(r"tse_all_results.csv", index=False, encoding="utf-8-sig")

    # --- 4. Pick top 10 by percent change and save ---
    df_top10 = df.sort_values('Percent Change (last close vs first open)', ascending=False).head(10)
    df_top10.to_csv(r"tse_top10_results.csv", index=False, encoding="utf-8-sig")
    df_top10['Percent Change (last close vs first open)'] = df_top10['Percent Change (last close vs first open)'].map(lambda x: f"{x:.2f}%")
    print(df_top10)

    # --- 5. Save table image ---
    table_cols = [
        'Stock Code', 'Company Name', 'today open price', 'yesterday close price',
        'Diff1', 'Diff2', 'Diff3', 'Percent Change (last close vs first open)',
        'Diff1_dates', 'Diff2_dates', 'Diff3_dates'
    ]
    save_table_image(df_top10, table_cols, r"top10_tse_table.png")

    # --- 6. Plot and save diff/percent graph ---
    plot_diff_and_percent(df_top10, r"top10_tse_diff.png")

if __name__ == "__main__":
    main()

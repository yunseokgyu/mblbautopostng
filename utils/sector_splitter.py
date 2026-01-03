import json
import os

# Mapping of Tickers to Sectors (Approximate GICS 11 Sectors)
sector_map = {
    "Communication Services": ["GOOG", "GOOGL", "META", "NFLX", "DIS", "CMCSA", "T", "VZ", "TMUS", "CHTR", "WBD", "PARA", "FOX", "FOXA", "NWS", "NWSA", "OMC", "IPG", "EA", "TTWO", "LYV", "MTCH"],
    "Consumer Discretionary": ["AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "LOW", "BKNG", "TJX", "TGT", "F", "GM", "MAR", "HLT", "CMG", "YUM", "LULU", "ORLY", "AZO", "ROST", "EXPE", "RCL", "CCL", "NCLH", "MGM", "CZR", "WYNN", "LVS", "DPZ", "DRI", "LEN", "DHI", "PHM", "BBY", "ULTA", "TSCO", "GPC", "LKQ", "KMX", "Pool", "VFC", "UAA", "UA", "TPR", "RL", "PVH", "HOG", "HAS", "MAT", "WHR", "MHK"],
    "Consumer Staples": ["WMT", "PG", "COST", "KO", "PEP", "PM", "MO", "MDLZ", "EL", "CL", "KMB", "GIS", "SYY", "ADM", "STZ", "DG", "DLTR", "KR", "K", "HSY", "MKC", "CAG", "KHC", "J", "SJM", "TSN", "HRL", "CPB", "TAP", "BF.B", "MNST", "CHD", "CLX", "LW"],
    "Energy": ["XOM", "CVX", "COP", "SLB", "EOG", "PXD", "MPC", "PSX", "VLO", "OXY", "HES", "DVN", "HAL", "BKR", "KMI", "WMB", "OKE", "TRGP", "CTRA", "FANG", "MRO", "APA", "EQT"],
    "Financials": ["BRK.B", "JPM", "V", "MA", "BAC", "WFC", "SPGI", "GS", "MS", "BLK", "C", "AXP", "CB", "MMC", "PGR", "SCHW", "CME", "AON", "ICE", "USB", "PNC", "TFC", "COF", "TRV", "AFL", "AIG", "MET", "PRU", "BK", "ALL", "STT", "AMP", "DFS", "HIG", "FITB", "MTB", "RF", "KEY", "CFG", "HBAN", "NTRS", "CINF", "RJF", "PFG", "L", "GL", "WRB", "AJG", "BRO", "WTW", "AIZ", "ACGL", "EG", "RE", "JKHY", "FIS", "GPN", "FLT", "CPT", "MKTX", "MSCI", "NDAQ", "CBOE", "FDS", "MCO"],
    "Health Care": ["LLY", "UNH", "JNJ", "MRK", "ABBV", "TMO", "ABT", "PFE", "AMGN", "DHR", "ISRG", "ELV", "SYK", "GILD", "CVS", "VRTX", "REGN", "CI", "ZTS", "BDX", "BSX", "HCA", "BMY", "HUM", "MCK", "MDT", "EW", "COR", "CNC", "IQV", "A", "IDXX", "DXCM", "MTD", "RMD", "GEHC", "STE", "TFX", "BIO", "WST", "TECH", "ALGN", "COO", "HOLX", "LH", "DGX", "RVTY", "WAT", "CRL", "UHS", "VTR", "WELL", "PEAK", "MRNA", "BAX", "PODD", "ALB"],
    "Industrials": ["GE", "CAT", "UNP", "HON", "UPS", "BA", "DE", "LMT", "ADP", "RTX", "ETN", "WM", "MMM", "CSX", "NSC", "GD", "ITW", "EMR", "FDX", "NOC", "PH", "PCAR", "CARR", "OTIS", "JCI", "TT", "GWW", "FAST", "PAYX", "CTAS", "TDG", "LHX", "VRSK", "EFX", "URI", "AME", "RSG", "DOV", "SWK", "TXT", "HII", "LDOS", "WAB", "GATX", "XYL", "ROK", "CMI", "PCAR", "ODFL", "JBHT", "EXPD", "CHRW", "DAL", "UAL", "AAL", "LUV", "ALK"],
    "Information Technology": ["AAPL", "MSFT", "NVDA", "AVGO", "CSCO", "ACN", "ADBE", "CRM", "AMD", "ORCL", "INTC", "QCOM", "TXN", "IBM", "INTU", "AMAT", "NOW", "ADI", "LRCX", "MU", "KLAC", "SNPS", "CDNS", "PANW", "ROP", "NXPI", "APH", "FTNT", "ADSK", "MSI", "MCHP", "ON", "TEL", "IT", "ANSS", "CDW", "KEYS", "GLW", "HPE", "HPQ", "STX", "WDC", "NTAP", "TDY", "ZBRA", "SWKS", "QRVO", "TER", "TRMB", "PTC", "TYL", "EPAM", "AKAM", "FICO", "VRSN", "FFIV", "JNPR", "ANET", "ENPH", "FSLR", "SEDG", "PAYC"],
    "Materials": ["LIN", "SHW", "APD", "FCX", "ECL", "NUE", "DOW", "DD", "PPG", "CTVA", "MLM", "VMC", "STLD", "ALB", "FMC", "MOS", "CF", "EMN", "CE", "LYB", "IFF", "BALL", "AMCR", "WRK", "PKG", "IP", "SEE", "AVY"],
    "Real Estate": ["PLD", "AMT", "CCI", "EQIX", "PSA", "O", "SPG", "VICI", "DLR", "AVB", "EQR", "CSGP", "SBAC", "CBRE", "EXR", "MAA", "INVH", "IRM", "UDR", "ESS", "KIM", "REG", "HST", "BXP", "VTR", "WELL", "PEAK", "ARE", "FRT"],
    "Utilities": ["NEE", "DUK", "SO", "D", "SRE", "AEP", "PEG", "EXC", "XEL", "ED", "WEC", "ES", "EIX", "DTE", "ETR", "FE", "PPL", "AEE", "CMS", "CNP", "LNT", "EVRG", "ATO", "NI", "PNW", "NRG", "AES"]
}

def generate_files():
    base_dir = "stock_data"
    os.makedirs(base_dir, exist_ok=True)
    
    all_mapped = set()
    
    for sector, tickers in sector_map.items():
        # Create safe filename
        filename = "sp500_" + sector.lower().replace(" ", "_") + ".json"
        filepath = os.path.join(base_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(tickers, f, indent=2)
            
        print(f"✅ Generated {filename} ({len(tickers)} stocks)")
        all_mapped.update(tickers)

    # Load full list to check for 'Others'
    full_sp500_path = os.path.join(base_dir, "sp500.json")
    if os.path.exists(full_sp500_path):
        with open(full_sp500_path, 'r', encoding='utf-8') as f:
            full_list = set(json.load(f))
            
        others = list(full_list - all_mapped)
        if others:
            with open(os.path.join(base_dir, "sp500_others.json"), 'w', encoding='utf-8') as f:
                json.dump(others, f, indent=2)
            print(f"✅ Generated sp500_others.json ({len(others)} stocks)")

if __name__ == "__main__":
    generate_files()

import time
import os
import core
import sp500_loader

def process_batch(tickers, progress_callback=None, stop_event=None):
    """
    Process a list of tickers sequentially.
    
    Args:
        tickers: List of ticker strings.
        progress_callback: Function(current_index, total, message) to update UI.
        stop_event: Function() -> bool. If returns True, stop processing.
    """
    total = len(tickers)
    results = []
    
    for i, ticker in enumerate(tickers):
        if stop_event and stop_event():
            if progress_callback:
                progress_callback(i, total, "Stopped by user.")
            break
            
        ticker = ticker.strip().upper()
        
        # Check if report already exists
        report_path = f"reports/{ticker}.docx"
        if os.path.exists(report_path):
            msg = f"Skipping {ticker} (Report already exists)"
            print(msg)
            if progress_callback:
                progress_callback(i + 1, total, msg)
            continue
            
        try:
            msg = f"Processing {ticker}..."
            if progress_callback:
                progress_callback(i + 1, total, msg)
                
            # 1. Get Data
            html, filing_date = core.get_sec_data(ticker)
            if not html:
                print(f"[{ticker}] No data found.")
                continue
                
            # 2. Extract
            text = core.extract_sections(html)
            if not text:
                print(f"[{ticker}] Extraction failed.")
                continue
                
            # Wrapper to bubble up chunk progress
            def chunk_callback(current_chunk, total_chunks, msg):
                if progress_callback:
                    progress_callback(i + 1, total, f"[{ticker}] {msg}")

            # 3. Analyze (Full mode for better quality as requested)
            report = core.analyze_with_gemini(text, ticker, filing_date, progress_callback=chunk_callback, mode="full")
            
            if report:
                # 4. Financials
                income, balance, cashflow, info = core.get_financials(ticker)
                
                # 5. Save
                filename = core.save_to_word(ticker, report, filing_date, income, balance, cashflow, info)
                results.append(filename)
                
                # Rate limit sleep (important for free tier/API limits)
                time.sleep(2) 
                
                # Intermediate Callback (e.g., for batch downloads)
                if (i + 1) % 5 == 0:
                    if progress_callback:
                        progress_callback(i + 1, total, "BATCH_READY", results)
            
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            # Continue to next ticker even if one fails
            continue
            
    return results

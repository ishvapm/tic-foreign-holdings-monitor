# TIC Foreign Holdings Monitor
Monthly analysis of foreign holdings of US long-term securities using Treasury International Capital Form SLT, Table 1.

## Data
Source: US Department of the Treasury, *US Long-Term Securities Held by Foreign Residents*  
File: https://ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/slt_table1.txt  
Frequency: Monthly  
Units: Millions of US dollars

The source file is saved as `data/slt_table1_official.txt`. It contains positions, net US sales, and valuation changes for Treasury securities, agency bonds, corporate bonds, and equity.

## Analysis
- Monthly position changes by country and security type
- Transaction and valuation decomposition
- Rolling median absolute deviation scores
- Position-change reconciliation residuals
- Country concentration measures
- Country groups based on portfolio composition

Position-change alerts require an absolute robust z-score of at least 4 and a monthly change of at least $500 million. Residual alerts require both a $500 million difference and a difference equal to at least 5 percent of the prior position.

## Run
```powershell
python src/run_analysis.py
python -m unittest discover -s tests -v
```

The analysis uses the Python standard library.

## Files
- `artifacts/dashboard.html`: monthly summary
- `artifacts/research_brief.md`: current-period results
- `artifacts/anomaly_cases.csv`: review queue
- `artifacts/concentration_history.csv`: concentration measures by month
- `artifacts/portfolio_clusters.csv`: latest country group assignments
- `artifacts/tic_stress_monitor.db`: SQLite output

## Data notes
The transaction and valuation series begin in February 2023. Earlier missing values are retained as nulls. Country attribution may reflect the location of a custodian or intermediary. Residuals can also reflect revisions, rounding or adjustments not shown separately in Table 1.

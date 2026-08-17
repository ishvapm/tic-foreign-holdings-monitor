-- Highest-priority recent cases.
SELECT date,country,asset,signal,severity,ROUND(robust_z,2) robust_z,ROUND(residual_pct,2) residual_pct FROM anomaly_cases WHERE severity='HIGH' ORDER BY date DESC,ABS(robust_z) DESC;
-- Concentration trend and effective number of equally sized holders.
SELECT date,ROUND(hhi,4) hhi,ROUND(effective_number,1) effective_holders,ROUND(100*top5_share,1) top5_pct FROM concentration ORDER BY date;

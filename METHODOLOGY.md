# Methodology

## Position-change score
For each country and security type, the monthly dollar change is compared with the preceding 24 monthly changes:
`0.6745 × (current change − historical median) / median absolute deviation`
At least 12 prior observations are required. A record enters the review queue when the absolute score is at least 4 and the position changes by at least $500 million.

## Change reconciliation
For observations from February 2023 onward:
`residual = change in holdings − net US sales − valuation change`
A residual enters the review queue when it is at least $500 million in absolute value and at least 5 percent of the prior-month position.

## Concentration
Country shares are calculated from the sum of non-aggregate country rows. The Herfindahl-Hirschman Index is the sum of squared country shares. Its reciprocal is reported as the effective number of equally sized holders. The top-five share is reported separately.

## Country groups
Countries with at least $10 billion in total holdings are grouped using k-means on four portfolio shares: Treasuries, agency bonds, corporate bonds, and equity. Four initial centers are selected deterministically. Assignments are iterated until stable or 50 iterations are reached.

## Limitations
Country attribution may reflect custodial and financial-center activity. The February 2023 reporting change limits comparison of transactions and valuation changes with earlier periods. Alerts identify observations for review; they do not determine whether a published value is erroneous.

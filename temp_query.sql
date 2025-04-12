SELECT
    ds.deal_id,
    ds.target_name AS target,
    ds.acquiror_name AS acquiror,
    ds.rank_value AS deal_value
FROM deals_summary ds
ORDER BY ds.rank_value DESC
LIMIT 5;
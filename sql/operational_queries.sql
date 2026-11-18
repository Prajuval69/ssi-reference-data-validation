-- Synthetic SSI project: read-only operational query examples.

-- Prioritized unresolved exception queue.
SELECT e.exception_id,
       e.ssi_id,
       e.rule_id,
       e.severity,
       e.status,
       e.assigned_to,
       s.client_id,
       s.market,
       s.currency,
       e.detected_at
FROM exceptions AS e
JOIN ssi_records AS s ON s.record_id = e.record_id
WHERE e.status NOT IN ('RESOLVED', 'REJECTED')
ORDER BY CASE e.severity
           WHEN 'Critical' THEN 1
           WHEN 'High' THEN 2
           WHEN 'Medium' THEN 3
           WHEN 'Low' THEN 4
           ELSE 99
         END,
         e.detected_at,
         e.exception_id;

-- Validation failures by rule.
SELECT rule_id, rule_name, severity, COUNT(*) AS failure_count
FROM validation_results
WHERE result = 'FAIL'
GROUP BY rule_id, rule_name, severity
ORDER BY failure_count DESC, rule_id;

-- Audit history for one physical SSI record (bind :record_id in a client).
SELECT audit_id, action, old_state, new_state, performed_by, performed_at, reason
FROM audit_log
WHERE entity_type = 'SSI' AND entity_id = :record_id
ORDER BY performed_at, audit_id;


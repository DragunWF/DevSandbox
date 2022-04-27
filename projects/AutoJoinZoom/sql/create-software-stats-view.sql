CREATE VIEW software_stats AS
SELECT COUNT(tpo.id) AS times_program_opened, 
       COUNT(mj.id) AS meeting_joins_count
FROM times_program_opened tpo
LEFT JOIN meeting_joins mj ON tpo.id = mj.id
UNION ALL
SELECT COUNT(tpo.id), COUNT(mj.id)
FROM meeting_joins mj
LEFT JOIN times_program_opened tpo ON mj.id = tpo.id
WHERE tpo.id IS NULL
LIMIT 1
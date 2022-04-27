CREATE VIEW grouped_meeting_joins AS
SELECT m.id AS meeting_id,
       m.name AS meeting_name,
	   COUNT(mj.id) AS times_meeting_joined
FROM meetings m
JOIN meeting_joins mj ON mj.id = m.id
GROUP BY mj.id
WITH RECURSIVE family(process, started) AS (
    SELECT process, stamp FROM events
    WHERE host = :host AND process = :root AND kind = 'process'
    UNION
    SELECT child.process, child.stamp FROM events AS child
    JOIN family ON child.parent = family.process
    WHERE child.host = :host AND child.kind = 'process'
      AND child.stamp >= family.started AND child.stamp <= :until
)
SELECT e.id, e.stamp, e.kind, e.process, e.detail
FROM events AS e JOIN family ON family.process = e.process
WHERE e.host = :host AND e.stamp BETWEEN family.started AND :until
ORDER BY e.stamp, e.id;

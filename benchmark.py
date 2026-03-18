import timeit
import cProfile
import pstats
from sql_compare import canonicalize_common

def run_benchmark():
    sql = """
    SELECT
        a.id,
        b.name,
        c.value,
        d.status,
        e.timestamp
    FROM
        table_a a
    JOIN
        table_b b ON a.b_id = b.id
    LEFT JOIN
        table_c c ON a.c_id = c.id
    CROSS JOIN
        table_d d
    INNER JOIN
        table_e e ON b.e_id = e.id
    WHERE
        a.status = 'ACTIVE'
        AND b.type IN ('TYPE_1', 'TYPE_2', 'TYPE_3')
        AND c.value > 100
        AND d.flag = 1
        AND e.timestamp >= '2023-01-01'
    GROUP BY
        a.id, b.name, c.value, d.status, e.timestamp
    HAVING
        COUNT(a.id) > 1
    ORDER BY
        e.timestamp DESC, a.id ASC
    LIMIT 100;
    """

    # We create a larger string by duplicating the query logic slightly, or just running it many times
    large_sql = sql * 10

    # Measure execution time
    timer = timeit.Timer(lambda: canonicalize_common(large_sql))
    num_runs = 1000
    total_time = timer.timeit(number=num_runs)
    avg_time = (total_time / num_runs) * 1000 # Convert to ms

    print(f"Benchmark: {avg_time:.4f} ms per call")

    # Profile the function
    profiler = cProfile.Profile()
    profiler.enable()
    for _ in range(100):
        canonicalize_common(large_sql)
    profiler.disable()

    stats = pstats.Stats(profiler).sort_stats('cumtime')
    stats.print_stats(15)

if __name__ == "__main__":
    run_benchmark()

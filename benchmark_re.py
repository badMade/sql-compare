import timeit
import sql_compare

# Sample SQL string with excessive whitespace
sql_string = "   SELECT   a,   b,   c   FROM   table   WHERE   x   =   1   AND   y   =   2   " * 100

def benchmark():
    sql_compare.collapse_whitespace(sql_string)

if __name__ == "__main__":
    t = timeit.timeit(benchmark, number=10000)
    print(f"Time taken: {t:.4f} seconds")

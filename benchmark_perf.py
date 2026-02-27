import timeit
import sql_compare
import random
import string

def generate_test_string(size=100000):
    # Create a string with random words and lots of whitespace
    words = ["SELECT", "FROM", "WHERE", "AND", "OR", "JOIN", "INNER", "OUTER", "LEFT", "RIGHT", "ON", "GROUP", "BY", "ORDER", "LIMIT"]
    res = []
    for _ in range(size // 5):
        res.append(random.choice(words))
        # Inject random whitespace
        res.append(" " * random.randint(1, 10))
        if random.random() < 0.1:
            res.append("\n" * random.randint(1, 3))
        if random.random() < 0.1:
            res.append("\t" * random.randint(1, 3))
    return "".join(res)

test_str = generate_test_string()
print(f"Generated test string of length {len(test_str)}")

def benchmark():
    sql_compare.collapse_whitespace(test_str)

if __name__ == "__main__":
    # Warmup
    benchmark()

    # Measure
    number = 100
    time_taken = timeit.timeit(benchmark, number=number)
    print(f"Time taken for {number} iterations: {time_taken:.4f} seconds")
    print(f"Average time per iteration: {time_taken/number:.6f} seconds")

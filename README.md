## Why?

I recently found that PHP `break` accepts an optional numeric argument which tells it how many nested enclosing structures are to be broken out of. 

I thought it would be nice to have similar functionality in Python.

We all have written code like following at least once

```python
result = []
for row in grid:
    valid = False
    for col in row:
        if some_method(row, col, result):
            valid = True
            break
    if valid:
        break
```

Wouldn't it be nice to just break both loops with a single statement?

## Do you need it?

Kinda, but not really. There are many ways to deal with it when you want to exit all the enclosing loops. But `breakn` is useful when you need to exit only a few loops amongst many nested loops.

```python
# refactor the logic inside a function and return
def foo():
    result = []
    for row in range(num_rows):
        for col in range(num_cols):
            if some_method(row, col, result):
                return result
```

```python
# flatten the loops if possible, into a single loop
from itertools import product

result = []
for row, col in product(range(num_rows), range(num_cols)):
    if some_method(row, col, result):
        break
```

## Usage

```python
from breakn.breaker import breaker


@breaker
def find_n_submatrices(matrix, n, N, M, K, T):
    """
    find top left corner of first 'n' K x K submatrices where all cells are >= T
    """
    results = []
    for i in range(N - K + 1):
        for j in range(M - K + 1):
            valid = True
            for x in range(K):
                for y in range(K):
                    if matrix[i + x][j + y] < T:
                        valid = False
                        breakn(2)
            if valid:
                results.append((i, j))
            if len(results) == n:
                breakn(2)
    return results


matrix = [
    [6, 7, 5, 8, 9],
    [5, 4, 6, 7, 8],
    [7, 8, 5, 6, 7],
    [6, 7, 8, 9, 4]
]
N = 4
M = 5
K = 2
T = 5
n = 4
print(find_n_submatrices(matrix, n, N, M, K, T))  # prints [(0, 2), (0, 3), (1, 2), (1, 3)]
```

### Limitations

- Only works with `for` loops
- Breaks `for-else`

> PS - I just wrote this for fun, so there might be many breaking cases.
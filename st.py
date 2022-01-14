from time import perf_counter

items = ["a"] * 100000


st = perf_counter()
for i in range(100):
    "".join(i for i in items)
print(perf_counter() - st)

st = perf_counter()
for i in range(100):
    "".join([i for i in items])
print(perf_counter() - st)

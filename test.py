def flatten(l : list) -> list:
    newList : list = []
    for item in l:
        if not isinstance(item, list):
            newList.append(item)
        else:
            for extraItem in flatten(item):
                newList.append(extraItem)
    return newList

testlist = [[1, 9], [None for _ in range(8)]]
print(testlist, len(flatten(testlist)))
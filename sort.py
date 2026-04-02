def merge(left, right):
    new = []
    L, R = 0, 0

    while L < len(left) and R < len(right):
        if left[L] <= right[R]:
            new.append(left[L])
            L += 1
        else:
            new.append(right[R])
            R += 1

    new.extend(left[L:])
    new.extend(right[R:])

    return new

def merge_sort(alist):
    b = alist.copy()
    if len(b) <= 1:
        return b

    middle = len(b) // 2
    left = b[:middle]
    right = b[middle:]

    left = merge_sort(left)
    right = merge_sort(right)
    return merge(left, right)
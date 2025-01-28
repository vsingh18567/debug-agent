def quicksort(arr):
    if len(arr) <= 1:  # Changed from == 0 to <= 1
        return arr

    pivot = arr[0]

    left = [x for x in arr[1:] if x < pivot]
    right = [x for x in arr[1:] if x >= pivot]

    return quicksort(left) + [pivot] + quicksort(right)


if __name__ == "__main__":
    test_arr = [3, 3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
    print("Original array:", test_arr)
    sorted_arr = quicksort(test_arr)
    print("Sorted array:", sorted_arr)
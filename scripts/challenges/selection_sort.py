from rich import print


def selection_sort(unsorted: list):
    list_count = len(unsorted)
    min_num_index = None
    for i in range(list_count):
        min_num_index = i
        for j in range(i, list_count):
            if unsorted[j] < unsorted[min_num_index]:
                min_num_index = j
        temp = unsorted[i]
        unsorted[i] = unsorted[min_num_index]
        unsorted[min_num_index] = temp


def main():
    nums = [5, 2, 0, 9, 3, 4, 1, 6, 8]
    print(f"Unsorted: {nums}")
    selection_sort(nums)
    print(f"Sorted: {nums}")


main()

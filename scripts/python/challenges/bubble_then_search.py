import random
from rich import print


def bubble_sort(arr: list) -> list:
    for i in range(len(arr)):
        for j in range(len(arr) - i - 1):
            if arr[j] > arr[j + 1]:
                temp = arr[j + 1]
                arr[j + 1] = arr[j]
                arr[j] = temp
    return arr


def binary_search(arr: list, element: int) -> int:
    if not element in arr:
        return -1

    high, low = len(arr) - 1, 0
    mid = high // 2
    while True:
        if element == arr[mid]:
            return mid
        if element > arr[mid]:
            low = mid + 1
        if element < arr[mid]:
            high = mid - 1
        mid = (low + high) // 2


def generate_random_array(length: int) -> list:
    output = []
    for i in range(length):
        output.append(random.randint(1, 30))
    return output


def stringify(array: int) -> list:
    return list(map(str, array))


def main():
    array = generate_random_array(10)
    sorted_array = bubble_sort([*array])
    print(f"Original Array: {' '.join(stringify(array))}\nSorted Array: {' '.join(stringify(sorted_array))}")

    element_to_search = 15
    element_index = binary_search(sorted_array, element_to_search)
    print(f"Index of {element_to_search}: {element_index if element_index != -1 else 'None'}")


main()

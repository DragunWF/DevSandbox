/*
    Problem Statement:
    Make a function which accepts an array of integers and 
    a number x, the function should calculate the maximum sum 
    of x consecutive elements in the array
*/

function maxConsecutiveSumArr(arr, x) {
  let maxSum = 0;
  for (let i = 0; i < arr.length; i++) {
    let sum = 0;
    for (let j = i, k = 1; j < arr.length && k <= x; j++, k++) {
      sum += arr[j];
    }
    if (sum > maxSum) {
      maxSum = sum;
    }
  }
  return maxSum;
}

function test() {
  console.log(maxConsecutiveSumArr([1, 2, 3, 4, 5], 3));
}

test();

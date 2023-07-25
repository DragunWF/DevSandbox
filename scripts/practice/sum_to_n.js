const n = 6;

function sumNumbers(n) {
  let sum = 0;
  for (let i = 1; i <= n; i++) {
    sum += i;
  }
  return sum;
}

function sumNumbersConstantTime(n) {
  return (n * (n + 1)) / 2;
}

console.log(sumNumbers(n));
console.log(sumNumbersConstantTime(n));

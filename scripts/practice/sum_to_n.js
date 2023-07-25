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

function showResult(func, arg) {
  const t1 = performance.now();
  console.log(`Result: ${func(arg)}`);
  const t2 = performance.now();
  console.log(`Time to execute: ${(t2 - t1) / 1000} seconds`);
}

function main() {
  const n = 6;
  const wall = "----------------------";
  console.log(`n = ${n}`);

  console.log(`${wall}\nFirst Function (Iteration)`);
  showResult(sumNumbers, n);
  console.log(`${wall}\nSecond Function (Formula)`);
  showResult(sumNumbersConstantTime, n);
}

main();

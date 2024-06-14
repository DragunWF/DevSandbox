// https://www.youtube.com/shorts/wY3kUe1qhWM

function isPowerOfFour(n) {
  let result = 4;
  let exponent = 2;
  while (result < n) {
    result = result ** exponent;
    exponent++;
  }
  return result === n;
}

function test() {
  const testCases = [16, 4, 24, 84];
  for (let i = 0, j = 1; i < testCases.length; i++, j++) {
    console.log(`Test Case #${j}: ${isPowerOfFour(testCases[i])}`);
  }
}

test();

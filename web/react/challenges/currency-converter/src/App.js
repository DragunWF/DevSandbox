// `https://api.frankfurter.app/latest?amount=100&from=EUR&to=USD`

import { useState, useEffect } from "react";

export default function App() {
  const [output, setOutput] = useState(null);
  const [amount, setAmount] = useState("");
  const [currencyType1, setCurrencyType1] = useState("USD");
  const [currencyType2, setCurrencyType2] = useState("USD");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(
    function () {
      const controller = new AbortController();

      async function convertCurrency() {
        try {
          if (!amount) {
            setOutput("OUTPUT");
            return;
          }
          if (currencyType1 === currencyType2) {
            setOutput(`${amount} ${currencyType2}`);
            return;
          }

          setIsLoading(true);
          const res = await fetch(
            `https://api.frankfurter.app/latest?amount=${amount}&from=${currencyType1}&to=${currencyType2}`,
            { signal: controller.signal }
          );

          if (!res.ok) {
            throw new Error(
              "Something went wrong with the currency conversion"
            );
          }

          const data = await res.json();
          console.log(data);
          const currencyKey = Object.keys(data.rates)[0];
          const convertedAmount = data.rates[currencyKey];

          setOutput(`${convertedAmount} ${currencyType2}`);
          setIsLoading(false);
        } catch (err) {
          setOutput("OUTPUT");
        }
      }

      convertCurrency();

      return function () {
        controller.abort();
      };
    },
    [amount, currencyType1, currencyType2]
  );

  return (
    <div>
      <input type="number" onChange={(e) => setAmount(e.target.value)} />
      <select
        onChange={(e) => setCurrencyType1(e.target.value)}
        disabled={isLoading}
      >
        <option value="USD">USD</option>
        <option value="EUR">EUR</option>
        <option value="CAD">CAD</option>
        <option value="INR">INR</option>
      </select>
      <select
        onChange={(e) => setCurrencyType2(e.target.value)}
        disabled={isLoading}
      >
        <option value="USD">USD</option>
        <option value="EUR">EUR</option>
        <option value="CAD">CAD</option>
        <option value="INR">INR</option>
      </select>
      <p>{output !== null ? output : "OUTPUT"}</p>
    </div>
  );
}

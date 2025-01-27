import { useState } from "react";

const ratings = [
  { text: "Dissatisfied (0%)", rating: 0 },
  { text: "It was okay (5%)", rating: 0.05 },
  { text: "It was good (10%)", rating: 0.1 },
  { text: "Absolutely amazing! (20%)", rating: 0.2 },
];
const DEFAULT_RATING = ratings[0].rating;

function App() {
  const [bill, setBill] = useState(0);
  const [serviceRating, setServiceRating] = useState(DEFAULT_RATING);
  const [friendServiceRating, setFriendServiceRating] =
    useState(DEFAULT_RATING);

  function toFixedIfNecessary(value, decimalPlaces) {
    return +value.toFixed(decimalPlaces);
  }

  function handleReset() {
    setBill(0);
    setServiceRating(DEFAULT_RATING);
    setFriendServiceRating(DEFAULT_RATING);
  }

  const ratingAverage = (serviceRating + friendServiceRating) / 2;
  const tipAmount = bill * ratingAverage;
  const finalBill = bill + tipAmount;

  return (
    <div>
      <BillInput bill={bill} setBill={setBill} />
      <TipPercentageInput rating={serviceRating} setRating={setServiceRating}>
        How did you like the service?
      </TipPercentageInput>
      <TipPercentageInput
        rating={friendServiceRating}
        setRating={setFriendServiceRating}
      >
        How did your friend like the service?
      </TipPercentageInput>
      {bill !== 0 ? (
        <h1>{`You pay $${finalBill} ($${bill} + $${toFixedIfNecessary(
          tipAmount,
          2
        )} tip)`}</h1>
      ) : (
        ""
      )}
      {bill !== 0 ? <button onClick={handleReset}>Reset</button> : ""}
    </div>
  );
}

function BillInput({ bill, setBill }) {
  return (
    <div>
      <label>How much was the bill?</label>
      <input
        type="number"
        onChange={(e) => setBill(Number(e.target.value))}
        value={bill}
      />
    </div>
  );
}

function TipPercentageInput({ rating, setRating, children }) {
  return (
    <div>
      <label>{children}</label>
      <select
        value={rating}
        onChange={(e) => setRating(Number(e.target.value))}
      >
        {ratings.map((rating) => (
          <option key={rating.text} value={rating.rating}>
            {rating.text}
          </option>
        ))}
      </select>
    </div>
  );
}

export default App;

import { useState } from "react";
import "./styles.css";

const faqs = [
  {
    title: "Where are these chairs assembled?",
    text: "Lorem ipsum dolor sit amet consectetur, adipisicing elit. Accusantium, quaerat temporibus quas dolore provident nisi ut aliquid ratione beatae sequi aspernatur veniam repellendus.",
  },
  {
    title: "How long do I have to return my chair?",
    text: "Pariatur recusandae dignissimos fuga voluptas unde optio nesciunt commodi beatae, explicabo natus.",
  },
  {
    title: "Do you ship to countries outside the EU?",
    text: "Excepturi velit laborum, perspiciatis nemo perferendis reiciendis aliquam possimus dolor sed! Dolore laborum ducimus veritatis facere molestias!",
  },
];

export default function App() {
  return (
    <div className="accordion">
      <Accordion items={faqs} />
    </div>
  );
}

function Accordion({ items }) {
  const [currentlyOpenAccordionNum, setCurrentlyOpen] = useState(1);

  return (
    <div>
      {items.map((item, i) => (
        <AccordionItem
          currentlyOpen={currentlyOpenAccordionNum}
          onOpen={setCurrentlyOpen}
          num={i + 1}
          title={item.title}
          key={item.title}
        >
          {item.text}
        </AccordionItem>
      ))}
      <AccordionItem
        currentlyOpen={currentlyOpenAccordionNum}
        onOpen={setCurrentlyOpen}
        num={43}
        title="Dragun Members"
        key="Dragun Members"
      >
        <p>History of the members of the Dragun Developer Team</p>
        <ul>
          <li>Marc</li>
          <li>Jay</li>
          <li>Gidan</li>
          <li>Isaac</li>
          <li>Bastian</li>
        </ul>
      </AccordionItem>
    </div>
  );
}

function AccordionItem({ currentlyOpen, onOpen, num, title, children }) {
  const isOpen = num === currentlyOpen;

  function handleToggle() {
    onOpen(isOpen ? null : num);
  }

  return (
    <div className={`item ${isOpen ? "open" : ""}`} onClick={handleToggle}>
      <p className="number">{num <= 9 ? `0${num}` : num}</p>
      <p className="title">{title}</p>
      <p className="icon">{isOpen ? "-" : "+"}</p>
      {isOpen && <div className="content-box">{children}</div>}
    </div>
  );
}

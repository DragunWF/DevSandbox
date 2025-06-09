import styles from "./Button.module.css";

function Button({ children, onClick, type }) {
  return (
    <button
      type={type}
      onClick={onClick}
      className={`${styles.btn} ${styles[type]}`}
    >
      {children}
    </button>
  );
}

export default Button;

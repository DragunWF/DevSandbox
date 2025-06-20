import { useState, useRef } from "react";
import { Modal, StyleSheet, View, Button, Text, FlatList } from "react-native";
import GuessCard from "./GuessCard";
import GameOverView from "./GameOverView";

function GameView({ isVisible, correctNumber, onCancelGame, onGameWon }) {
  const minNumber = useRef(1);
  const maxNumber = useRef(100);

  const [guesses, setGuesses] = useState([]);
  const [guessedNumber, setGuessedNumber] = useState(null);
  const [warningMessage, setWarningMessage] = useState("");
  const [isGameOver, setGameOver] = useState(false);

  const [finalGuessCount, setFinalGuessCount] = useState(0);

  function handleHigherButtonClick() {
    if (correctNumber > guessedNumber) {
      // User says "Higher" - AI should guess higher numbers
      const newMinNumber = guessedNumber + 1;
      minNumber.current = newMinNumber;
      guessNumber(newMinNumber, maxNumber);
    } else {
      setWarningMessage("⚠️ Number should be lower! ⚠️");
    }
  }

  function handleLowerButtonClick() {
    if (correctNumber < guessedNumber) {
      // User says "Lower" - AI should guess lower numbers
      const newMaxNumber = guessedNumber - 1;
      maxNumber.current = newMaxNumber;
      guessNumber(minNumber, newMaxNumber);
    } else {
      setWarningMessage("⚠️ Number should be higher! ⚠️");
    }
  }

  function handleCancelGameButtonClick() {
    // TODO: Add other functionality
    onCancelGame();
  }

  function guessNumber(updatedMinNumber, updatedMaxNumber) {
    // Fixed random number generation to include max number
    const newGuessedNumber = Math.floor(
      Math.random() * (updatedMaxNumber - updatedMinNumber + 1) +
        updatedMinNumber
    );
    setGuesses((current) => [...current, newGuessedNumber]);
    setWarningMessage("");

    if (newGuessedNumber === correctNumber) {
      setGameOver(true);
      resetGame();
      onGameWon();
    } else {
      setGuessedNumber(newGuessedNumber);
    }
  }

  function resetGame() {
    minNumber.current = 1;
    maxNumber.current = 1;
    setWarningMessage("");
    setGuesses([]);
  }

  if (guessedNumber == null) {
    guessNumber(minNumber.current, maxNumber.current);
  }

  return (
    <Modal visible={isVisible} animationType="slide">
      <GameOverView isVisible={isGameOver} guessCount={finalGuessCount} />

      <View style={styles.viewContainer}>
        <View style={styles.gameContainer}>
          <Text style={styles.textHeader}>Opponent's Guess</Text>
          <View style={styles.opponentGuessContainer}>
            <Text style={styles.opponentGuessText}>{guessedNumber}</Text>
          </View>
          {warningMessage && (
            <Text style={styles.warningText}>{warningMessage}</Text>
          )}
          <View style={styles.gameButtonsContainer}>
            <Button title="Higher" onPress={handleHigherButtonClick} />
            <Button title="Lower" onPress={handleLowerButtonClick} />
          </View>
          <Button title="Cancel Game" onPress={handleCancelGameButtonClick} />
          <View style={styles.guessCardContainer}>
            <Text style={styles.guessTextHeader}>Guess Log</Text>
            <FlatList
              data={guesses}
              renderItem={(itemData) => {
                return (
                  <GuessCard order={itemData.index + 1} guess={itemData.item} />
                );
              }}
              keyExtractor={(item, index) => {
                return index;
              }}
            />
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  viewContainer: {
    backgroundColor: "#090040",
  },
  gameContainer: {
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    marginTop: 300,
  },
  opponentGuessContainer: {
    backgroundColor: "#471396",
    padding: 20,
    margin: 20,
    width: "70%",
    alignItems: "center",
    borderRadius: 100,
  },
  warningText: {
    color: "#ffcc00",
    padding: 10,
    marginBottom: 5,
    fontSize: 18,
  },
  opponentGuessText: {
    color: "#fff",
    fontSize: 50,
  },
  textHeader: {
    color: "#fff",
    fontSize: 34,
  },
  guessTextHeader: {
    color: "#fff",
    fontSize: 28,
    marginTop: 15,
    marginBottom: 15,
    textAlign: "center",
    border: "solid",
  },
  gameButtonsContainer: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    gap: 20,
    marginBottom: 10,
  },
});

export default GameView;

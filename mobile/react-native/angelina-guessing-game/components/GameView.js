import { useState } from "react";
import { Modal, StyleSheet, View, Button, Text, FlatList } from "react-native";
import GuessCard from "./GuessCard";

function GameView({ isVisible, correctNumber, onCancelGame, onGameWon }) {
  const [guesses, setGuesses] = useState([]);
  const [guessedNumber, setGuessedNumber] = useState(null);
  const [minNumber, setMinNumber] = useState(1);
  const [maxNumber, setMaxNumber] = useState(100);

  function handleHigherButton() {
    guessNumber();
  }

  function handleLowerButton() {
    guessNumber();
  }

  function guessNumber() {
    const newGuessedNumber = Math.floor(
      Math.random() * (maxNumber - minNumber) + minNumber
    );
    setGuesses((current) => [...current, newGuessedNumber]);
    if (newGuessedNumber === correctNumber) {
      //
    } else {
      setGuessedNumber(newGuessedNumber);
    }
  }

  if (guessedNumber == null) {
    guessNumber();
  }

  return (
    <Modal visible={isVisible} animationType="slide">
      <View style={styles.gameContainer}>
        <Text style={styles.textHeader}>Opponent's Guess</Text>
        <View style={styles.opponentGuessContainer}>
          <Text style={styles.opponentGuessText}>{guessedNumber}</Text>
        </View>
        <View style={styles.gameButtonsContainer}>
          <Button title="Higher" />
          <Button title="Lower" />
        </View>
        <Button title="Cancel Game" onPress={onCancelGame} />
        <View style={styles.guessCardContainer}>
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
    </Modal>
  );
}

const styles = StyleSheet.create({
  gameContainer: {
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#090040",
  },
  opponentGuessContainer: {
    backgroundColor: "#471396",
    padding: 20,
    margin: 20,
    width: "70%",
    alignItems: "center",
    borderRadius: 100,
  },
  opponentGuessText: {
    color: "#fff",
    fontSize: 50,
  },
  textHeader: {
    color: "#fff",
    fontSize: 34,
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

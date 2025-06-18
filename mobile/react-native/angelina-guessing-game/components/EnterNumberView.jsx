import { useState } from "react";
import { StyleSheet, View, Modal, TextInput, Text, Button } from "react-native";
import GameView from "./GameView";

function EnterNumberView({ isVisible, onGameWon, onCancelGame }) {
  const [enteredNumber, setEnteredNumber] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isGameOpen, setIsGameOpen] = useState(false);

  function handleNumberInput(userInput) {
    setEnteredNumber(userInput);
  }

  function handleSubmit() {
    const convertedNumber = Number(enteredNumber);
    if (convertedNumber <= 0) {
      setErrorMessage("Number cannot be 0 or negative!");
      handleResetInput();
    } else if (convertedNumber > 100) {
      setErrorMessage("Number cannot be greater than 100!");
      handleResetInput();
    } else {
      setIsGameOpen(true);
    }
  }

  function handleResetInput() {
    setEnteredNumber("");
  }

  return (
    <Modal visible={isVisible} animationType="fade">
      <GameView
        isVisible={isGameOpen}
        correctNumber={Number(enteredNumber)}
        onGameWon={onGameWon}
        onCancelGame={onCancelGame}
      />
      <View style={styles.viewContainer}>
        <Text style={styles.textHeader}>Enter your number!</Text>
        <TextInput
          style={styles.textInput}
          placeholder="Your secret number!"
          onChangeText={handleNumberInput}
          value={enteredNumber}
          keyboardType="number-pad"
        />
        {errorMessage && (
          <Text style={styles.errorMessage}>{errorMessage}</Text>
        )}
        <View style={styles.buttonContainer}>
          <Button title="Back" onPress={onCancelGame} />
          <Button title="Reset" onPress={handleResetInput} />
          <Button title="Submit" onPress={handleSubmit} />
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  viewContainer: {
    flex: 1,
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#471396",
  },
  buttonContainer: {
    marginTop: 15,
    flexDirection: "row",
    backgroundColor: "#fff",
    gap: 20,
    padding: 8,
    paddingLeft: 24,
    paddingRight: 24,
    borderRadius: 15,
  },
  errorMessage: {
    color: "#DC2525",
    fontSize: 19,
    marginTop: 10,
  },
  textHeader: {
    fontSize: 24,
    color: "#fff",
    marginBottom: 20,
  },
  textInput: {
    borderWidth: 1,
    borderColor: "#e4d0ff",
    backgroundColor: "#e4d0ff",
    color: "#120438",
    borderRadius: 6,
    width: "70%",
    padding: 16,
  },
});

export default EnterNumberView;

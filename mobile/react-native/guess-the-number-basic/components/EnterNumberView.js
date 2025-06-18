import { useState } from "react";
import { StyleSheet, View, Modal, TextInput, Text, Button } from "react-native";
import GameView from "./GameView";

function EnterNumberView({ isVisible, onGameWon, onCancelGame }) {
  const [enteredNumber, setEnteredNumber] = useState("");
  const [isGameOpen, setIsGameOpen] = useState(false);

  function handleNumberInput(userInput) {
    setEnteredNumber(userInput);
  }

  function handleSubmit() {}

  function handleResetInput() {
    setEnteredNumber("");
  }

  return (
    <Modal visible={isVisible} animationType="fade">
      <View style={styles.viewContainer}>
        <Text style={styles.textHeader}>Enter your number!</Text>
        <TextInput
          style={styles.textInput}
          placeholder="Your secret number!"
          onChangeText={handleNumberInput}
          value={enteredNumber}
        />
        <View style={styles.buttonContainer}>
          <Button title="Back" onPress={onCancelGame} />
          <Button title="Reset" onPress={handleResetInput} />
          <Button title="Submit" onPress={handleSubmit} />
        </View>
        <GameView
          isVisible={isGameOpen}
          onGameWon={onGameWon}
          onCancelGame={onCancelGame}
        />
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

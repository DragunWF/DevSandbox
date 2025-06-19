import { StyleSheet, View, Button, TextInput, Pressable } from "react-native";

import PrimaryButton from "../components/PrimaryButton";

function StartGameScreen() {
  return (
    <View>
      <TextInput />
      <PrimaryButton>Reset</PrimaryButton>
      <PrimaryButton>Confirm</PrimaryButton>
    </View>
  );
}

export default StartGameScreen;

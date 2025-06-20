import { StyleSheet, View, Text, Pressable } from "react-native";

function PrimaryButton({ children, onPress, style }) {
  return (
    <Pressable onPress={onPress}>
      <View style={[styles.buttonContainer, style]}>
        <Text style={styles.buttonText}>{children}</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  buttonContainer: {
    backgroundColor: "#537D5D",
    borderRadius: 15,
    borderWidth: 2,
    borderColor: "#405e47",
    elevation: 4,
    shadowColor: "black",
    shadowOffset: { width: 2, height: 2 },
    shadowRadius: 8,
    shadowOpacity: 0.5,
  },
  buttonText: {
    color: "white",
    padding: 10,
    textAlign: "center",
  },
});

export default PrimaryButton;

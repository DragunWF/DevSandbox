import { StyleSheet, View, Text } from "react-native";

function Title({ children, style }) {
  return <Text style={[styles.title, style]}>{children}</Text>;
}

const styles = StyleSheet.create({
  title: {
    fontFamily: "poppins-bold",
    fontSize: 22,
    color: "white",
    textAlign: "center",
  },
});

export default Title;

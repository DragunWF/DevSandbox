import { StatusBar } from "expo-status-bar";
import { StyleSheet, Text, View, SafeAreaView } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useFonts } from "expo-font";
import AppLoading from "expo-app-loading";

import Title from "./components/Title";
import CategoriesScreen from "./screens/CategoriesScreen";

export default function App() {
  const [fontsLoaded] = useFonts({
    poppins: require("./assets/fonts/Poppins-Regular.ttf"),
    "poppins-bold": require("./assets/fonts/Poppins-Bold.ttf"),
  });

  if (!fontsLoaded) {
    return <AppLoading />;
  }

  return (
    <LinearGradient style={styles.screen} colors={["#18230F", "#1F7D53"]}>
      <StatusBar style="light" />
      <SafeAreaView style={styles.screen}>
        <CategoriesScreen />
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
  },
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
});

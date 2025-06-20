import { useState } from "react";
import { StyleSheet, SafeAreaView, ImageBackground } from "react-native";
import { StatusBar } from "expo-status-bar";
import { LinearGradient } from "expo-linear-gradient";
import { useFonts } from "expo-font";
import AppLoading from "expo-app-loading";

import CategoriesScreen from "./screens/CategoriesScreen";
import MealListScreen from "./screens/MealListScreen";

export default function App() {
  const [isCategoriesScreenOpen, setIsCategoriesScreenOpen] = useState(true);
  const [isMealListScreenOpen, setIsMealListScreenOpen] = useState(false);
  const [selectedCategoryId, setSelectedCategoryId] = useState(null);

  const [fontsLoaded] = useFonts({
    poppins: require("./assets/fonts/Poppins-Regular.ttf"),
    "poppins-bold": require("./assets/fonts/Poppins-Bold.ttf"),
  });

  if (!fontsLoaded) {
    return <AppLoading />;
  }

  function selectCategoryHandler(categoryId) {
    setSelectedCategoryId(categoryId);
    setIsCategoriesScreenOpen(false);
    setIsMealListScreenOpen(true);
  }

  function backButtonHandler() {
    setSelectedCategoryId(null);
    setIsMealListScreenOpen(false);
    setIsCategoriesScreenOpen(true);
  }

  let screen;
  if (isCategoriesScreenOpen) {
    screen = <CategoriesScreen onSelectCategory={selectCategoryHandler} />;
  } else if (isMealListScreenOpen) {
    screen = (
      <MealListScreen
        onBackButtonPressed={backButtonHandler}
        categoryId={selectedCategoryId}
      />
    );
  }

  return (
    <LinearGradient style={styles.screen} colors={["#18230F", "#1F7D53"]}>
      <StatusBar style="light" />
      <ImageBackground
        source={require("./assets/images/background.jpg")}
        resizeMode="cover"
        style={styles.screen}
        imageStyle={styles.backgroundImage}
      >
        <SafeAreaView style={styles.screen}>{screen}</SafeAreaView>
      </ImageBackground>
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
  backgroundImage: {
    opacity: 0.35,
  },
});

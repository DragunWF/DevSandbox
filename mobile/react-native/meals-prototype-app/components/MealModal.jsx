import {
  StyleSheet,
  View,
  Modal,
  Text,
  SafeAreaView,
  ScrollView,
} from "react-native";

import TitleCard from "./TitleCard";
import { MEALS } from "../data/dummy-data";
import Card from "./Card";
import MealImage from "./MealImage";
import PrimaryButton from "./PrimaryButton";

function MealModal({ isVisible, mealId, onCloseButtonPressed }) {
  const meal = MEALS.filter((meal) => meal.id === mealId)[0];

  if (!isVisible || !Boolean(meal)) {
    return null;
  }

  function convert(boolValue) {
    return boolValue ? "Yes" : "No";
  }

  return (
    <Modal visible={isVisible} animationType="slide">
      <SafeAreaView style={styles.container}>
        <TitleCard>{meal.title}</TitleCard>
        <ScrollView>
          <MealImage source={meal.imageUrl} />
          <Card style={styles.mealCard}>
            <Text style={[styles.mealText, styles.firstMealText]}>
              Affordability: {meal.affordability}
            </Text>
            <Text style={styles.mealText}>Complexity: {meal.complexity}</Text>
            <Text style={styles.mealText}>
              Ingredients: {meal.ingredients.join(", ")}
            </Text>
            <Text style={styles.mealText}>
              Gluten Free: {convert(meal.isGlutenFree)}
            </Text>
            <Text style={styles.mealText}>Vegan: {convert(meal.isVegan)}</Text>
            <Text style={styles.mealText}>
              Vegetarian: {convert(meal.isVegetarian)}
            </Text>
            <Text style={styles.mealText}>
              Lactose: {convert(meal.isLactoseFree)}
            </Text>
          </Card>
          <View style={styles.buttonContainer}>
            <PrimaryButton
              onPress={onCloseButtonPressed}
              style={styles.closeButton}
            >
              Close
            </PrimaryButton>
          </View>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#5A827E",
  },
  mealCard: {
    margin: 15,
    alignItems: "flex-start",
  },
  firstMealText: {
    marginTop: 0,
  },
  mealText: {
    color: "white",
    textAlign: "left",
    marginTop: 10,
  },
  buttonContainer: {
    alignItems: "center",
    paddingBottom: 40,
  },
  closeButton: {
    width: "60%",
    paddingHorizontal: 80,
    paddingVertical: 2,
  },
});

export default MealModal;

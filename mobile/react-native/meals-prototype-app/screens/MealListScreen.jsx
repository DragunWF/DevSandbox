import { StyleSheet, View, Text, FlatList } from "react-native";

import { MEALS, CATEGORIES } from "../data/dummy-data";
import MealCard from "../components/MealCard";
import TitleCard from "../components/TitleCard";
import PrimaryButton from "../components/PrimaryButton";

function MealListScreen({ categoryId, onBackButtonPressed }) {
  const category = CATEGORIES.filter((item) => item.id === categoryId)[0];
  const meals = MEALS.filter((item) => item.categoryIds.includes(categoryId));

  return (
    <View style={styles.screen}>
      <View style={styles.titleContainer}>
        <TitleCard>{category.title}</TitleCard>
      </View>
      <View style={styles.mealsContainer}>
        <FlatList
          data={meals}
          renderItem={(itemData) => {
            return (
              <MealCard
                title={itemData.item.title}
                affordability={itemData.item.affordability}
                complexity={itemData.item.complexity}
              />
            );
          }}
          keyExtractor={(item) => item.id}
          alwaysBounceVertical={false}
          contentContainerStyle={styles.flatListContent}
        />
      </View>
      <View style={styles.buttonContainer}>
        <PrimaryButton onPress={onBackButtonPressed} style={styles.backButton}>
          Back
        </PrimaryButton>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
  },
  titleContainer: {
    // Add any specific styling for title if needed
  },
  mealsContainer: {
    flex: 1,
  },
  flatListContent: {
    paddingBottom: 80, // Add padding to prevent content from being hidden behind the button
  },
  buttonContainer: {
    position: "absolute",
    bottom: 20,
    left: 20,
    right: 20,
    backgroundColor: "transparent",
    justifyContent: "center",
    alignItems: "center",
  },
  backButton: {
    width: "70%",
    paddingHorizontal: 80,
    paddingVertical: 2,
  },
});

export default MealListScreen;

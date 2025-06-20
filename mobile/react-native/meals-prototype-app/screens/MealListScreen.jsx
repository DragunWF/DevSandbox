import { StyleSheet, View, Text, FlatList } from "react-native";

import { MEALS, CATEGORIES } from "../data/dummy-data";
import Title from "../components/Title";
import MealCard from "../components/MealCard";
import TitleCard from "../components/TitleCard";

function MealListScreen({ categoryId }) {
  const category = CATEGORIES.filter((item) => item.id === categoryId)[0];
  const meals = MEALS.filter((item) => item.categoryIds.includes(categoryId));

  return (
    <View>
      <TitleCard>{category.title}</TitleCard>
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
      />
    </View>
  );
}

const styles = StyleSheet.create({});

export default MealListScreen;

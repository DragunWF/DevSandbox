import { StyleSheet, View, Text, FlatList } from "react-native";

import CategoryCard from "../components/CategoryCard";
import TitleCard from "../components/TitleCard";
import { CATEGORIES } from "../data/dummy-data";

function CategoriesScreen({ onSelectCategory }) {
  return (
    <View style={styles.screen}>
      <TitleCard>Meal Categories</TitleCard>
      <View style={styles.categoriesContainer}>
        <FlatList
          data={CATEGORIES}
          renderItem={(itemData) => {
            return (
              <CategoryCard
                id={itemData.item.id}
                title={itemData.item.title}
                backgroundColor={itemData.item.color}
                onSelectCategory={onSelectCategory}
              />
            );
          }}
          keyExtractor={(item) => item.id}
          alwaysBounceVertical={false}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    justifyContent: "flex-start", // Align to top
    alignItems: "center",
  },
  categoriesContainer: {
    paddingBottom: 150,
  },
});

export default CategoriesScreen;

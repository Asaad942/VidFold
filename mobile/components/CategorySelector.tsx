import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, TextInput, ScrollView } from 'react-native';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { Colors } from '@/constants/Colors';

interface CategorySelectorProps {
  selectedCategories: string[];
  onCategoriesChange: (categories: string[]) => void;
}

export function CategorySelector({ selectedCategories, onCategoriesChange }: CategorySelectorProps) {
  const [newCategory, setNewCategory] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  const handleAddCategory = () => {
    if (!newCategory.trim()) return;
    
    const updatedCategories = [...selectedCategories, newCategory.trim()];
    onCategoriesChange(updatedCategories);
    setNewCategory('');
    setIsAdding(false);
  };

  const handleRemoveCategory = (category: string) => {
    const updatedCategories = selectedCategories.filter(c => c !== category);
    onCategoriesChange(updatedCategories);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Categories</Text>
      
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.categoriesContainer}
      >
        {selectedCategories.map((category) => (
          <View key={category} style={styles.categoryChip}>
            <Text style={styles.categoryText}>{category}</Text>
            <TouchableOpacity
              onPress={() => handleRemoveCategory(category)}
              style={styles.removeButton}
            >
              <IconSymbol name="xmark.circle.fill" size={16} color="#666" />
            </TouchableOpacity>
          </View>
        ))}
        
        {isAdding ? (
          <View style={styles.addCategoryContainer}>
            <TextInput
              style={styles.addCategoryInput}
              value={newCategory}
              onChangeText={setNewCategory}
              placeholder="New category"
              autoFocus
              onSubmitEditing={handleAddCategory}
              onBlur={() => setIsAdding(false)}
            />
          </View>
        ) : (
          <TouchableOpacity
            style={styles.addButton}
            onPress={() => setIsAdding(true)}
          >
            <IconSymbol name="plus.circle.fill" size={20} color={Colors.light.tint} />
            <Text style={styles.addButtonText}>Add Category</Text>
          </TouchableOpacity>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 10,
    color: '#333',
  },
  categoriesContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 5,
  },
  categoryChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f0f0f0',
    borderRadius: 20,
    paddingVertical: 8,
    paddingHorizontal: 12,
    marginRight: 8,
  },
  categoryText: {
    fontSize: 14,
    marginRight: 4,
  },
  removeButton: {
    padding: 2,
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 8,
  },
  addButtonText: {
    color: Colors.light.tint,
    marginLeft: 4,
    fontSize: 14,
    fontWeight: '500',
  },
  addCategoryContainer: {
    backgroundColor: '#f0f0f0',
    borderRadius: 20,
    paddingHorizontal: 12,
    height: 36,
    justifyContent: 'center',
  },
  addCategoryInput: {
    fontSize: 14,
    minWidth: 100,
  },
}); 
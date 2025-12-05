/**
 * Home Screen
 * Select Surah/Ayah and start recording
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

// Sample Surah data (in production, load from database)
const SURAHS = [
  { number: 1, name: 'Al-Fatiha', arabicName: 'الفاتحة', ayahs: 7 },
  { number: 112, name: 'Al-Ikhlas', arabicName: 'الإخلاص', ayahs: 4 },
  { number: 113, name: 'Al-Falaq', arabicName: 'الفلق', ayahs: 5 },
  { number: 114, name: 'An-Nas', arabicName: 'الناس', ayahs: 6 },
];

interface HomeScreenProps {
  navigation: any;
}

const HomeScreen: React.FC<HomeScreenProps> = ({ navigation }) => {
  const [selectedSurah, setSelectedSurah] = useState<number | null>(null);
  const [selectedAyah, setSelectedAyah] = useState<number | null>(null);

  const handleSurahSelect = (surahNumber: number) => {
    setSelectedSurah(surahNumber);
    setSelectedAyah(null);
  };

  const handleStartRecording = () => {
    navigation.navigate('Record', {
      surah: selectedSurah,
      ayah: selectedAyah,
    });
  };

  const selectedSurahData = SURAHS.find(s => s.number === selectedSurah);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Qari App</Text>
        <Text style={styles.headerSubtitle}>Quran Recitation Analysis</Text>
      </View>

      <ScrollView style={styles.content}>
        {/* Surah Selection */}
        <Text style={styles.sectionTitle}>Select Surah</Text>
        <View style={styles.surahGrid}>
          {SURAHS.map(surah => (
            <TouchableOpacity
              key={surah.number}
              style={[
                styles.surahCard,
                selectedSurah === surah.number && styles.surahCardSelected,
              ]}
              onPress={() => handleSurahSelect(surah.number)}
            >
              <Text style={styles.surahNumber}>{surah.number}</Text>
              <Text style={styles.surahArabic}>{surah.arabicName}</Text>
              <Text style={styles.surahName}>{surah.name}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Ayah Selection */}
        {selectedSurahData && (
          <View style={styles.ayahSection}>
            <Text style={styles.sectionTitle}>Select Ayah (Optional)</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              <View style={styles.ayahRow}>
                <TouchableOpacity
                  style={[
                    styles.ayahChip,
                    selectedAyah === null && styles.ayahChipSelected,
                  ]}
                  onPress={() => setSelectedAyah(null)}
                >
                  <Text style={styles.ayahChipText}>All</Text>
                </TouchableOpacity>
                {Array.from({ length: selectedSurahData.ayahs }, (_, i) => i + 1).map(
                  ayahNum => (
                    <TouchableOpacity
                      key={ayahNum}
                      style={[
                        styles.ayahChip,
                        selectedAyah === ayahNum && styles.ayahChipSelected,
                      ]}
                      onPress={() => setSelectedAyah(ayahNum)}
                    >
                      <Text style={styles.ayahChipText}>{ayahNum}</Text>
                    </TouchableOpacity>
                  ),
                )}
              </View>
            </ScrollView>
          </View>
        )}

        {/* Quick Tips */}
        <View style={styles.tipsContainer}>
          <Text style={styles.tipsTitle}>Tips for best results:</Text>
          <View style={styles.tipItem}>
            <Icon name="microphone" size={20} color="#2E7D32" />
            <Text style={styles.tipText}>Record in a quiet environment</Text>
          </View>
          <View style={styles.tipItem}>
            <Icon name="volume-high" size={20} color="#2E7D32" />
            <Text style={styles.tipText}>Speak clearly at normal pace</Text>
          </View>
          <View style={styles.tipItem}>
            <Icon name="clock-outline" size={20} color="#2E7D32" />
            <Text style={styles.tipText}>Keep recordings under 2 minutes</Text>
          </View>
        </View>
      </ScrollView>

      {/* Start Recording Button */}
      <View style={styles.footer}>
        <TouchableOpacity
          style={[
            styles.startButton,
            !selectedSurah && styles.startButtonDisabled,
          ]}
          onPress={handleStartRecording}
          disabled={!selectedSurah}
        >
          <Icon name="microphone" size={24} color="#fff" />
          <Text style={styles.startButtonText}>
            {selectedSurah ? 'Start Recording' : 'Select a Surah'}
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#2E7D32',
    padding: 20,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#C8E6C9',
    marginTop: 4,
  },
  content: {
    flex: 1,
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
    marginTop: 8,
  },
  surahGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  surahCard: {
    width: '48%',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  surahCardSelected: {
    backgroundColor: '#E8F5E9',
    borderWidth: 2,
    borderColor: '#2E7D32',
  },
  surahNumber: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  surahArabic: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2E7D32',
    marginBottom: 4,
  },
  surahName: {
    fontSize: 12,
    color: '#666',
  },
  ayahSection: {
    marginTop: 8,
  },
  ayahRow: {
    flexDirection: 'row',
    paddingVertical: 8,
  },
  ayahChip: {
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  ayahChipSelected: {
    backgroundColor: '#2E7D32',
    borderColor: '#2E7D32',
  },
  ayahChipText: {
    fontSize: 14,
    color: '#333',
  },
  tipsContainer: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginTop: 16,
  },
  tipsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  tipItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  tipText: {
    marginLeft: 12,
    fontSize: 14,
    color: '#666',
  },
  footer: {
    padding: 16,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#eee',
  },
  startButton: {
    backgroundColor: '#2E7D32',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
  },
  startButtonDisabled: {
    backgroundColor: '#ccc',
  },
  startButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
    marginLeft: 8,
  },
});

export default HomeScreen;

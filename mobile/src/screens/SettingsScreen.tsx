/**
 * Settings Screen
 * App settings and user preferences
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
  SafeAreaView,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

interface SettingsScreenProps {
  navigation: any;
}

const SettingsScreen: React.FC<SettingsScreenProps> = () => {
  const [notifications, setNotifications] = useState(true);
  const [autoPlay, setAutoPlay] = useState(true);
  const [highQuality, setHighQuality] = useState(false);

  const SettingItem = ({ 
    icon, 
    title, 
    subtitle, 
    value, 
    onToggle,
    showArrow = false,
    onPress,
  }: {
    icon: string;
    title: string;
    subtitle?: string;
    value?: boolean;
    onToggle?: (value: boolean) => void;
    showArrow?: boolean;
    onPress?: () => void;
  }) => (
    <TouchableOpacity 
      style={styles.settingItem}
      onPress={onPress}
      disabled={!onPress && !showArrow}
    >
      <View style={styles.settingIcon}>
        <Icon name={icon} size={24} color="#2E7D32" />
      </View>
      <View style={styles.settingContent}>
        <Text style={styles.settingTitle}>{title}</Text>
        {subtitle && <Text style={styles.settingSubtitle}>{subtitle}</Text>}
      </View>
      {onToggle && (
        <Switch
          value={value}
          onValueChange={onToggle}
          trackColor={{ false: '#E0E0E0', true: '#A5D6A7' }}
          thumbColor={value ? '#2E7D32' : '#f4f3f4'}
        />
      )}
      {showArrow && (
        <Icon name="chevron-right" size={24} color="#999" />
      )}
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Settings</Text>
      </View>

      <ScrollView style={styles.content}>
        {/* Recording Settings */}
        <Text style={styles.sectionTitle}>Recording</Text>
        <View style={styles.section}>
          <SettingItem
            icon="microphone-settings"
            title="High Quality Recording"
            subtitle="Uses more storage but better accuracy"
            value={highQuality}
            onToggle={setHighQuality}
          />
          <SettingItem
            icon="play-circle"
            title="Auto-play Corrections"
            subtitle="Automatically play correction audio"
            value={autoPlay}
            onToggle={setAutoPlay}
          />
        </View>

        {/* Notifications */}
        <Text style={styles.sectionTitle}>Notifications</Text>
        <View style={styles.section}>
          <SettingItem
            icon="bell"
            title="Daily Reminders"
            subtitle="Get reminded to practice daily"
            value={notifications}
            onToggle={setNotifications}
          />
        </View>

        {/* Account */}
        <Text style={styles.sectionTitle}>Account</Text>
        <View style={styles.section}>
          <SettingItem
            icon="account"
            title="Profile"
            showArrow
            onPress={() => {}}
          />
          <SettingItem
            icon="cloud-sync"
            title="Sync Data"
            subtitle="Last synced: Today at 2:30 PM"
            showArrow
            onPress={() => {}}
          />
          <SettingItem
            icon="delete"
            title="Clear Local Data"
            subtitle="Delete all recordings from device"
            showArrow
            onPress={() => {}}
          />
        </View>

        {/* About */}
        <Text style={styles.sectionTitle}>About</Text>
        <View style={styles.section}>
          <SettingItem
            icon="information"
            title="About Qari App"
            showArrow
            onPress={() => {}}
          />
          <SettingItem
            icon="file-document"
            title="Privacy Policy"
            showArrow
            onPress={() => {}}
          />
          <SettingItem
            icon="help-circle"
            title="Help & Support"
            showArrow
            onPress={() => {}}
          />
        </View>

        {/* Version */}
        <View style={styles.versionContainer}>
          <Text style={styles.versionText}>Version 1.0.0</Text>
        </View>
      </ScrollView>
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
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    marginBottom: 8,
    marginTop: 16,
    marginLeft: 4,
    textTransform: 'uppercase',
  },
  section: {
    backgroundColor: '#fff',
    borderRadius: 12,
    overflow: 'hidden',
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  settingIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#E8F5E9',
    justifyContent: 'center',
    alignItems: 'center',
  },
  settingContent: {
    flex: 1,
    marginLeft: 12,
  },
  settingTitle: {
    fontSize: 16,
    color: '#333',
  },
  settingSubtitle: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  versionContainer: {
    alignItems: 'center',
    padding: 32,
  },
  versionText: {
    fontSize: 14,
    color: '#999',
  },
});

export default SettingsScreen;

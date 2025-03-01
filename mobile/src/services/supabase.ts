import 'react-native-url-polyfill/auto';
import { createClient } from '@supabase/supabase-js';
import AsyncStorage from '@react-native-async-storage/async-storage';

const supabaseUrl = 'https://ugxvnkdqjrripmjvblsm.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVneHZua2RxanJyaXBtanZibHNtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDA1NzI0OTQsImV4cCI6MjA1NjE0ODQ5NH0.mllJ_didAVO_ghQo1e8lEIiDf7P-TLJc-_y_7RyGNRM';

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    storage: AsyncStorage,
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false,
  },
}); 
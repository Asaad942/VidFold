import { NativeModules } from 'react-native';

interface ShareModuleInterface {
  getSharedText(): Promise<string | null>;
}

const { ShareModule } = NativeModules;

export default ShareModule as ShareModuleInterface; 
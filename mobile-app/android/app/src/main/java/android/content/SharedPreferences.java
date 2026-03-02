package android.content;

/**
 * Mock SharedPreferences class for non-Android compilation
 */
public class SharedPreferences {

    public interface Editor {
        Editor putString(String key, String value);
        Editor putLong(String key, long value);
        Editor remove(String key);
        void apply();
    }

    public String getString(String key, String defValue) {
        return defValue;
    }

    public long getLong(String key, long defValue) {
        return defValue;
    }

    public Editor edit() {
        return new Editor() {
            @Override
            public Editor putString(String key, String value) {
                return this;
            }

            @Override
            public Editor putLong(String key, long value) {
                return this;
            }

            @Override
            public Editor remove(String key) {
                return this;
            }

            @Override
            public void apply() {
                // Mock implementation
            }
        };
    }
}
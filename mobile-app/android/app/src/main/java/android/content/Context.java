package android.content;

/**
 * Mock Context class for non-Android compilation
 */
public class Context {
    public static final int MODE_PRIVATE = 0;

    public String getPackageName() {
        return "com.soulsense";
    }

    public Object getPackageManager() {
        return new Object();
    }

    public SharedPreferences getSharedPreferences(String name, int mode) {
        return new SharedPreferences();
    }

    public Context getApplicationContext() {
        return this;
    }
}
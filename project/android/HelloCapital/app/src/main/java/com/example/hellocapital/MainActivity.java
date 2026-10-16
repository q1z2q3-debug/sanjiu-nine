package com.example.hellocapital;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        TextView tv = new TextView(this);
        tv.setText("Hello from Capital-Agent Gradle build");
        tv.setTextSize(24f);
        setContentView(tv);
    }
}

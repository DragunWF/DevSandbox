package com.example.fragmenttest;

import android.os.Bundle;
import android.widget.FrameLayout;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.fragment.app.Fragment;
import androidx.fragment.app.FragmentTransaction;

import com.google.android.material.tabs.TabLayout;

public class MainActivity extends AppCompatActivity {
    private FrameLayout frameLayout;
    private TabLayout tabLayout;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_main);
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
            Insets systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom);
            return insets;
        });

        frameLayout = findViewById(R.id.frameLayout);
        tabLayout = findViewById(R.id.tabLayout);

        // Indicates the first fragment that is loaded on startup
        getSupportFragmentManager().beginTransaction().replace(R.id.frameLayout, new FirstFragment())
                .setTransition(FragmentTransaction.TRANSIT_FRAGMENT_OPEN)
                .addToBackStack(null)
                .commit();

        tabLayout.setOnTabSelectedListener(new TabLayout.OnTabSelectedListener() {
            @Override
            public void onTabSelected(TabLayout.Tab tab) {
                Fragment fragment = null;

                int transitionAnimation = FragmentTransaction.TRANSIT_NONE; // default

                switch (tab.getPosition()) {
                    case 0:
                        fragment = new FirstFragment();
                        transitionAnimation = FragmentTransaction.TRANSIT_FRAGMENT_OPEN;
                        break;
                    case 1:
                        fragment = new SecondFragment();
                        transitionAnimation = FragmentTransaction.TRANSIT_FRAGMENT_FADE;
                        break;
                    case 2:
                        fragment = new ThirdFragment();
                        transitionAnimation = FragmentTransaction.TRANSIT_FRAGMENT_CLOSE;
                        break;
                }

                // setTransition() - determines the animation
                // commit() - changes the fragment
                getSupportFragmentManager().beginTransaction().replace(R.id.frameLayout, fragment)
                        .setTransition(transitionAnimation).commit();
            }

            @Override
            public void onTabUnselected(TabLayout.Tab tab) {

            }

            @Override
            public void onTabReselected(TabLayout.Tab tab) {

            }
        });
    }
}
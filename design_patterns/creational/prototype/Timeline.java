package com.codewithmosh.prototype;

import java.util.ArrayList;
import java.util.List;

public class Timeline {
    private List<Component> components = new ArrayList<>();

    public void add(Component component) {
        components.add(component);
    }
}

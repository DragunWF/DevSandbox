package com.codewithmosh.prototype;

public class ContextMenu {
    private Timeline timeline;

    public ContextMenu(Timeline timeline) {
        this.timeline = timeline;
    }

    public void duplicate(Component component) {
        this.timeline.add(component.clone());
    }
}

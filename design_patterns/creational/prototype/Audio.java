package com.codewithmosh.prototype;

public class Audio implements Component {
    @Override
    public Audio clone() {
        return new Audio();
    }
}

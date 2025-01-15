package com.codewithmosh.prototype;

public class Clip implements Component {
    @Override
    public Clip clone() {
        return new Clip();
    }
}

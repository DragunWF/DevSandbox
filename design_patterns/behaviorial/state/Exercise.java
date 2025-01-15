/*
    Exercise to the State Pattern section of Mosh 
    Hamedani's Design Patterns Course
*/

public class Exercise {
    public static void main(String[] args) {
        DirectionService service = new DirectionService();
        TravelMode[] modes = {
                new DrivingMode(), new BicyclingMode(),
                new TransitMode(), new WalkingMode()
        };
        for (TravelMode mode : modes) {
            service.setTravelMode(mode);
            service.getEta();
            service.getDirection();
        }
        /*
         * Expected Output:
         * Calculating ETA (driving)
         * Calculating Direction (driving)
         * Calculating ETA (bicycling)
         * Calculating Direction (bicycling)
         * Calculating ETA (transit)
         * Calculating Direction (transit)
         * Calculating ETA (walking)
         * Calculating Direction (walking)
         */
    }
}

interface TravelMode {
    int getEta();

    int getDirection();
}

class DirectionService {
    private TravelMode travelMode;

    public int getEta() {
        return travelMode.getEta();
    }

    public int getDirection() {
        return travelMode.getDirection();
    }

    public TravelMode getTravelMode() {
        return travelMode;
    }

    public void setTravelMode(TravelMode travelMode) {
        this.travelMode = travelMode;
    }
}

class DrivingMode implements TravelMode {
    @Override
    public int getEta() {
        System.out.println("Calculating ETA (Driving)");
        return 1;
    }

    @Override
    public int getDirection() {
        System.out.println("Calculating Direction (Driving)");
        return 1;
    }
}

class BicyclingMode implements TravelMode {
    @Override
    public int getEta() {
        System.out.println("Calculating ETA (Bicycling)");
        return 2;
    }

    @Override
    public int getDirection() {
        System.out.println("Calculating Direction (Bicycling)");
        return 2;
    }
}

class TransitMode implements TravelMode {
    @Override
    public int getEta() {
        System.out.println("Calculating ETA (Transit)");
        return 3;
    }

    @Override
    public int getDirection() {
        System.out.println("Calculating Direction (Transit)");
        return 3;
    }
}

class WalkingMode implements TravelMode {
    @Override
    public int getEta() {
        System.out.println("Calculating ETA (Walking)");
        return 4;
    }

    @Override
    public int getDirection() {
        System.out.println("Calculating Direction (Walking)");
        return 4;
    }
}

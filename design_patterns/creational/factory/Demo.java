import java.util.Date;

public class Demo {
    public static void show() {
        var arabianScheduler = new ArabianScheduler();
        arabianScheduler.schedule(new Event());

        var gregorianScheduler = new GregorianScheduler();
        gregorianScheduler.schedule(new Event());
    }

    public static void main(String[] args) {
        show();
    }
}

interface Calendar {
    public void addEvent(Event event, Date date);
}

class ArabianCalendar implements Calendar {
    @Override
    public void addEvent(Event event, Date date) {
        System.out.println("Adding an event to the Arabian calendar on a given date.");
    }
}

class GregorianCalendar implements Calendar {
    @Override
    public void addEvent(Event event, Date date) {
        System.out.println("Adding an event to the Gregorian calendar on a given date.");
    }
}

interface Scheduler {
    public void schedule(Event event);

    public Calendar createCalendar();
}

class ArabianScheduler implements Scheduler {
    private ArabianCalendar calendar = new ArabianCalendar();

    @Override
    public void schedule(Event event) {
        calendar.addEvent(event, new Date()); // today
    }

    @Override
    public ArabianCalendar createCalendar() {
        return new ArabianCalendar();
    }
}

class GregorianScheduler implements Scheduler {
    private GregorianCalendar calendar = new GregorianCalendar();

    @Override
    public void schedule(Event event) {
        calendar.addEvent(event, new Date()); // today
    }

    @Override
    public GregorianCalendar createCalendar() {
        return new GregorianCalendar();
    }
}

class Event {
}

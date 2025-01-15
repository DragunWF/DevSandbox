import java.util.ArrayList;
import java.util.List;

public class Exercise {
    public static void main(String[] args) {
        WavFile wavFile = WavFile.read("dragun.wav");
        wavFile.applyOperations(new AddReverbOperation());
        wavFile.applyOperations(new ReduceNoiseOperation());
        wavFile.applyOperations(new NormalizeOperation());
    }
}

interface Operation {
    void apply(FormatSegment segment);

    void apply(FactSegment segment);
}

class ReduceNoiseOperation implements Operation {
    @Override
    public void apply(FormatSegment segment) {
        System.out.println("Reducing noise to format segment");
    }

    @Override
    public void apply(FactSegment segment) {
        System.out.println("Reducing noise to fact segment");
    }
}

class AddReverbOperation implements Operation {
    @Override
    public void apply(FormatSegment segment) {
        System.out.println("Adding reverb to format segment");
    }

    @Override
    public void apply(FactSegment segment) {
        System.out.println("Adding reverb to fact segment");
    }
}

class NormalizeOperation implements Operation {
    @Override
    public void apply(FormatSegment segment) {
        System.out.println("Normalizing format segment");
    }

    @Override
    public void apply(FactSegment segment) {
        System.out.println("Normalizing fact segment");
    }
}

abstract class Segment {
    abstract public void execute(Operation operation);
}

class WavFile {
    private List<Segment> segments = new ArrayList<>();

    public static WavFile read(String fileName) {
        // Simulate reading a wav file and building the segments
        var wavFile = new WavFile();
        wavFile.segments.add(new FormatSegment());
        wavFile.segments.add(new FactSegment());
        wavFile.segments.add(new FactSegment());
        wavFile.segments.add(new FactSegment());

        return wavFile;
    }

    public void applyOperations(Operation operation) {
        for (var segment : segments) {
            segment.execute(operation);
        }
    }
}

class FormatSegment extends Segment {
    public void execute(Operation operation) {
        operation.apply(this);
    }
}

class FactSegment extends Segment {
    public void execute(Operation operation) {
        operation.apply(this);
    }
}
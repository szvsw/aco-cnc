# Plotter / CNC / Laser Cutter Path Optimization

Laser cutters, pen plotters, and other CNC tools are subject to a version of the Traveling Salesman Problem: the plotter must find an optimal sequencing for each curve that it must draw/cut, etc.

This library is a collection of tools (in progress!) to optimize the action sequencing.

For now, the each path should be represented as a LineSegment, corresponding to the start and end points of the path (even if it is curved).

Different strategies for optimizing the path sequencing are implemented in the library, including:

- `Ant Colony System`
- `Simulated Annealing (WIP)`
- `Greedy`

`Greedy` is by far the fastest to compute, while the others seem to achieve 5-10% over `Greedy`, at least in initial testing.


## Usage

Documentation coming soon.
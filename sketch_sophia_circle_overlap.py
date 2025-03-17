import vsketch
from shapely.geometry import (
    Point,
    LineString,
    GeometryCollection,
    MultiPolygon,
    Polygon,
)
import shapely as shapely
import shapely.ops as ops
import numpy as np


class Region:
    def __init__(self, geom: Polygon, primary):
        self.geom = geom
        self.layer = None
        self.primary = primary
        self.neighbors = []

    def touches(self, other):
        return self.geom.touches(other.geom)

    def set_layer(self, n):
        self.layer = n

    def __str__(self):
        return f"{self.layer}"


class SophiaCircleOverlapSketch(vsketch.SketchClass):
    # Sketch parameters:
    debug = vsketch.Param(False)
    simple = vsketch.Param(False)
    fixed_stroke = vsketch.Param(True)
    max_attempts = vsketch.Param(20)

    width = vsketch.Param(6.0, decimals=2, unit="in")
    height = vsketch.Param(4.0, decimals=2, unit="in")
    margin = vsketch.Param(0.1, decimals=3, unit="in")
    num_layers = vsketch.Param(2)
    noise_detail = vsketch.Param(0.007)
    min_circles = vsketch.Param(5, decimals=0, min_value=2)
    max_circles = vsketch.Param(10, decimals=0, min_value=1)
    min_radius = vsketch.Param(2, decimals=0, unit="mm")
    max_radius = vsketch.Param(20, decimals=0, unit="mm")
    evenly_spaced = vsketch.Param(False)
    kind = vsketch.Param(
        "line",
        choices=[
            "line",
            "region",
            "region-noise",
            "bug-circle",
            "circle",
            "walker",
            "circle-walker",
            "trying",
            "noise-walker",
        ],
    )
    layer1_pen_width = vsketch.Param(0.3, decimals=3, min_value=1e-10, unit="mm")
    layer2_pen_width = vsketch.Param(0.7, decimals=3, min_value=1e-10, unit="mm")

    min_pen_width = vsketch.Param(0.3, decimals=3, min_value=1e-10, unit="mm")
    max_pen_width = vsketch.Param(0.7, decimals=3, min_value=1e-10, unit="mm")

    def random_point(self, vsk: vsketch.Vsketch):
        return Point(vsk.random(0, self.width), vsk.random(0, self.height))

    def random_circle(self, vsk: vsketch.Vsketch, radius):
        return Point(
            vsk.random(radius, self.width - radius),
            vsk.random(radius, self.height - radius),
        ).buffer(radius)

    def path(self, vsk: vsketch.Vsketch):
        match self.kind:
            case "bug-circle":
                return (
                    Point(self.width / 2, self.height / 2)
                    .buffer(
                        min(self.width, self.height) / 2 - self.margin - self.max_radius
                    )
                    .boundary
                )
            case "circle":
                return (
                    Point(self.width / 2, self.height / 2)
                    .buffer(vsk.random(0.25, 0.5) * min(self.width, self.height))
                    .boundary
                )

            case _:
                return LineString([(0, self.height / 2), (self.width, self.height / 2)])

    def make_circles_orig(self, vsk: vsketch.Vsketch):

        path = self.path(vsk)
        if self.debug:
            vsk.geometry(path)
        num_circles = int(vsk.random(self.min_circles, self.max_circles))

        radii = [
            vsk.random(self.min_radius, self.max_radius) for i in range(num_circles)
        ]
        actual_max_radius = max(radii)
        y = vsk.random(radii[0], self.height - radii[0])
        x = radii[0]
        theta = 0
        outer_r = vsk.random(0.25, 0.5) * min(self.width, self.height)
        circles = []
        for i, radius in enumerate(radii):
            # todo maybe force to be a whole number of millimeters
            interp = (
                path.length * (i + 1) / (num_circles + 1)
                if self.evenly_spaced
                else vsk.random(radius, path.length - radius)
            )

            match self.kind:

                case "region":
                    shape = self.random_circle(vsk, radius)

                case "region-noise":
                    x = vsk.random(self.max_radius, self.width - self.max_radius)
                    y = vsk.random(self.max_radius, self.height - self.max_radius)
                    r = (
                        vsk.noise(x * self.noise_detail, y * self.noise_detail)
                        * (self.max_radius - self.min_radius)
                        + self.min_radius
                    )
                    shape = Point(x, y).buffer(r)
                case "line":

                    shape = path.interpolate(interp).buffer(radius)
                case "walker":
                    shape = Point(x, y).buffer(radius)
                    x += vsk.random(0.1, 1.2) * radius
                    y += vsk.random(-1, 1) * radius

                case _:
                    shape = path.interpolate(interp).buffer(radius)

            circles.append(shape)
        return circles

    def make_circles(self, vsk: vsketch.Vsketch):

        a = 1
        b = 2

        y = vsk.random(-0.5, 0.5) * self.height
        x = 0

        circles = []
        match self.kind:
            case "walker":

                while True:
                    radius = vsk.random(self.min_radius, self.max_radius)
                    if radius + x > self.width:
                        print(len(circles))
                        return circles
                    shape = Point(x, y).buffer(radius)
                    x += vsk.random(0.1, 1.2) * radius
                    y += vsk.random(-1, 1) * radius
                    circles.append(shape)

            case "noise-walker":
                while True:
                    radius = (
                        (vsk.noise(x * self.noise_detail, y * self.noise_detail))
                    ) * (self.max_radius - self.min_radius) + self.min_radius
                    if radius + x > self.width:
                        print(len(circles))
                        return circles
                    shape = Point(x, y).buffer(radius)
                    x += vsk.random(0.1, 1.2) * radius
                    y += vsk.random(-1, 1) * radius
                    circles.append(shape)

            case _:
                return self.make_circles_orig(vsk)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size(f"{self.height}x{self.width}", landscape=True, center=True)
        self.width = self.width - 2 * self.margin
        self.height = self.height - 2 * self.margin
        vsk.translate(self.margin, self.margin)

        layer_offset = 2 if self.fixed_stroke else 1
        layers = [layer_offset + i for i in range(self.num_layers)]

        circles = self.make_circles(vsk)

        geom = GeometryCollection([])
        print(len(circles))
        for circle in circles:
            geom = geom.symmetric_difference(circle)

        for index, layer in enumerate(layers):
            # what randomness would be better for favoring higher variation?
            penWidth = (
                self.layer1_pen_width
                if index == 0
                else (
                    self.layer2_pen_width
                    if index == 1
                    else vsk.random(self.min_pen_width, self.max_pen_width)
                )
            )
            vsk.penWidth(penWidth, layer)

        if self.simple or self.num_layers < 2:
            for shape in geom.geoms:
                layer = layers[int(vsk.random(0, 1) * len(layers))]
                vsk.stroke(layer)
                vsk.fill(layer)
                vsk.geometry(shape)

        else:

            universe = ops.unary_union(circles)
            other_regions = universe.symmetric_difference(geom)

            fill = 3
            regions = [Region(region, True) for region in geom.geoms]
            if not other_regions.is_empty:
                if other_regions.geom_type in ["Point", "Line", "Polygon"]:
                    regions.append(Region(other_regions, False))
                else:
                    regions = regions + [
                        Region(region, False) for region in other_regions.geoms
                    ]

            for i in range(len(regions)):
                current = regions[i]
                for j in range(i + 1, len(regions)):
                    other = regions[j]
                    if current.primary is not other.primary and current.touches(other):
                        regions[j].neighbors.append(i)
                        regions[i].neighbors.append(j)

            to_check = [i for i in range(len(regions))]
            attempts_left = self.max_attempts
            while len(to_check) > 0 and attempts_left >= 0:
                current_index = to_check.pop()
                current = regions[current_index]
                if current.layer is not None:
                    continue

                neighbor_layers = {
                    regions[neighbor].layer
                    for neighbor in current.neighbors
                    if regions[neighbor].layer is not None
                }
                possible_layers = [
                    layer for layer in layers if layer not in neighbor_layers
                ]
                if len(possible_layers) > 0:
                    # todo weight layers
                    current.layer = possible_layers[
                        int(vsk.random(0, 1) * len(possible_layers))
                    ]
                else:
                    print(f"no good choices: {current}")
                    random_layer = layers[int(vsk.random(0, 1) * len(layers))]
                    current.layer = random_layer
                    for neighbor in current.neighbors:
                        if regions[neighbor].layer == random_layer:
                            regions[neighbor].layer = None

                    attempts_left -= 1

                to_check.extend(
                    [
                        neighbor
                        for neighbor in current.neighbors
                        if regions[neighbor].layer is None
                    ]
                )

            vsk.stroke(1)
            for region in regions:
                if region.layer is not None:
                    vsk.fill(region.layer)
                    if not self.fixed_stroke:
                        vsk.stroke(region.layer)
                else:
                    vsk.stroke(1)
                    vsk.noFill()
                vsk.geometry(region.geom)

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    SophiaCircleOverlapSketch.display()

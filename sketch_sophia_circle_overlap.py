import vsketch
from shapely.geometry import Point, LineString, GeometryCollection
import shapely as shapely


class SophiaCircleOverlapSketch(vsketch.SketchClass):
    # Sketch parameters:
    debug = vsketch.Param(False)
    width = vsketch.Param(5., decimals=2, unit="in")
    height = vsketch.Param(3., decimals=2, unit="in")
    margin = vsketch.Param(0.1, decimals=3, unit="in")
    pen_width = vsketch.Param(0.7, decimals=3, min_value=1e-10, unit="mm")
    num_layers = vsketch.Param(1)
    min_circles = vsketch.Param(5, decimals=0, min_value=1)
    max_circles = vsketch.Param(10, decimals=0, min_value=1)
    min_radius = vsketch.Param(2, decimals=0, unit="mm")
    max_radius = vsketch.Param(20, decimals=0, unit="mm")

    def random_point(self, vsk: vsketch.Vsketch):
        return Point(vsk.random(0, self.width), vsk.random(0, self.height))

    def path(self):
        return LineString([(0, self.height / 2),
                           (self.width, self.height / 2)])

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size(f"{self.height}x{self.width}", landscape=True, center=False)
        self.width = self.width - 2 * self.margin
        self.height = self.height - 2 * self.margin
        vsk.translate(self.margin, self.margin)
        vsk.penWidth(f"{self.pen_width}")

        path = self.path()
        if self.debug:
            vsk.geometry(path)

        circles = []
        # layers = [1 + i for i in range(self.num_layers)]
        num_circles = int(vsk.random(self.min_circles, self.max_circles))
        for i in range(num_circles):
            # todo maybe force to be a whole number of millimeters
            radius = vsk.random(self.min_radius, self.max_radius)

            position = path.interpolate(vsk.random(1), normalized=True)
            shape = position.buffer(radius)
            circles.append(shape)

        geom = GeometryCollection([])
        for circle in circles:
            geom = geom.symmetric_difference(circle)

        # vsk.noFill()
        vsk.fill(2)
        vsk.geometry(geom)

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    SophiaCircleOverlapSketch.display()

import vsketch
from shapely.geometry import Point, LineString, GeometryCollection, MultiPolygon, Polygon
import shapely as shapely
import shapely.ops as ops 

class Region:
    def __init__(self, geom:Polygon):
        self.geom = geom
        self.layer = None

    def touches(self, other):
        return self.geom.touches(other.geom)

    def set_layer(self, n):
        self.layer = n

    def draw(self, vsk: vsketch.Vsketch):
        if self.layer is not None:
            vsk.stroke(self.layer)
            vsk.fill(self.layer)
        else:
            vsk.stroke(42)
            vsk.fill(42)
        vsk.geometry(self.geom)

    def __str__(self):
        return f"{self.layer}"

class SophiaCircleOverlapSketch(vsketch.SketchClass):
    # Sketch parameters:
    debug = vsketch.Param(False)
    simple = vsketch.Param(False)
    width = vsketch.Param(5., decimals=2, unit="in")
    height = vsketch.Param(3., decimals=2, unit="in")
    margin = vsketch.Param(0.1, decimals=3, unit="in")
    pen_width = vsketch.Param(0.7, decimals=3, min_value=1e-10, unit="mm")
    num_layers = vsketch.Param(1)
    min_circles = vsketch.Param(5, decimals=0, min_value=1)
    max_circles = vsketch.Param(10, decimals=0, min_value=1)
    min_radius = vsketch.Param(2, decimals=0, unit="mm")
    max_radius = vsketch.Param(20, decimals=0, unit="mm")
    kind = vsketch.Param("line", choices=["line", "region"])
    def random_point(self, vsk: vsketch.Vsketch):
        return Point(vsk.random(0, self.width), vsk.random(0, self.height))

    def random_circle(self, vsk: vsketch.Vsketch, radius):
        return Point(vsk.random(radius, self.width-radius), vsk.random(radius, self.height-radius)).buffer(radius)

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
        layers = [1 + i for i in range(self.num_layers)]
        num_circles = int(vsk.random(self.min_circles, self.max_circles))
        for i in range(num_circles):
            # todo maybe force to be a whole number of millimeters
            radius = vsk.random(self.min_radius, self.max_radius)


            match self.kind:
                    case "line":
                        shape = path.interpolate(vsk.random(radius,path.length-radius)).buffer(radius)
                    case "region":
                        shape = self.random_circle(vsk, radius)
                    case _:

                        shape = self.random_circle(vsk, radius)
            circles.append(shape)

        geom = GeometryCollection([])
        for circle in circles:
            geom = geom.symmetric_difference(circle)

        if self.simple:
            for shape in geom.geoms:
                layer = layers[int(vsk.random(0, 1) * len(layers))]
                vsk.stroke(layer)
                vsk.fill(layer)
                vsk.geometry(shape)

        else:

            universe = ops.unary_union(circles)
            other_regions = universe.symmetric_difference(geom)
            fill = 3
            shape = geom.geoms[0]
            vsk.stroke(42)
            vsk.fill(42)
            vsk.geometry(shape)
            for region in geom.geoms:
                if shape.touches(region):
                    vsk.stroke(1)
                    vsk.fill(1)
                else:
                    vsk.stroke(fill)
                    vsk.noFill()
                fill += 1
                vsk.geometry(region)


            for region in other_regions.geoms:
                if shape.touches(region):
                    vsk.stroke(2)
                    vsk.fill(2)
                else:
                    vsk.noFill()
                    vsk.stroke(fill)
                fill += 1
                vsk.geometry(region)

        
    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    SophiaCircleOverlapSketch.display()

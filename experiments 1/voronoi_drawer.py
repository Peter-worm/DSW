import matplotlib.pyplot as plt
from scipy.spatial import Voronoi, voronoi_plot_2d
import numpy as np
from pyproj import Transformer
import contextily as ctx
import random
from matplotlib import cm
from matplotlib import pylab
import matplotlib.patches as mpatches

def voronoi_finite_polygons_2d(vor, radius=None):
    """
    Reconstruct finite Voronoi polygons from Voronoi diagram in 2D.
    
    Parameters
    ----------
    vor : Voronoi
        Input diagram from scipy.spatial.Voronoi
    radius : float, optional
        Distance to 'points at infinity'.
    
    Returns
    -------
    regions : list of ndarray of int
        Indices of vertices in each revised Voronoi region.
    vertices : ndarray of float
        Coordinates for revised Voronoi vertices.
    """
    if vor.points.shape[1] != 2:
        raise ValueError("Requires 2D input")
    
    new_regions = []
    new_vertices = vor.vertices.tolist()
    
    center = vor.points.mean(axis=0)
    if radius is None:
        radius = vor.points.ptp().max()*2

    # Construct a map of all ridges for a point
    all_ridges = {}
    for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
        all_ridges.setdefault(p1, []).append((p2, v1, v2))
        all_ridges.setdefault(p2, []).append((p1, v1, v2))

    # Reconstruct each Voronoi region
    for p1, region_idx in enumerate(vor.point_region):
        region = vor.regions[region_idx]
        if -1 not in region:
            # Finite region
            new_regions.append(region)
            continue

        # Reconstruct a non-finite region
        ridges = all_ridges[p1]
        new_region = [v for v in region if v != -1]

        for p2, v1, v2 in ridges:
            if v2 == -1:
                v1, v2 = v2, v1
            if v1 != -1 and v2 != -1:
                continue  # already finite

            # Compute the missing endpoint
            tangent = vor.points[p2] - vor.points[p1]
            tangent /= np.linalg.norm(tangent)
            normal = np.array([-tangent[1], tangent[0]])

            midpoint = vor.points[[p1, p2]].mean(axis=0)
            direction = np.sign(np.dot(midpoint - center, normal)) * normal
            far_point = vor.vertices[v2] + direction * radius

            new_vertices.append(far_point.tolist())
            new_region.append(len(new_vertices) - 1)

        # Sort region counterclockwise
        vs = np.array([new_vertices[v] for v in new_region])
        c = vs.mean(axis=0)
        angles = np.arctan2(vs[:,1] - c[1], vs[:,0] - c[0])
        new_region = [new_region[i] for i in np.argsort(angles)]

        new_regions.append(new_region)

    return new_regions, np.array(new_vertices)

def draw_voronoi_heatmap_on_warsaw_on_subplot(points, points_to_colors, ax, name = "Voronoi Heatmap",save = True,save_path="plots/",station_legend=None,zoom =1,alpha = 0.4):
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)
    coords_deg = np.array(points)
    lngs = coords_deg[:, 1]
    lats = coords_deg[:, 0]

    xs, ys = transformer.transform(lngs, lats)
    coords_m = np.column_stack([xs, ys])

    coords_m_to_deg = {tuple(m): tuple(d) for m, d in zip(coords_m, coords_deg)}

    # Create Voronoi diagram in meters
    vor = Voronoi(coords_m)
    new_regions, new_vertices = voronoi_finite_polygons_2d(vor,radius=100000)


    print(f"Is there problem with mapping: {all(sorted(a) == sorted(b) for a, b in zip(new_vertices, vor.vertices))}")

    # Set the CRS for plotting (EPSG:2180)
    ax.set_aspect('equal')
    x_center = (xs.max() + xs.min()) / 2
    y_center = (ys.max() + ys.min()) / 2
    x_range = (xs.max() - xs.min()) / zoom / 2
    y_range = (ys.max() - ys.min()) / zoom / 2
    ax.set_xlim(x_center - x_range, x_center + x_range)
    ax.set_ylim(y_center - y_range, y_center + y_range)

    # Add basemap (Warsaw area, EPSG:2180)
    ctx.add_basemap(ax, crs="EPSG:2180", source=ctx.providers.OpenStreetMap.Mapnik)

    # Fill Voronoi regions with colors
    for region, point_idx in zip(new_regions, range(len(xs))):
        location = coords_m_to_deg[tuple(coords_m[point_idx])]
        polygon = [new_vertices[i] for i in region]
        # if location_to_station[location] in ('testtest'):
        #     color = 'black'
        # else:
        color = points_to_colors[location]  # Or use your color logic
        ax.fill(*zip(*polygon), color=color, alpha=alpha)

    voronoi_plot_2d(vor, ax=ax, show_vertices=False, line_colors='black', line_width=1, line_alpha=0.6, point_size=10)

    # Plot station points
    ax.scatter(xs, ys, c='blue', s=1, label='Stations')
    frame = pylab.gca()

    frame.axes.get_xaxis().set_ticks([])
    frame.axes.get_yaxis().set_ticks([])
    ax.set_title(name)

    if station_legend is not None:
        legend_patches = [mpatches.Patch(color=color, label=label) for label, color in station_legend]
        plt.legend(handles=legend_patches, title='Station Levels', loc='upper right')


    plt.tight_layout()
    if save:
        plt.savefig(f"{save_path}{name}.png")
    plt.show()

def draw_voronoi_heatmap_on_warsaw(points, points_to_colors, name = "Voronoi Heatmap",save = True,save_path="plots/",station_legend=None,zoom=1,alpha = 0.4):
        # Plot Voronoi diagram (no station names, just map)
    fig, ax = plt.subplots(figsize=(12, 12))
    draw_voronoi_heatmap_on_warsaw_on_subplot(points, points_to_colors, ax, name=name,station_legend=station_legend,save=save,save_path=save_path,zoom =zoom,alpha=alpha)
   
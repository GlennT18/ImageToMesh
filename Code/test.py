import open3d as o3d
import numpy as np

# Create some random points for testing
points = np.random.rand(1000, 3)  # 1000 random 3D points
pcd = o3d.geometry.PointCloud()
pcd.points = o3d.utility.Vector3dVector(points)

# Visualize the point cloud
o3d.visualization.draw_geometries([pcd])

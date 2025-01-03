#libraries
import faulthandler
import matplotlib
matplotlib.use('TkAgg')
from matplotlib import pyplot as plt
from PIL import Image
import torch
from transformers import GLPNImageProcessor, GLPNForDepthEstimation
import numpy as np
import open3d as o3d

faulthandler.enable()

#getting the model(feature extractor)
feature_extractor = GLPNImageProcessor.from_pretrained("vinvino02/glpn-nyu")
model = GLPNForDepthEstimation.from_pretrained("vinvino02/glpn-nyu")

#loading and resizing image
image = Image.open("../Images/birdExample2.jpg")
new_height = 480 if image.height > 480 else image.height
new_height -= (new_height % 32)
new_width = int(new_height * image.width / image.height)
diff = new_width % 32

new_width = new_width - diff if diff < 16 else new_width + 32 - diff
new_size = (new_width, new_height)
image = image.resize(new_size)

#preparing the image for the model
inputs = feature_extractor(images=image, return_tensors="pt")

#getting the prediction from the model
with torch.no_grad():
    outputs = model(**inputs)
    predicted_depth = outputs.predicted_depth

#post processing
pad = 16
output = predicted_depth.squeeze().cpu().numpy() * 1000.0
output = output[pad:-pad, pad:-pad]
image = image.crop((pad, pad, image.width - pad, image.height - pad))

#visualize the prediction
fig, ax = plt.subplots(1, 2)
ax[0].imshow(image)
ax[0].tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
ax[1].imshow(output, cmap='plasma')
ax[1].tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
plt.tight_layout()
#change to make image last longer
plt.pause(1)

#using numpy and open3d here
#preparing image for open3d
width, height = image.size
depth_image = (output * 255 / np.max(output)).astype('uint8')
image = np.array(image)

#this portion of code breaks*******************************************************************************************************************
# #create rgbd image
# depth_o3d = o3d.geometry.Image(depth_image)
# image_o3d = o3d.geometry.Image(image)
# rgbd_image = o3d.geometry.RGBDImage.create_from_color_and_depth(image_o3d, depth_o3d, convert_rgb_to_intensity=False)

# #create a camera
# camera_intrinsic = o3d.camera.PinholeCameraIntrinsic()
# camera_intrinsic.set_intrinsics(width, height, 500, 500, width/2, height/2)

# pcd = o3d.geometry.PointCloud.create_from_rgbd_image(rgbd_image, camera_intrinsic)
# o3d.visualization.draw_geometries([pcd])
#***********************************************************************************************************************************************

#this portion of code works*********************************************************************************************************************
# Create a point cloud manually from depth values
depth_o3d = o3d.geometry.Image(depth_image.astype(np.float32))
pcd = o3d.geometry.PointCloud()

# Convert depth to 3D points
depth_array = np.asarray(depth_o3d)
height, width = depth_array.shape
intrinsic = np.array([
    [1000, 0, width / 2],
    [0, 1000, height / 2],
    [0, 0, 1]
])

# Generate 3D points from depth map
points = []
for v in range(height):
    for u in range(width):
        Z = depth_array[v, u]
        X = (u - intrinsic[0, 2]) * Z / intrinsic[0, 0]
        Y = (v - intrinsic[1, 2]) * Z / intrinsic[1, 1]
        points.append([X, Y, Z])

pcd.points = o3d.utility.Vector3dVector(np.array(points))
#o3d.visualization.draw_geometries([pcd])
#************************************************************************************************************************************************

#Post processing 3D point cloud
cl, index = pcd.remove_statistical_outlier(nb_neighbors=20, std_ratio=20.0)
pcd = pcd.select_by_index(index)
pcd.estimate_normals()

#o3d.visualization.draw_geometries([pcd])

#surface reconstructions
mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=10, n_threads=1)[0]
#mesh.paint_uniform_color(np.array([[0.5],[0.5],[0.5]]))
o3d.visualization.draw_geometries([mesh], mesh_show_back_face=False)

#exporting mesh
o3d.io.write_triangle_mesh('../Results/bird.obj', mesh)
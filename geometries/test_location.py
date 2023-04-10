x = 5
y = 10
cell_x=20
cell_y=30
rotation=90
mirrored=True
frame_location = PointLocationCalculator(cell_x=cell_x,cell_y=cell_y,rotation=rotation)
x_frame, y_frame = frame_location.calculate_location(x, y)
print("FRAME_LOC=({},{})".format(x_frame, y_frame))

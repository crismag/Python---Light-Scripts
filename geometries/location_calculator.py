import math

class PointLocationCalculator:
    def __init__(self, cell_x, cell_y, rotation, mirrored):
        self.cell_x = cell_x
        self.cell_y = cell_y
        self.rotation = rotation
        self.mirrored = mirrored
        
        # Calculate the angle of rotation in radians
        self.theta = math.radians(rotation)

        # Calculate the sine and cosine of the angle of rotation
        self.cos_theta = math.cos(self.theta)
        self.sin_theta = math.sin(self.theta)
    
    def calculate_location(self, x, y):
        # Translate the point to the origin of the cell
        x -= self.cell_x
        y -= self.cell_y

        # Apply the rotation and mirror transformations
        if self.mirrored:
            x = -x
        x_rotated = x * self.cos_theta - y * self.sin_theta
        y_rotated = x * self.sin_theta + y * self.cos_theta

        # Translate the point back to the frame
        x_frame = self.cell_x + x_rotated
        y_frame = self.cell_y + y_rotated

        return x_frame, y_frame

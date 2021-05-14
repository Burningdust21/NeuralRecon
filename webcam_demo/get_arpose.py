import requests
import numpy as np


class PoseHandler:
    def __init__(self, host):
        self.host = host
        self.poses = np.zeros((0, 14))
        self.count = -1
        self.session = requests.Session()

    def get_item(self):
        self.count += 1
        # return intrinsic, extrinsic, width of original image, height of original image,
        return self.poses[self.count][:5], self.poses[self.count][4:12], \
               self.poses[self.count][12], self.poses[self.count][13]

    def top_time(self):
        if not self.not_empty():
            self.pose_update()
        return self.poses[self.count + 1][0]

    def not_empty(self):
        return self.count < np.shape(self.poses)[0] - 1

    def make_empty(self):
        self.count = np.shape(self.poses)[0] - 1

    def pose_update(self):
        # receive only when current data has used up
        if self.not_empty():
            return
        while True:
            r = self.session.get(self.host)
            if r.status_code == requests.codes.ok:
                lines = r.text.split('\r\n')
                lines.pop(-1)

                poses = []
                for line in lines:
                    try:
                        pose = np.array(line.split(',')).astype("float64").reshape(1, -1)
                    except:
                        continue
                    poses.append(pose)

                if len(poses) > 0:
                    self.poses = np.vstack(poses)
                    self.count = -1
                    break
            else:
                print("Error loading ARpose???")
                return

import numpy as np
import queue
from .pre_processing import quad2camera, quad2pose
from PIL import Image
import os
from webcam_demo.reconstruction import ModelEval
import matplotlib.pyplot as plt


class DataQueue:
    def __init__(self, max_queuesize, min_angle, min_distance):
        self.min_angle = min_angle
        self.min_distance = min_distance
        self.max_queuesize = max_queuesize

        # Set up images queue
        self.queue_img = queue.Queue(max_queuesize)

        # Set up pose queue
        self.queue_pose = queue.Queue(max_queuesize)

        # Set up instincts queue
        self.queu_intrin = queue.Queue(max_queuesize)

        self.fragment_id = 0
        self.curr_size = 0
        self.last_pose = np.zeros((4, 4))

    def push_queue(self, img, intrin_list, exintrin_list, fragment_id, origin_width, origin_height):
        """ push synchronized data to queue """

        # convert intrinsic and extrinsic to matrix form
        intrin = quad2camera(intrin_list, np.shape(img)[1], np.shape(img)[0], origin_width, origin_height)
        exintrin = quad2pose(exintrin_list)

        # RGB to BGR
        img = img[:, :, ::-1]
        img = Image.fromarray(img.astype('uint8')).convert('RGB')

        angle = np.arccos(
            ((np.linalg.inv(exintrin[:3, :3]) @ self.last_pose[:3, :3] @ np.array([0, 0, 1]).T) * np.array(
                [0, 0, 1])).sum())

        dis = np.linalg.norm(exintrin[:3, 3] - self.last_pose[:3, 3])
        # key frame selection
        if self.curr_size == 0 or (angle > (self.min_angle / 180) * np.pi or dis > self.min_distance):  # keyframe
            # update
            self.last_pose = exintrin
            self.curr_size += 1

            # push to data queue
            self.queue_img.put(img)
            self.queue_pose.put(exintrin)
            self.queu_intrin.put(intrin)
            self.fragment_id = fragment_id
            return True

        return False

    def get_window(self, winsize=9):
        # assemble a windows
        if winsize > self.curr_size:
            return -1
        print("[INFO]Start Reconstruction!")
        poses = []
        intrinsics = []
        imgs = []

        # pop data from queue
        for i in range(winsize):
            self.curr_size -= 1
            poses.append(self.queue_pose.get())
            self.queue_pose.task_done()

            intrinsics.append(self.queu_intrin.get())
            self.queu_intrin.task_done()

            imgs.append(self.queue_img.get())
            self.queue_img.task_done()

        # uncomment to save inputs
        self.save_input(imgs, poses, intrinsics)

        window = {
            "imgs": imgs,
            'extrinsics': poses,
            'intrinsics': intrinsics,
            'scene': "ARkit",
            'fragment_id': self.fragment_id,
        }
        self.fragment_id += 1
        return window

    # you can save inputs through this function
    def save_input(self, images, poses, intrins):
        dir = "./inputs/" + str(self.fragment_id)
        if not os.path.isdir(dir):
            os.makedirs(dir)

        for ind, (img, pose, intrin) in enumerate(zip(images, poses, intrins)):
            plt.imsave(os.path.join(dir, str(ind) + ".jpg"), np.array(img))
            np.savetxt(os.path.join(dir, str(ind) + "_pose.txt"), pose)
            np.savetxt(os.path.join(dir, str(ind) + "_intrin.txt"), intrin)


class DataController:

    def __init__(self, cfg):
        self.max_queuesize = 1000

        self.model = ModelEval(cfg)

        self.fragment_id = 0

        # key frame selection
        self.min_angle = 15
        self.min_distance = 0.1
        self.max_queuesize = 1000
        self.windowSize = 9

        self.data_queue = DataQueue(self.max_queuesize, self.min_angle, self.min_distance)

        pass

    def push_data(self, img, intrin_list, exintrin_list, origin_w, origin_h):
        # push to data queue
        pushed = self.data_queue.push_queue(img, intrin_list, exintrin_list, self.fragment_id, origin_w, origin_h)

        # reconstruct if current queue has enough frames
        window = self.data_queue.get_window()
        if window != -1:
            self.model.reconstruct(window)
            print("[INFO] Reconstruct")
        if pushed:
            print("[INFO] PUSHED")
            self.fragment_id += 1



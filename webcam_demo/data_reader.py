from webcam_demo.get_arpose import PoseHandler
from webcam_demo.data_contoller import DataController
import librtmp
import cv2
import time


class DataReader:
    def __init__(self, rtmpURL, poseURL, cfg):
        """handles incoming data"""
        self.rtmpURL = rtmpURL
        self.poseURL = poseURL

        self.PoseGetter = PoseHandler(self.poseURL)

        # for rtmp receiving
        self.rtmpURL = rtmpURL
        self.VideoStamp = None

        self.conn = None
        self.cap = None
        self.stream = None
        self.connected = False

        self.num = 0
        self.times = [0]

        # for actual FPS evaluation
        self.time_start = time.time()
        self.time_end = -1

        self.control = DataController(cfg)

    def start_receive(self):
        self.connected = False
        # linker initiation
        self.conn = librtmp.RTMP(self.rtmpURL, live=True)
        # establish link to rtmp server
        while not self.connected:
            self.conn.connect()
            _ = self.conn.create_stream()
            self.cap = cv2.VideoCapture(self.rtmpURL)
            self.connected = self.conn.connected  # and ret

        # receive until packet of type 9, which is video
        first_packet = self.conn.read_packet()
        while first_packet.type != 9:
            first_packet = self.conn.read_packet()

        # set video timestamp
        self.VideoStamp = first_packet.timestamp

        # if is the beginning of a stream, read first frame from server for synchronization
        if first_packet.timestamp == 0:
            self.cap.read()

        print("strat from: ", first_packet.timestamp)
        # start receiving!!!
        while 1:

            # log fps
            if self.num != 0 and self.num % 60 == 0:
                self.time_end = time.time()
                print("Process FPS {}, pose timestamp {}, video timestap {}".format(
                    60.0 / (self.time_end - self.time_start), self.PoseGetter.top_time(), self.VideoStamp))
                self.times = [self.times[-1]]
                self.time_start = time.time()

            # read pose and video
            self.PoseGetter.pose_update()
            ret, frame = self.cap.read()
            self.VideoStamp += 1

            if not ret:
                print("[ERROR] connection lost!!")

            # synchronization and push data to queue

            # if pose time stamp is larger, drop all received poses
            if self.PoseGetter.top_time() - self.VideoStamp <= -1:
                self.PoseGetter.make_empty()
                print("[WARN] Data Not Syn!!")
                continue

            # find synchronized data, push to queue
            if self.PoseGetter.top_time() == self.VideoStamp:
                intrin, extrin, origin_width, origin_height = self.PoseGetter.get_item()
                self.control.push_data(frame, intrin, extrin, origin_width, origin_height)
            else:
                print("[WARN] Data Not Syn!!")

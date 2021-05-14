# webcam

A tool for real time reconstruction! 

This tutorial helps to setup a real time reconstruction system, which needs nothing but an iphone/ipad to capture image, and an server to visulize you reconsrunction result.

### Setup Your IOS

Install [NeuralRecon]( https://github.com/Burningdust21/webcam_ios.git) to you Apple Device.

### Setup Your server

1. Set up an RTMP server, run the following command

   ```bash
   docker run -it -p 1935:1935 -p 8080:80 --rm alfg/nginx-rtmp
   ```

   Make sure you have docker installed in your system!

2. Install `requirement.txt`

### System Configration

Your server and IOS can function normally seperatly. This section helps you to connect them together.

1. Network

   - Find the IP adddress of server and IOS, make sure server can successfully ping ipad, and vice versa.

   - A network of 1m/s capacity would be enough

2. Open preference tab on IOS

   - Fill in RTMP server URL and stream ID(first two rows)

   - Adjust `bitrate` and `scale factor `. By now you should be able to push stream to RTMP server. Due to constrains on H264 encoding in IOS, quality of video should not be too high, or encoding would fail and no video can be sent. 

     - bitrate should be not too large, we found that 5000 is sufficient.
     - scale factor should not be too small, the actual transmitting frame size of (640, 480) would be enough. 

     **The default value provided is proven to be good enough**, but you can adjust them yourself, for better or for worse.

3. Server

   - Config IP addresses in `/config/webcam.yaml`

     ```yaml
     RTMP_SERVER: "rtmp://127.0.0.1:1935/stream/stream_id" # your rtmp server URL
     POSE_SERVER: 'http://192.168.50.211:9000/pose' # your logger URL, which is `ipad_IP:9000/pose`
     ```

   - Note that value of `RTMP_SERVER` here should be the same as that in IOS: `RTMP server URL` + `stream ID`.

### System check

1. Turn on app on your IOS, access the address of "POSE_SERVER" from server to make sure server can access IOS

2. Hit play button, watch sending FPS in the left corner, which should be around 30. If its 0, double check your configurations in previous step.

### Have Fun

1. To start reconstruction, run the following in server

   ```bash
   webcam.py --cfg webcam.yaml
   ```

2. Hit play button on IOS.

3. Recontructions started, you can see the real time visual result on the server. Besides, resulting meshes are saved under folder `real_time`.

### Trouble Shoooting

1. If one of IOS or Server is not responding, please check your network status.
2. On encounter any wierd problem, restart may be the solution!
# pre-processing for incoming data
import numpy as np
from transforms3d.quaternions import quat2mat
from tools.kp_reproject import rotx

def quad2pose(line_data):
    line_data = line_data if isinstance(line_data, list) else line_data.tolist()
    line_data = line_data[:4] + line_data[5:] + [line_data[4]]
    line_data = np.array(line_data, dtype=float)
    trans = line_data[1:4]
    quat = line_data[4:]
    rot_mat = quat2mat(np.append(quat[-1], quat[:3]).tolist())

    rot_mat = rot_mat.dot(np.array([
        [1, 0, 0],
        [0, -1, 0],
        [0, 0, -1]
    ]))
    rot_mat = rotx(np.pi / 2) @ rot_mat
    trans = rotx(np.pi / 2) @ trans
    trans_mat = np.zeros([3, 4])
    trans_mat[:3, :3] = rot_mat
    trans_mat[:3, 3] = trans

    trans_mat = np.vstack((trans_mat, [0, 0, 0, 1]))
    trans_mat[2, 3] = trans_mat[2, 3] + 1.5
    return trans_mat


def quad2camera(line_data_list, W, H, origin_width, origin_height):
    if len(line_data_list) == 0:
        print("[PANIC] Received invalid pose line!")

    # resolution normalized
    camMat = np.array([
        [line_data_list[1], 0, line_data_list[3]],
        [0, line_data_list[2], line_data_list[4]],
        [0, 0, 1]
    ], dtype=float)

    # scale intrinsics
    camMat[0, :] /= (origin_width / W)
    camMat[1, :] /= (origin_height / H)
    return camMat

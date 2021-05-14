from webcam_demo.data_reader import DataReader
import argparse
import sys
from config import update_config
from config import cfg


def parse_args():
    parser = argparse.ArgumentParser(description='A PyTorch Implementation of MVSNet')

    # general
    parser.add_argument('--cfg',
                        help='experiment configure file name',
                        required=True,
                        type=str)

    parser.add_argument('opts',
                        help="Modify config options using the command-line",
                        default=None,
                        nargs=argparse.REMAINDER)
    # parse arguments and check
    args = parser.parse_args()

    return args

# Setups
args = parse_args()
update_config(cfg, args)

# run !!
Reader = DataReader(cfg.RTMP_SERVER, cfg.POSE_SERVER, cfg)
Reader.start_receive()


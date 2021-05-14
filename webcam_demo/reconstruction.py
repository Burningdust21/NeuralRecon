from models import *
from utils import *
import torch.nn as nn
from datasets import transforms
import time


class ModelEval:
    def __init__(self, cfg):
        self.cfg = cfg

        self.model = None
        self.n_views = 9
        self.transforms = self.build_transform()
        self.count = 0

        # model
        self.model = NeuralRecon(cfg).cuda().eval()
        self.model = nn.DataParallel(self.model, device_ids=[0])

        # Load trained model
        self.load_model(cfg.LOGDIR)
        self.vis = o3d.visualization.VisualizerWithKeyCallback()
        self.vis.create_window()

        # directory of save mesh
        self.save_path = None
        self.setup_dir()

        pass

    def setup_dir(self):
        self.save_path = os.path.join("./real_time", time.strftime('%Y-%m-%dT%H-%M-%S', time.localtime(time.time())))
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)

    def build_transform(self):
        cfg = self.cfg

        transform = [transforms.ResizeImage((640, 480)),
                     transforms.ToTensor(),
                     transforms.RandomTransformSpace(
                         cfg.MODEL.N_VOX, cfg.MODEL.VOXEL_SIZE, random_rotation=False, random_translation=False,
                         paddingXY=0, paddingZ=0, max_epoch=cfg.TRAIN.EPOCHS),
                     transforms.IntrinsicsPoseToProjection(cfg.TEST.N_VIEWS, 4)]
        return transforms.Compose(transform)

    def load_model(self, dir):
        # load trained model
        saved_models = [fn for fn in os.listdir(dir) if fn.endswith(".ckpt")]
        saved_models = sorted(saved_models, key=lambda x: int(x.split('_')[-1].split('.')[0]))

        # use the latest checkpoint file
        ckpt = saved_models[-1]
        loadckpt = os.path.join(self.cfg.LOGDIR, ckpt)

        state_dict = torch.load(loadckpt)
        self.model.load_state_dict(state_dict['model'], strict=False)

    def reconstruct(self, window):
        # numpy to tensor
        sample = self.make_sample(window)

        # evaluate
        with torch.no_grad():
            outputs, loss_dict = self.model(sample)

        # visualize model
        self.visualization(outputs)

    def make_sample(self, window):
        intrinsics_list = window['intrinsics']
        extrinsics_list = window['extrinsics']
        intrinsics = np.stack(intrinsics_list)
        extrinsics = np.stack(extrinsics_list)

        items = {
            'imgs': window["imgs"],  # 1, 9, 3, 486, 640
            'intrinsics': intrinsics,  # 1,9,3,3
            'extrinsics': extrinsics,  # 1,9,4,4
            'scene': [window['scene']],
            'fragment': [window['scene'] + '_' + str(window['fragment_id'])],
            'vol_origin': np.array([0, 0, 0]),
            'epoch': [self.count],
        }
        if self.transforms is not None:
            items = self.transforms(items)

        # some element needs to expand dimension
        items['imgs'] = items['imgs'].unsqueeze(0)
        items['vol_origin'] = items['vol_origin'].unsqueeze(0)
        items['vol_origin_partial'] = items['vol_origin_partial'].unsqueeze(0)
        items['world_to_aligned_camera'] = items['world_to_aligned_camera'].unsqueeze(0)
        items['proj_matrices'] = items['proj_matrices'].unsqueeze(0)

        return items

    def visualization(self, outputs):
        if not ("scene_tsdf" in outputs):
            return -1
        else:
            print("Senen succeed!!")

        tsdf_volume = outputs['scene_tsdf'][0].data.cpu().numpy()
        origin = outputs['origin'][0].data.cpu().numpy()
        origin[2] -= 1.5

        # sdf to Marching cubes t mesh
        mesh = self.sdf2mesh(self.cfg.MODEL.VOXEL_SIZE, origin, tsdf_volume)
        if self.count % self.cfg.SAVE_FREQ == 0:
            mesh.export(os.path.join(self.save_path, "{:04d}.ply".format(self.count)))
        mesh = mesh.as_open3d
        mesh = mesh.compute_vertex_normals()
        self.count += 1

        # vis mesh
        self.vis.clear_geometries()
        self.vis.add_geometry(mesh)
        self.vis.poll_events()
        self.vis.update_renderer()
        return mesh

    @staticmethod
    def sdf2mesh(voxel_size, origin, sdf_vol):
        verts, faces, norms, vals = measure.marching_cubes_lewiner(sdf_vol, level=0)
        verts = verts * voxel_size + origin  # voxel grid coordinates to world coordinates
        mesh = trimesh.Trimesh(vertices=verts, faces=faces, vertex_normals=norms)
        return mesh

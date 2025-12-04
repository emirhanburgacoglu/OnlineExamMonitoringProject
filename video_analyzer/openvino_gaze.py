from dataclasses import dataclass
from typing import Optional, Tuple
import cv2
import numpy as np
from openvino.runtime import Core

@dataclass
class GazeResult:
    yaw: float
    pitch: float
    roll: float
    gaze_vec: Tuple[float, float, float]   # x,y,z (model çıktısı)
    gaze_xy: Tuple[float, float]           # roll düzeltilmiş ekranda x,y
    bbox: Tuple[int, int, int, int]        # x1,y1,x2,y2
    conf: float

class OpenVinoGaze:
    """
    OMZ zinciri:
      - face-detection-adas-0001 (IR)
      - head-pose-estimation-adas-0001 (IR)
      - gaze-estimation-adas-0002 (IR)
    Gerekli dosyalar (FP32):
      models/intel/face-detection-adas-0001/FP32/*.xml/.bin
      models/intel/head-pose-estimation-adas-0001/FP32/*.xml/.bin
      models/intel/gaze-estimation-adas-0002/FP32/*.xml/.bin
    """
    def __init__(self, models_dir: str = "models"):
        core = Core()
        # Yollar
        fd = f"{models_dir}/intel/face-detection-adas-0001/FP32/face-detection-adas-0001.xml"
        hp = f"{models_dir}/intel/head-pose-estimation-adas-0001/FP32/head-pose-estimation-adas-0001.xml"
        gz = f"{models_dir}/intel/gaze-estimation-adas-0002/FP32/gaze-estimation-adas-0002.xml"

        # Model & Compile
        self.fd_compiled = core.compile_model(core.read_model(fd), "CPU")
        self.hp_compiled = core.compile_model(core.read_model(hp), "CPU")
        self.gz_compiled = core.compile_model(core.read_model(gz), "CPU")

        # FD I/O
        self.fd_input = self.fd_compiled.inputs[0]    # [1,3,H,W]
        self.fd_out = self.fd_compiled.outputs[0]     # [1,1,N,7]
        self.fd_h, self.fd_w = self.fd_input.shape[2], self.fd_input.shape[3]

        # HP I/O
        self.hp_input = self.hp_compiled.inputs[0]    # [1,3,60,60]
        self.hp_out_y = self.hp_compiled.outputs[0]   # angle_y_fc
        self.hp_out_p = self.hp_compiled.outputs[1]   # angle_p_fc
        self.hp_out_r = self.hp_compiled.outputs[2]   # angle_r_fc
        self.hp_h, self.hp_w = self.hp_input.shape[2], self.hp_input.shape[3]

        # GZ I/O
        # giriş isimleri: "left_eye_image", "right_eye_image", "head_pose_angles"
        self.gz_in_left  = self.gz_compiled.inputs[0]
        self.gz_in_right = self.gz_compiled.inputs[1]
        self.gz_in_head  = self.gz_compiled.inputs[2]
        self.gz_out_vec  = self.gz_compiled.outputs[0]  # [1,3]
        self.gz_h, self.gz_w = self.gz_in_left.shape[2], self.gz_in_left.shape[3]

    def _preprocess_fd(self, bgr: np.ndarray) -> np.ndarray:
        img = cv2.resize(bgr, (self.fd_w, self.fd_h))
        img = img.transpose(2, 0, 1)[None, ...]  # NCHW
        return img

    def _preprocess_face(self, bgr: np.ndarray, bbox) -> np.ndarray:
        x1, y1, x2, y2 = bbox
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(bgr.shape[1]-1, x2), min(bgr.shape[0]-1, y2)
        face = bgr[y1:y2, x1:x2]
        if face.size == 0:
            face = bgr
        face = cv2.resize(face, (self.hp_w, self.hp_h))
        face = face.transpose(2, 0, 1)[None, ...]      # NCHW
        return face

    def _parse_fd(self, detections: np.ndarray, W: int, H: int, conf_thr: float = 0.6):
        dets = detections.reshape(-1, 7)
        candidates = []
        for _, _, conf, xmin, ymin, xmax, ymax in dets:
            if conf < conf_thr: continue
            x1, y1 = int(xmin*W), int(ymin*H)
            x2, y2 = int(xmax*W), int(ymax*H)
            candidates.append((x1, y1, x2, y2, float(conf)))
        if not candidates:
            return None
        candidates.sort(key=lambda b: (b[2]-b[0])*(b[3]-b[1]), reverse=True)
        return candidates[0]

    def _eye_crops(self, bgr: np.ndarray, face_bbox):
        # Heüristik göz kırpmaları: yüz kutusuna göre konum
        x1, y1, x2, y2 = face_bbox
        w = x2 - x1
        h = y2 - y1
        # sol göz merkezi ~ yüzün sol-üst çeyreği
        lc = (int(x1 + 0.33*w), int(y1 + 0.42*h))
        rc = (int(x1 + 0.67*w), int(y1 + 0.42*h))
        box = int(0.26 * min(w, h))   # kutu boyutu

        def crop(cx, cy):
            half = box // 2
            x_a, y_a = cx - half, cy - half
            x_b, y_b = cx + half, cy + half
            x_a, y_a = max(0, x_a), max(0, y_a)
            x_b, y_b = min(bgr.shape[1]-1, x_b), min(bgr.shape[0]-1, y_b)
            roi = bgr[y_a:y_b, x_a:x_b]
            if roi.size == 0:
                roi = bgr[max(0,y1):y2, max(0,x1):x2]
            roi = cv2.resize(roi, (self.gz_w, self.gz_h))
            return roi.transpose(2, 0, 1)[None, ...]  # NCHW

        left  = crop(*lc)
        right = crop(*rc)
        return left, right

    def infer(self, bgr: np.ndarray) -> Optional[GazeResult]:
        H, W = bgr.shape[:2]
        # 1) Face detect
        fd_in = self._preprocess_fd(bgr)
        fd_res = self.fd_compiled([fd_in])[self.fd_out]
        det = self._parse_fd(fd_res, W, H, 0.6)
        if det is None:
            return None
        x1, y1, x2, y2, conf = det

        # 2) Head pose (face crop)
        face_in = self._preprocess_face(bgr, (x1, y1, x2, y2))
        hp_res = self.hp_compiled([face_in])
        yaw   = float(hp_res[self.hp_out_y][0][0])
        pitch = float(hp_res[self.hp_out_p][0][0])
        roll  = float(hp_res[self.hp_out_r][0][0])

        # 3) Eye crops
        left_eye, right_eye = self._eye_crops(bgr, (x1, y1, x2, y2))

        # 4) Gaze estimation
        head_angles = np.array([[yaw, pitch, roll]], dtype=np.float32)
        gz_res = self.gz_compiled([
            left_eye.astype(np.float32),
            right_eye.astype(np.float32),
            head_angles
        ])
        gaze_vec = gz_res[self.gz_out_vec][0]  # [3] (x,y,z)

        # 5) Roll düzeltmesi: ekranda x,y bileşenleri
        r = np.deg2rad(roll)
        cx, sx = np.cos(r), np.sin(r)
        gx = gaze_vec[0]*cx + gaze_vec[1]*sx
        gy = -gaze_vec[0]*sx + gaze_vec[1]*cx

        return GazeResult(
            yaw=yaw, pitch=pitch, roll=roll,
            gaze_vec=(float(gaze_vec[0]), float(gaze_vec[1]), float(gaze_vec[2])),
            gaze_xy=(float(gx), float(gy)),
            bbox=(x1, y1, x2, y2), conf=conf)
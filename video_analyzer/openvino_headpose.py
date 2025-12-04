# C:\Projelerim\OnlineExamMonitoringProject\video_analyzer\openvino_headpose.py
from dataclasses import dataclass
from typing import Optional, Tuple
import cv2
import numpy as np
from openvino.runtime import Core

@dataclass
class HeadPoseResult:
    yaw: float
    pitch: float
    roll: float
    bbox: Tuple[int, int, int, int]  # x1,y1,x2,y2
    conf: float

class HeadPoseEstimator:
    """
    Intel OpenVINO ADAS zinciri:
      - face-detection-adas-0001
      - head-pose-estimation-adas-0001
    Not: Bu minimal bir zincirdir (gaze yok). Doğruluk için yaw/pitch ile karar veriyoruz.
    """
    def __init__(self, models_dir: str = "models"):
        self.core = Core()

        # Model pathleri (IR)
        fd = f"{models_dir}/intel/face-detection-adas-0001/FP32/face-detection-adas-0001.xml"
        hp = f"{models_dir}/intel/head-pose-estimation-adas-0001/FP32/head-pose-estimation-adas-0001.xml"

        # Yükle/compile
        self.fd_model = self.core.read_model(fd)
        self.hp_model = self.core.read_model(hp)
        self.fd_compiled = self.core.compile_model(self.fd_model, "CPU")
        self.hp_compiled = self.core.compile_model(self.hp_model, "CPU")

        # FD I/O
        self.fd_input = self.fd_compiled.inputs[0]      # NCHW
        self.fd_out = self.fd_compiled.outputs[0]       # [1,1,N,7]
        self.fd_h, self.fd_w = self.fd_input.shape[2], self.fd_input.shape[3]

        # HP I/O
        self.hp_input = self.hp_compiled.inputs[0]      # [1,3,60,60] tipik
        self.hp_out_y = self.hp_compiled.outputs[0]     # angle_y_fc
        self.hp_out_p = self.hp_compiled.outputs[1]     # angle_p_fc
        self.hp_out_r = self.hp_compiled.outputs[2]     # angle_r_fc
        self.hp_h, self.hp_w = self.hp_input.shape[2], self.hp_input.shape[3]

    def _preprocess_fd(self, bgr: np.ndarray) -> np.ndarray:
        img = cv2.resize(bgr, (self.fd_w, self.fd_h))
        img = img.transpose(2, 0, 1)[None, ...]  # NCHW
        return img

    def _preprocess_face_for_hp(self, bgr: np.ndarray, bbox) -> np.ndarray:
        x1, y1, x2, y2 = bbox
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(bgr.shape[1] - 1, x2), min(bgr.shape[0] - 1, y2)
        face = bgr[y1:y2, x1:x2]
        if face.size == 0:
            face = bgr
        face = cv2.resize(face, (self.hp_w, self.hp_h))
        face = face.transpose(2, 0, 1)[None, ...]  # NCHW
        return face

    def _parse_fd(self, detections: np.ndarray, frame_w: int, frame_h: int, conf_thr: float = 0.6):
        # detections: [1,1,N,7] => [image_id,label,conf,xmin,ymin,xmax,ymax]
        dets = detections.reshape(-1, 7)
        boxes = []
        for _, _, conf, xmin, ymin, xmax, ymax in dets:
            if conf < conf_thr:
                continue
            x1 = int(xmin * frame_w)
            y1 = int(ymin * frame_h)
            x2 = int(xmax * frame_w)
            y2 = int(ymax * frame_h)
            boxes.append((x1, y1, x2, y2, float(conf)))
        if not boxes:
            return None
        # En büyük yüz
        boxes.sort(key=lambda b: (b[2]-b[0])*(b[3]-b[1]), reverse=True)
        b = boxes[0]
        return (b[0], b[1], b[2], b[3], b[4])

    def infer(self, bgr: np.ndarray) -> Optional[HeadPoseResult]:
        # Face detect
        fd_in = self._preprocess_fd(bgr)
        fd_res = self.fd_compiled([fd_in])[self.fd_out]  # [1,1,N,7]
        det = self._parse_fd(fd_res, bgr.shape[1], bgr.shape[0], conf_thr=0.6)
        if det is None:
            return None
        x1, y1, x2, y2, conf = det

        # Head pose on face crop
        hp_in = self._preprocess_face_for_hp(bgr, (x1, y1, x2, y2))
        hp_res = self.hp_compiled([hp_in])
        yaw = float(hp_res[self.hp_out_y][0][0])
        pitch = float(hp_res[self.hp_out_p][0][0])
        roll = float(hp_res[self.hp_out_r][0][0])

        return HeadPoseResult(yaw=yaw, pitch=pitch, roll=roll, bbox=(x1, y1, x2, y2), conf=conf)
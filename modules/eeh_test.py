# File: eeh.py
# Description: Edge Enhancement
# Created: 2021/10/22 20:50
# Author: Qiu Jueqin (qiujueqin@gmail.com)


from cv2 import imwrite
import numpy as np
import cv2

from basic_module import BasicModule, register_dependent_modules
from helpers import generic_filter, gen_gaussian_kernel


class EEHTEST():
    def __init__(self) -> None:
        self.cfg_flat_threshold = 4
        self.cfg_edge_threshold = 8
        self.cfg_edge_gain = 384
        self.cfg_delta_threshold = 64


        kernel = gen_gaussian_kernel(kernel_size=5, sigma=1.2)
        self.gaussian = (1024 * kernel / kernel.max()).astype(np.int32)  # x1024

        t1, t2 = self.cfg_flat_threshold, self.cfg_edge_threshold
        threshold_delta = np.clip(t2 - t1, 1E-6, None)
        self.middle_slope = np.array(self.cfg_edge_gain * t2 / threshold_delta, dtype=np.int32)  # x256
        self.middle_intercept = -np.array(self.cfg_edge_gain * t1 * t2 / threshold_delta, dtype=np.int32)  # x256
        self.edge_gain = np.array(self.cfg_edge_gain, dtype=np.int32)  # x256
    
    def execute(self, data):
        y_image = data.astype(np.int32)

        delta = y_image - generic_filter(y_image, self.gaussian)
        sign_map = np.sign(delta)
        abs_delta = np.abs(delta)

        middle_delta = np.right_shift(self.middle_slope * abs_delta + self.middle_intercept, 8)
        edge_delta = np.right_shift(self.edge_gain * abs_delta, 8)
        enhanced_delta = (
                (abs_delta > self.cfg_flat_threshold) * (abs_delta <= self.cfg_edge_threshold) * middle_delta +
                (abs_delta > self.cfg_edge_threshold) * edge_delta
        )

        enhanced_delta = sign_map * np.clip(enhanced_delta, 0, self.cfg_delta_threshold)
        eeh_y_image = np.clip(y_image + enhanced_delta, 0, 255)
        return eeh_y_image.astype(np.uint8)
        # print(data['y_image'].size())

if __name__ == '__main__':
    
    img = cv2.imread('../output/bnf.jpg')
    img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
    y, u, v = cv2.split(img_yuv)
    eeh_test = EEHTEST()
    new_y = eeh_test.execute(y)
    yuv_new = cv2.merge((new_y, u, v))
    img_new = cv2.cvtColor(yuv_new, cv2.COLOR_YUV2BGR)
    cv2.imwrite('./test.jpg', img_new)
    origin = cv2.imread('./test_eeh.jpg')
    print(np.sum(img_new-origin))



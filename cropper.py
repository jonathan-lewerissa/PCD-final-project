import cv2 as cv
import numpy as np
from matplotlib import pyplot as plt

import os


class Cropper:

    def __init__(self, image: np.ndarray):
        self.image = image
        self.image_visualizer = self.image.copy()

        self.imgray = None
        self.thresh = None
        self.contours = []

        self.boundaries = []
        self.cropped_images = []

    def crop(self, object_count: int) -> list:
        self.__preprocess()
        self.boundaries = self.__find_boundary(object_count)
        self.cropped_images = self.__cropper(self.boundaries)

        return self.cropped_images

    def __preprocess(self, lower_threshold: int = 200) -> None:
        # perform gray image and blurring

        if 'THRESHOLD' in os.environ:
            lower_threshold = os.environ.get('THRESHOLD')

        self.imgray = cv.cvtColor(self.image, cv.COLOR_RGB2GRAY)
        self.imgray = cv.blur(self.imgray, (5, 5))

        # perform thresholding and preparation for finding contour
        _, self.thresh = cv.threshold(self.imgray, lower_threshold, 255, cv.THRESH_BINARY_INV)
        self.thresh = cv.morphologyEx(self.thresh, cv.MORPH_OPEN, np.ones((5, 5), np.uint8))
        self.thresh = cv.morphologyEx(self.thresh, cv.MORPH_CLOSE, np.ones((5, 5), np.uint8))

        # find image contours
        self.contours, _ = cv.findContours(self.thresh, cv.RETR_LIST, cv.CHAIN_APPROX_TC89_L1)

    def __find_boundary(self, object_count: int) -> list:
        # perform n-greatest area checking for generated contours
        areas = []
        for cnt in self.contours:
            areas.append(cv.contourArea(cnt))
        areas.sort()
        min_area_size = min(areas[-object_count:])

        # perform point extraction from contour bounding rectangle 
        result = []
        for i, cnt in enumerate(self.contours):
            if cv.contourArea(cnt) < min_area_size:
                continue

            # straight bounding rectangle
            x, y, w, h = cv.boundingRect(cnt)

            # rotated rectangle
            rect = cv.minAreaRect(cnt)
            box = cv.boxPoints(rect)
            box = np.int0(box)

            result.append(((x, y, w, h), rect))

            cv.rectangle(self.image_visualizer, (x, y), (x + w, y + h), (0, 255, 0), 5)
            cv.drawContours(self.image_visualizer, [box], 0, (0, 0, 255), 5)

        return result

    def __cropper(self, boundaries: list) -> list:
        result = []

        for boundary in boundaries:
            straight_box = boundary[0]
            rotated_box = boundary[1]

            # extracting cropping points for straight bounding rectangle
            x, y, w, h = straight_box

            # finding cropping points and perform warp transformation
            width = int(rotated_box[1][0])
            height = int(rotated_box[1][1])

            box = cv.boxPoints(rotated_box)
            box = np.int0(box)

            src_pts = box.astype('float32')
            dst_pts = np.array([[width - 1, 0], [width - 1, height - 1], [0, height - 1], [0, 0]], dtype='float32')
            m = cv.getPerspectiveTransform(src_pts, dst_pts)
            warp = cv.warpPerspective(self.image, m, (width, height))

            # resulting image
            rotated_image = warp
            straight_bounding_image = self.image[y:y + h, x:x + w]

            result.append((straight_bounding_image, rotated_image))

        return result

    def visualize(self):
        titles = ['Original Image', 'Boundaires', 'Gray', 'Thresh']
        images = [self.image, self.image_visualizer, self.imgray, self.thresh]

        for i in range(len(images)):
            plt.subplot(2, 2, i + 1), plt.imshow(cv.cvtColor(images[i], cv.COLOR_BGR2RGB))
            plt.title(titles[i])
            plt.xticks([]), plt.yticks([])
        plt.show()


if __name__ == "__main__":

    image_path = './example/01.jpg'
    image_count = 4

    image = cv.imread(image_path)
    cropper = Cropper(image)
    cropped_images = cropper.crop(image_count)
    cropper.visualize()

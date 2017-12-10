﻿import numpy as np
import cv2
from scipy.stats import mode
import time
import ImageFusion
import os
import skimage.measure

class Stitcher:
    '''
	    图像拼接类，包括所有跟材料显微组织图像配准相关函数
	'''
    outputAddress = "result/"
    isEvaluate = False
    evaluateFile = "evaluate.txt"
    isPrintLog = False

    def __init__(self, outputAddress, evaluate, isPrintLog):
        self.outputAddress = outputAddress
        self.isEvaluate = evaluate[0]
        self.evaluateFile = evaluate[1]
        self.isPrintLog = isPrintLog

    def printAndWrite(self, content):
        if self.isPrintLog:
            print(content)
        if self.isEvaluate:
            f = open(self.outputAddress + self.evaluateFile, "a")
            f.write(content)
            f.write("\n")
            f.close()

    def pairwiseStitch(self, fileList, registrateMethod, fuseMethod, direction="horizontal"):
        self.printAndWrite("Stitching " + str(fileList[0]) + " and " + str(fileList[1]))

        imageA = cv2.imread(fileList[0], 0)
        imageB = cv2.imread(fileList[1], 0)
        startTime = time.time()
        (status, offset) = self.calculateOffset([imageA,imageB], registrateMethod, fuseMethod, direction=direction)
        endTime = time.time()

        if status == False:
            self.printAndWrite(offset)
            return (status, offset)
        else:
            self.printAndWrite("  The time of stitching is " + str(endTime - startTime) + "s")
            startTime = time.time()
            (stitchImage, fuseRegion, roiImageRegionA, roiImageRegionB) = self.getStitchByOffset([imageA, imageB], offset, fuseMethod=fuseMethod)
            endTime = time.time()
            self.printAndWrite("  The time of fusing is " + str(endTime - startTime) + "s")
            return (status, stitchImage)

    def gridStitch(self, fileList, filePosition, registrateMethod, fuseMethod, shootOrder="snakeByCol"):
        largeBlockNum = len(filePosition)
        # self.printAndWrite("Stitching the directory which have" + str(fileList[0]))
        # offsetList = []
        # # calculating the offset for small image
        # startTime = time.time()
        # for i in range(0, largeBlockNum):
        #     offsetList.append([])
        #     if i % 2 == 0:
        #         indexStart = filePosition[i][0]; indexEnd = filePosition[i][1]; indexCrement = 1
        #     elif i % 2 == 1:
        #         indexStart = filePosition[i][1]; indexEnd = filePosition[i][0]; indexCrement = -1
        #     for fileIndex in range(indexStart, indexEnd, indexCrement):
        #         self.printAndWrite("stitching" + str(fileList[fileIndex - 1]) + " and " + str(fileList[fileIndex + indexCrement - 1]))
        #         imageA = cv2.imread(fileList[fileIndex - 1], 0)
        #         imageB = cv2.imread(fileList[fileIndex + indexCrement - 1], 0)
        #         if shootOrder == "snakeByCol":
        #             (status, offset) = self.calculateOffset([imageA, imageB], registrateMethod, fuseMethod, direction="vertical")
        #         elif shootOrder == "snakeByRow":
        #             (status, offset) = self.calculateOffset([imageA, imageB], registrateMethod, fuseMethod, direction="horizontal")
        #         if status == False:
        #             return (False, "  " + str(fileList[fileIndex - 1]) + " and "+ str(fileList[fileIndex + indexCrement - 1]) + str(offset))
        #         else:
        #             offsetList[i].append(offset)
        #
        # # calculating the offset for big block
        # # filePosition = [[1, 15], [16, 30], [31, 45], [46, 60], [61, 75], [76, 90]]
        # self.printAndWrite("Stitching large block")
        # offsetBlockList = []
        # for i in range(0, largeBlockNum - 1):
        #     if i % 2 == 0:
        #         indexA = filePosition[i][0]; indexB = filePosition[i + 1][1];
        #     elif i % 2 == 1:
        #         indexA = filePosition[i][1]; indexB = filePosition[i + 1][0];
        #     print(" stitching " + str(fileList[indexA - 1]) + " and " + str(fileList[indexB - 1]))
        #     imageA = cv2.imread(fileList[indexA - 1], 0)
        #     imageB = cv2.imread(fileList[indexB - 1], 0)
        #     if shootOrder == "snakeByCol":
        #         (status, offset) = self.calculateOffset([imageA, imageB], registrateMethod, fuseMethod,
        #                                                    direction="horizontal")
        #     elif shootOrder == "snakeByRow":
        #         (status, offset) = self.calculateOffset([imageA, imageB], registrateMethod, fuseMethod,
        #                                                 direction="vertial")
        #     if status == False:
        #         return (False, "  Stitching the large block " + str(fileList[indexA - 1]) + " and "+ str(fileList[indexB - 1]) + str(offset))
        #     else:
        #         offsetBlockList.append(offset)
        # endTime = time.time()
        # self.printAndWrite("  The time of registing is " + str(endTime - startTime) + "s")
        # print(offsetList)
        # print(offsetBlockList)

        # stitching and fusing
        # stiching One block
        # offsetList = [[(1784, 2), (1805, 2), (1810, 2), (1775, 3), (1761, 2), (1847, 3), (1809, 1), (1813, 3), (1787, 2), (1818, 3), (1786, 2), (1803, 3), (1722, 1), (1211, 1)], [(1439, 2), (1778, 2), (1677, 3), (1822, 4), (1768, 3), (1808, 3), (1779, 1), (1785, 3), (1790, 3), (1727, 2), (1754, 2), (1788, 4), (1809, 2), (1735, 2)], [(1758, 2), (1792, 2), (1795, 3), (1841, 3), (1783, 3), (1802, 4), (1782, 2), (1763, 3), (1738, 3), (1837, 3), (1781, 3), (1789, 18), (1713, 1), (1270, -12)], [(1411, 1), (1817, 2), (1672, 2), (1696, 3), (1875, 4), (1667, 2), (1747, 2), (1754, 2), (1885, 3), (1726, 2), (1763, 2), (1823, 2), (1812, 2), (1787, 1)], [(1874, 3), (1707, -3), (1783, 3), (1795, 3), (1732, 3), (1838, 4), (1721, 1), (1783, 4), (1805, 3), (1726, 4), (1829, 2), (1775, 3), (1776, 1), (1596, 179)], [(1197, 1), (1792, 3), (1833, 2), (1659, 2), (1766, 2), (1750, 2), (1768, 2), (1848, 2), (1817, 3), (1815, 3), (1742, 4), (1758, 3), (1844, 2), (1822, 1)]]
        # offsetBlockList = [(60, 2408), (-3, 2410), (5, 2487), (-4, 2432), (-83, 2406)]
        offsetList = [[(1734, 2), (1768, 2), (1722, 0), (1772, 2), (1713, 1), (1723, 1), (1816, 2), (1835, 2), (1543, 0), (1807, 2),
          (1832, 2), (1794, 1), (1795, -1), (1514, 1)],
         [(1497, 0), (1836, 3), (1693, -1), (1798, 2), (1809, 2), (1782, 1), (1745, 2), (1760, 1), (1793, 2), (1777, 1),
          (1731, 2), (1748, 2), (1752, 1), (1746, 2)],
         [(1778, 2), (1747, 2), (1824, 1), (1823, 3), (1784, 2), (1771, 0), (1750, 2), (1753, 2), (1826, 0), (1770, 2),
          (1771, 1), (1714, 1), (1813, 1), (1351, 1)],
         [(1523, 1), (1770, 2), (1663, 0), (1748, 1), (1822, 1), (1783, 2), (1762, 2), (1812, 2), (1789, 1), (1748, 1),
          (1790, 1), (1800, 2), (1735, 1), (1774, 2)],
         [(1802, 2), (1753, 3), (1847, 1), (1757, 2), (1751, 2), (1782, 2), (1833, 1), (1792, 1), (1760, 2), (1777, 2),
          (1853, 1), (1842, 2), (1822, 1), (1044, -1)],
         [(1514, 0), (1772, 1), (1735, 0), (1793, 1), (1787, 1), (1736, 1), (1695, 1), (1827, 2), (1763, 1), (1689, 1),
          (1791, 2), (1742, 2), (1772, 1), (1777, 1)]]
        offsetBlockList = [(-103, 2449), (-4, 2423), (-48, 2418), (-4, 2379), (19, 2526)]
        startTime = time.time()
        largeBlcokImage = []
        for i in range(0, largeBlockNum):
            # print(" one block:" + str(i))
            indexNum = len(offsetList[i])
            if i % 2 == 0:
                indexStart = filePosition[i][0];indexEnd = filePosition[i][1];indexCrement = 1
            elif i % 2 == 1:
                indexStart = filePosition[i][1];indexEnd = filePosition[i][0];indexCrement = -1
            count = 0
            dxSum = 0; dySum = 0

            stitchImage = cv2.imread(fileList[indexStart - 1], 0)
            for fileIndex in range(indexStart, indexEnd, indexCrement):
                imageA = cv2.imread(fileList[fileIndex - 1], 0)
                imageB = cv2.imread(fileList[fileIndex + indexCrement - 1], 0)
                dxSum = offsetList[i][count][0] + dxSum
                dySum = offsetList[i][count][1] + dySum
                offset = [dxSum,  dySum]
                # offset = [offsetList[i][count][0], offsetList[i][count][1]]
                (stitchImage, fuseRegion, roiImageRegionA, roiImageRegionB) = self.getStitchByOffset([stitchImage, imageB], offset, fuseMethod)
                if offsetList[i][count][1] < 0:
                    dySum = dySum - offsetList[i][count][1]
                count = count + 1
            cv2.imwrite(self.outputAddress + "\\" + str(i) + ".jpg", stitchImage)
            largeBlcokImage.append(stitchImage)


        # stiching multi block Image
        totalStitch = largeBlcokImage[0]
        dxSum = 0; dySum = 0;
        for i in range(0, largeBlockNum - 1):
            # print(" big block:" + str(i))
            imageB = largeBlcokImage[i + 1]
            dxSum = offsetBlockList[i][0] + dxSum
            dySum = offsetBlockList[i][1] + dySum
            offset = [dxSum, dySum]
            (totalStitch, fuseRegion, roiImageRegionA, roiImageRegionB) = self.getStitchByOffset([totalStitch, imageB],
                                                                                                 offset, fuseMethod)
            if offsetBlockList[i][0] < 0:
                dxSum = dxSum - offsetBlockList[i][0]
        endTime = time.time()
        self.printAndWrite("  The time of fusing is " + str(endTime - startTime) + "s")
        return (True, totalStitch)

    def calculateOffset(self, images, registrateMethod, fuseMethod, direction="horizontal"):
        '''
        Stitch two images
        :param images: [imageA, imageB]
        :param registrateMethod: list:
        :param fuseMethod:
        :param direction: stitching direction
        :return:
        '''
        (imageA, imageB) = images
        offset = [0, 0]
        if  registrateMethod[0] == "phaseCorrection":
            return (False, "  We don't develop the phase Correction method, Plesae wait for updating")
        elif  registrateMethod[0] == "featureSearchWithIncrease":
            featureMethod = registrateMethod[1]        # "sift","surf" or "orb"
            searchRatio = registrateMethod[2]          # 0.75 is common value for matches
            offsetCaculate = registrateMethod[3][0]    # "mode" or "ransac"
            offsetEvaluate = registrateMethod[3][1]    # 40 menas nums of matches for mode, 4.0 menas  of matches for ransac
            roiFirstLength = registrateMethod[4][0]     # roi length for stitching in first direction
            roiSecondLength = registrateMethod[4][1]    # roi length for stitching in second direction

            if direction == "horizontal":
                maxI = int(imageA.shape[1] / (2 * roiFirstLength))
            elif direction == "vertical":
                maxI = int(imageA.shape[0] / (2 * roiFirstLength))
            for i in range(1, maxI+1):
                # get the roi region of images
                # print("  i is: " + str(i))
                roiImageA = self.getROIRegion(imageA, direction=direction, order="first", searchLength=i * roiFirstLength,
                                                  searchLengthForLarge=roiSecondLength)
                roiImageB = self.getROIRegion(imageB, direction=direction, order="second", searchLength=i * roiFirstLength,
                                                  searchLengthForLarge=roiSecondLength)
                # get the feature points
                (kpsA, featuresA) = self.detectAndDescribe(roiImageA, featureMethod=featureMethod)
                (kpsB, featuresB) = self.detectAndDescribe(roiImageB, featureMethod=featureMethod)

                # ptsA = np.float32([kpsA[i] for (_, i) in matches])
                # ptsB = np.float32([kpsB[i] for (i, _) in matches])
                # # 计算视角变换矩阵
                # (H, status) = cv2.findHomography(ptsA, ptsB, cv2.RANSAC, 4.0)
                # print("H:" + str(H.astype(np.int)))

                # match all the feature points and return the list of offset
                (dxArray, dyArray) = self.matchKeypoints(kpsA, kpsB, featuresA, featuresB, searchRatio)
                if direction == "horizontal":
                        dyArray = dyArray + imageA.shape[1] - i * roiFirstLength
                elif direction == "vertical":
                        dxArray = dxArray + imageA.shape[0] - i * roiFirstLength
                if offsetCaculate == "mode":
                    localStartTime = time.time()
                    (status, offset) = self.getOffsetByMode(dxArray, dyArray, evaluateNum=offsetEvaluate)
                    localEndTime = time.time()
                    if status == True:
                        self.printAndWrite("  The time of registering is " + str(localEndTime - localStartTime) + "s")
                elif offsetCaculate == "ransac":
                    (status, offset) = self.getOffsetByRansac(dxArray, dyArray, evaluateNum=offsetEvaluate)
                    # return (False, "  We don't develop the stitching with ransac method, Plesae wait for updating")
                if status == True:
                    break
        self.printAndWrite("  The offset of stitching: dx is "+ str(offset[0]) + " dy is " + str(offset[1]))
        return (True, offset)

    def getROIRegion(self, image, direction="horizontal", order="first", searchLength=150, searchLengthForLarge=-1):
        '''对原始图像裁剪感兴趣区域
        :param originalImage:需要裁剪的原始图像
        :param direction:拼接的方向
        :param order:该图片的顺序，是属于第一还是第二张图像
        :param searchLength:搜索区域大小
        :param searchLengthForLarge:对于行拼接和列拼接的搜索区域大小
        :return:返回感兴趣区域图像
        :type searchLength: np.int
        '''
        row, col = image.shape[:2]
        if direction == "horizontal":
            if order == "first":
                if searchLengthForLarge == -1:
                    roiRegion = image[:, col - searchLength:col]
                elif searchLengthForLarge > 0:
                    roiRegion = image[row - searchLengthForLarge:row, col - searchLength:col]
            elif order == "second":
                if searchLengthForLarge == -1:
                    roiRegion = image[:, 0: searchLength]
                elif searchLengthForLarge > 0:
                    roiRegion = image[0:searchLengthForLarge, 0: searchLength]
        elif direction == "vertical":
            if order == "first":
                if searchLengthForLarge == -1:
                    roiRegion = image[row - searchLength:row, :]
                elif searchLengthForLarge > 0:
                    roiRegion = image[row - searchLength:row, col - searchLengthForLarge:col]
            elif order == "second":
                if searchLengthForLarge == -1:
                    roiRegion = image[0: searchLength, :]
                elif searchLengthForLarge > 0:
                    roiRegion = image[0: searchLength, 0:searchLengthForLarge]
        return roiRegion

    def detectAndDescribe(self, image, featureMethod):
        '''
    	计算图像的特征点集合，并返回该点集＆描述特征
    	:param image:需要分析的图像
    	:return:返回特征点集，及对应的描述特征
    	'''
        # 将彩色图片转换成灰度图
        # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 建立SIFT生成器
        if featureMethod == "sift":
            descriptor = cv2.xfeatures2d.SIFT_create()
        elif featureMethod == "surf":
            descriptor = cv2.xfeatures2d.SURF_create()
        # 检测SIFT特征点，并计算描述子
        (kps, features) = descriptor.detectAndCompute(image, None)

        # 将结果转换成NumPy数组
        kps = np.float32([kp.pt for kp in kps])

        # 返回特征点集，及对应的描述特征
        return (kps, features)

    def matchKeypoints(self, kpsA, kpsB, featuresA, featuresB, ratio):
        '''
        匹配特征点
        :param self:
        :param featuresA: 第一张图像的特征点描述符
        :param featuresB: 第二张图像的特征点描述符
        :param ratio: 最近邻和次近邻的比例
        :return:返回匹配的对数
        '''
        # 建立暴力匹配器
        matcher = cv2.DescriptorMatcher_create("BruteForce")

        # 使用KNN检测来自A、B图的SIFT特征匹配对，K=2，返回一个列表
        rawMatches = matcher.knnMatch(featuresA, featuresB, 2)
        matches = []
        for m in rawMatches:
        # 当最近距离跟次近距离的比值小于ratio值时，保留此匹配对
            if len(m) == 2 and m[0].distance < m[1].distance * ratio:
                # 存储两个点在featuresA, featuresB中的索引值
                matches.append((m[0].trainIdx, m[0].queryIdx))
        # self.printAndWrite("  The number of matching is " + str(len(matches)))
        dxList = []; dyList = []
        # # 获取输入图片及其搜索区域
        # (imageA, imageB) = images
        # (hA, wA) = imageA.shape[:2]
        # (hB, wB) = imageB.shape[:2]
        for trainIdx, queryIdx in matches:
            # ptA = (int(kpsA[queryIdx][1]), int(kpsA[queryIdx][0]))
            # ptB = (int(kpsB[trainIdx][1]), int(kpsB[trainIdx][0]))
            ptA = (kpsA[queryIdx][1], kpsA[queryIdx][0])
            ptB = (kpsB[trainIdx][1], kpsB[trainIdx][0])
            # if direction == "horizontal":
            dxList.append(ptA[0] - ptB[0])
            dyList.append(ptA[1] - ptB[1])
            # elif direction == "vertical":
            #     dx.append((hA - ptA[0]) + ptB[0])
            #     dy.append(ptA[1] - ptB[1])
        # print(np.array((np.array(dxList),np.array(dyList))).transpose())
        return (np.array(dxList) ,np.array(dyList))

    def getOffsetByMode(self, dxArray, dyArray, evaluateNum=20):
        if len(dxArray) < evaluateNum:
            return (False, (0, 0))
        else:
            return (True, (int(mode(dxArray.astype(np.int), axis=None)[0]), int(mode(dyArray.astype(np.int), axis=None)[0])))

    def getOffsetByRansac(self, dxArray, dyArray, evaluateNum=100):


        data = np.column_stack([dxArray, dyArray])
        model = skimage.measure.CircleModel
        ransac_model, inliers = skimage.measure.ransac(data, model, 20, residual_threshold=1, max_trials=200)
        dxRansac = []; dyRansac = []
        matchNum = len(inliers)
        if matchNum < evaluateNum:
            return (False, (0, 0))
        for i in range(0 , matchNum):
            if inliers[i] == True:
                dxRansac.append(data[i][0])
                dyRansac.append(data[i][1])
        # print(np.array(dxRansac))
        # print(np.array(dyRansac))
        return (True, (int(mode(np.array(dxRansac).astype(int), axis=None)[0]), int(mode(np.array(dyRansac).astype(int), axis=None)[0])))

    # def creatOffsetImage(self, image, direction, offset):
    #     h, w = image.shape[:2]
    #     returnImage = np.zeros(image.shape,dtype=np.uint8)
    #     if direction == "horizontal":
    #         if offset >= 0:
    #             returnImage[0:h-offset,:] = image[offset: h, :]
    #         elif offset < 0:
    #             returnImage[(-1 * offset):h, :] = image[0:h+offset,:]
    #     elif direction == "vertical":
    #         if offset >= 0:
    #             returnImage[:, 0:w-offset] = image[:, offset:w]
    #         elif offset < 0:
    #             returnImage[:, (-1 * offset):w] = image[:, 0:w+offset]
    #     return returnImage

    def getStitchByOffset(self, images, offset, fuseMethod):
        (imageA, imageB) = images
        (hA, wA) = imageA.shape[:2]
        (hB, wB) = imageB.shape[:2]
        dx = offset[0]; dy = offset[1]

        if abs(dy) >= abs(dx):
            direction = "horizontal"
        elif abs(dy) < abs(dx):
            direction = "vertical"

        if dx >= 0 and dy >= 0:
            # The first image is located at the left top, the second image located at the right bottom
            stitchImage = np.zeros((max(hA, dx + hB), max(dy + wB, wA)), dtype=np.uint8)
            roi_ltx = dx; roi_lty = dy
            roi_rbx = min(dx + hB, hA); roi_rby = min(dy + wB, wA)
            stitchImage[0: hA, 0:wA] = imageA
            roiImageRegionA = stitchImage[roi_ltx: roi_rbx, roi_lty: roi_rby].copy()
            stitchImage[dx: dx+hB, dy: dy+wB] = imageB
            roiImageRegionB = stitchImage[roi_ltx: roi_rbx, roi_lty: roi_rby].copy()
        elif dx >= 0 and dy < 0:
            # The first image is located at the right top, the second image located at the left bottom
            stitchImage = np.zeros((max(hA, dx + hB), -dy + wA), dtype=np.uint8)
            roi_ltx = dx; roi_lty = -dy
            roi_rbx = hA;  roi_rby = min(-dy + wA, wB)
            stitchImage[0: hA, -dy:-dy + wA] = imageA
            roiImageRegionA = stitchImage[roi_ltx: roi_rbx, roi_lty: roi_rby].copy()
            stitchImage[dx: dx+wB, 0: wB] = imageB
            roiImageRegionB = stitchImage[roi_ltx: roi_rbx, roi_lty: roi_rby].copy()
        elif dx < 0 and dy >= 0:
            # The first image is located at the left bottom, the second image located at the right top
            stitchImage = np.zeros((-dx + hA, max(dy + wB, wA)), dtype=np.uint8)
            roi_ltx = -dx; roi_lty = dy
            roi_rbx = min(-dx + hA, hB);  roi_rby = min(dy + wB, wA)
            stitchImage[-dx: -dx + hA, 0: wA] = imageA
            roiImageRegionA = stitchImage[roi_ltx: roi_rbx, roi_lty: roi_rby].copy()
            stitchImage[0: hB, dy: dy + wB] = imageB
            roiImageRegionB = stitchImage[roi_ltx: roi_rbx, roi_lty: roi_rby].copy()
        elif dx < 0 and dy < 0:
            # The first image is located at the right bottom, the second image located at the left top
            stitchImage = np.zeros((-dx + hA, -dy + wA), dtype=np.uint8)
            roi_ltx = -dx; roi_lty = -dy
            roi_rbx = wA;  roi_rby = hA
            stitchImage[-dx: -dx + hA, -dy: -dy + wA] = imageA
            roiImageRegionA = stitchImage[roi_ltx: roi_rbx, roi_lty: roi_rby].copy()
            stitchImage[0: hB, 0: wB] = imageB
            roiImageRegionB = stitchImage[roi_ltx: roi_rbx, roi_lty: roi_rby].copy()
        fuseRegion = self.fuseImage([roiImageRegionA, roiImageRegionB], direction=direction, fuseMethod=fuseMethod)
        stitchImage[roi_ltx: roi_rbx, roi_lty: roi_rby] = fuseRegion.copy()
        return (stitchImage, fuseRegion, roiImageRegionA, roiImageRegionB)

    def fuseImage(self, images, fuseMethod, direction="horizontal"):
        (imageA, imageB) = images
        fuseRegion = np.zeros(imageA.shape, np.uint8)
        imageA[imageA == 0] = imageB[imageA == 0]
        imageB[imageB == 0] = imageA[imageB == 0]
        if fuseMethod[0] == "notFuse":
            fuseRegion = imageB
        elif fuseMethod[0] == "average":
            fuseRegion = ImageFusion.fuseByAverage(images)
        elif fuseMethod[0] == "maximum":
            fuseRegion = ImageFusion.fuseByMaximum(images)
        elif fuseMethod[0] == "minimum":
            fuseRegion = ImageFusion.fuseByMinimum(images)
        elif fuseMethod[0] == "fadeInAndFadeOut":
            fuseRegion = ImageFusion.fuseByFadeInAndFadeOut(images,direction)
        elif fuseMethod[0] == "multiBandBlending":
            fuseRegion = ImageFusion.fuseByMultiBandBlending(images)
        elif fuseMethod[0] == "trigonometric":
            fuseRegion = ImageFusion.fuseByTrigonometric(images,direction)
        elif fuseMethod[0] == "optimalSeamLine":
            fuseRegion = ImageFusion.fuseByOptimalSeamLine(images, direction)
        return fuseRegion

if __name__=="__main__":
    # fileList = [".\\images\\dendriticCrystal\\2\\2-030.jpg", ".\\images\\dendriticCrystal\\2\\2-031.jpg"]
    # outputAddress = "result"
    # evaluate = (True, "evaluate.txt")
    # isPrintLog = True
    # stitcher = Stitcher(outputAddress, evaluate, isPrintLog)
    # registrateMethod = ("featureSearchWithIncrease", "surf", 0.65, ("mode", 100), (150, -1))
    # fuseMethod = ("notFuse", "Test")
    #
    # (status, result) = stitcher.pairwiseStitch(fileList, registrateMethod, fuseMethod, direction="horizontal")
    # if status == True:
    #     cv2.imwrite(outputAddress + "\\stitching_result.jpg", result)
    # if status == False:
    #     print("拼接失败")
    outputAddress = "result"
    fileList = [".\\result\\dendriticCrystalNotFuse\\0.jpg", ".\\result\\dendriticCrystalNotFuse\\1.jpg", ".\\result\\dendriticCrystalNotFuse\\2.jpg"]
    offset = [(-103, 2449), (-4, 4872)]
    evaluate = (True, "evaluate.txt")
    isPrintLog = True
    stitcher = Stitcher(outputAddress, evaluate, isPrintLog)
    registrateMethod = ("featureSearchWithIncrease", "surf", 0.65, ("mode", 100), (150, -1))
    fuseMethod = ("trigonometric", "Test")
    imageA = cv2.imread(fileList[0], 0)
    imageB = cv2.imread(fileList[1], 0)
    imageC = cv2.imread(fileList[2], 0)
    (stitchImage, fuseRegion, roiImageRegionA, roiImageRegionB) = stitcher.getStitchByOffset([imageA, imageB], offset[0], fuseMethod)
    (stitchImage, fuseRegion, roiImageRegionA, roiImageRegionB) = stitcher.getStitchByOffset([stitchImage, imageC],
                                                                                             offset[1], fuseMethod)
    cv2.imwrite("result.jpg", stitchImage)
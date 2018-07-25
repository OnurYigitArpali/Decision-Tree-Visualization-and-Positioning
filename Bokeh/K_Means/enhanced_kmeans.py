########################################################################################################################
############# Implementation from "Faster K_Means Cluster Estimation(Siddhesh Khandelwal, Amit Awekar)" ################

from __future__ import division
import numpy
import copy
import time
import threading
import math
import random
import bisect
import pandas as pd
from bokeh.transform import factor_cmap
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource
from bokeh.layouts import layout
from random import randint

graph_list = []


class Point:
    def __init__(self, p, dim, id=-1):
        self.coordinates = []
        self.pointList = []
        self.id = id
        self.pointCentroid = 0
        for x in range(0, dim):
            self.coordinates.append(p[x]);
        self.centroid = None


class Centroid:
    count = 0

    def __init__(self, point):
        self.point = point
        self.count = Centroid.count
        self.pointList = []
        self.centerPos = []
        self.predictions = []
        self.centerPos.append(self.point)
        self.centroid = None
        Centroid.count += 1

    def update(self, point):
        self.point = point
        self.centerPos.append(self.point)

    def addPoint(self, point):
        self.pointList.append(point)

    def removePoint(self, point):
        self.pointList.remove(point)


class Kmeans:
    def __init__(self, k, pointList, kmeansThreshold, centroidsToRemember, initialCentroids=None):
        self.pointList = []
        self.numPoints = len(pointList)
        self.k = k
        self.initPointList = []
        self.centroidsToRemember = int(k * centroidsToRemember / 100)
        print("Centroids to Remember:", self.centroidsToRemember)
        self.dim = len(pointList[0])
        self.kmeansThreshold = kmeansThreshold
        self.error = None
        self.errorList = []
        self.closestClusterDistance = {}
        self.centroidDistance = {}

        i = 0
        for point in pointList:
            p = Point(point, self.dim, i)
            i += 1
            self.pointList.append(p)
            self.closestClusterDistance[p.id] = -1
            self.centroidDistance[p.id] = []

        if initialCentroids != None:
            self.centroidList = self.seeds(initialCentroids)
        else:
            self.centroidList = self.selectSeeds(self.k)
        self.mainFunction()

    def selectSeeds(self, k):
        seeds = random.sample(self.pointList, k)
        centroidList = []
        for seed in seeds:
            centroidList.append(Centroid(seed))
        return centroidList

    def seeds(self, initList):
        centroidList = []
        for seed in initList:
            centroidList.append(Centroid(seed))
        return centroidList

    def getDistance(self, point1, point2):
        distance = 0
        for x in range(0, self.dim):
            distance += (point1.coordinates[x] - point2.coordinates[x]) ** 2
        return (distance) ** (0.5)

    def getCentroidInit(self, point):
        minDist = -1
        pos = 0
        for centroid in self.centroidList:
            dist = self.getDistance(point, centroid.point)
            if len(self.centroidDistance[point.id]) < self.centroidsToRemember:
                bisect.insort(self.centroidDistance[point.id], (dist, pos))
            elif self.centroidDistance[point.id][self.centroidsToRemember - 1][0] > dist:
                bisect.insort(self.centroidDistance[point.id], (dist, pos))
                del self.centroidDistance[point.id][self.centroidsToRemember]
            if minDist == -1:
                minDist = dist
                closestCentroid = pos
            elif minDist > dist:
                minDist = dist
                closestCentroid = pos
            pos += 1
        return (closestCentroid, minDist)

    def getCentroid(self, point):
        pos = 0
        dist = self.getDistance(point, self.centroidList[point.centroid].point)
        minDist = dist
        closestCentroid = point.centroid
        currCentroid = point.centroid
        if self.closestClusterDistance[point.id] < dist:
            for x in self.initPointList[point.id]:
                centroid = self.centroidList[x]
                if x != currCentroid:
                    dist = self.getDistance(point, centroid.point)
                    if minDist > dist:
                        minDist = dist
                        closestCentroid = x
                pos += 1
        else:
            self.numChange += 1
        self.closestClusterDistance[point.id] = minDist
        return (closestCentroid, minDist)

    def reCalculateCentroid(self):
        pos = 0
        for centroid in self.centroidList:
            zeroArr = []
            for x in range(0, self.dim):
                zeroArr.append(0)
            mean = Point(zeroArr, self.dim)
            for point in centroid.pointList:
                for x in range(0, self.dim):
                    mean.coordinates[x] += point.coordinates[x]
            for x in range(0, self.dim):
                try:
                    mean.coordinates[x] = mean.coordinates[x] / len(centroid.pointList)
                except:
                    mean.coordinates[x] = 0
            centroid.update(mean)
            self.centroidList[pos] = centroid
            pos += 1

    def assignPointsInit(self):
        self.initPointList = {}
        for i in range(len(self.pointList) - 1, -1, -1):
            temp = self.getCentroidInit(self.pointList[i])
            self.initPointList[self.pointList[i].id] = []
            for l in range(0, self.centroidsToRemember):
                self.initPointList[self.pointList[i].id].append(self.centroidDistance[self.pointList[i].id][l][1])
            centroidPos = temp[0]
            centroidDist = temp[1]
            self.closestClusterDistance[self.pointList[i].id] = centroidDist
            if self.pointList[i].centroid is None:
                self.pointList[i].centroid = centroidPos
                self.centroidList[centroidPos].pointList.append(copy.deepcopy(self.pointList[i]))

    def assignPoints(self):
        doneMap = {}
        self.numChange = 0
        for i in range(len(self.centroidList) - 1, -1, -1):
            for j in range(len(self.centroidList[i].pointList) - 1, -1, -1):
                try:
                    a = doneMap[self.centroidList[i].pointList[j].id]
                except:
                    doneMap[self.centroidList[i].pointList[j].id] = 1
                    temp = self.getCentroid(self.centroidList[i].pointList[j])
                    centroidPos = temp[0]
                    centroidDist = temp[1]
                    if self.centroidList[i].pointList[j].centroid != centroidPos:
                        self.centroidList[i].pointList[j].centroid = centroidPos
                        self.centroidList[centroidPos].pointList.append(
                            copy.deepcopy(self.centroidList[i].pointList[j]))
                        del self.centroidList[i].pointList[j]
        print(self.numChange)

    def calculateError(self, config):
        error = 0
        for centroid in self.centroidList:
            for point in centroid.pointList:
                error += self.getDistance(point, centroid.point) ** 2
        return error

    def errorCount(self):
        self.t = threading.Timer(0.5, self.errorCount)
        self.t.start()
        startTime = time.time()
        timeStamp = 0
        if self.error != None:
            timeStamp = math.log(self.error)
        endTime = time.time()
        self.errorList.append(timeStamp)
        self.ti += 0.5

    def mainFunction(self):
        self.iteration = 1
        self.ti = 0.0
        self.errorCount()
        error1 = 2 * self.kmeansThreshold + 1
        error2 = 0
        iterationNo = 0
        self.currentTime = time.time()
        self.startTime = time.time()
        self.assignPointsInit()
        print("First Step:", time.time() - self.startTime)
        while (abs(error1 - error2)) > self.kmeansThreshold:
            iterationNo += 1
            self.iteration = iterationNo
            error1 = self.calculateError(self.centroidList)
            self.error = error1
            print("Iteration:", iterationNo, "Error:", error1)
            self.reCalculateCentroid()
            self.assignPoints()
            error2 = self.calculateError(self.centroidList)
            self.error = error2
            graph_list.append(create_figure(self.centroidList))
        self.t.cancel()


def makeRandomPoint(n, lower, upper):
    return numpy.random.normal(loc=upper, size=[lower, n])
def create_figure(X):
    tools = "hover,crosshair,pan,wheel_zoom,zoom_in,zoom_out,box_zoom,undo," \
            "redo,reset,tap,save,box_select,poly_select,lasso_select,"
    p = figure(tools=tools)
    p.title.text = "Seçim"


    cluster_xs = []
    cluster_ys = []

    for centroid in X:
        cluster_xs.append(centroid.centerPos[-1].coordinates[0])
        cluster_ys.append(centroid.centerPos[-1].coordinates[1])

    columns = ['x', 'y', 'cluster']
    df = pd.DataFrame(columns=columns)

    for centroid in X:
        for point in centroid.pointList:
            df = df.append({'x': point.coordinates[0], 'y': point.coordinates[1],
                            'cluster': str(centroid.point.coordinates[0] + centroid.point.coordinates[1])}, ignore_index=True)

    cmap = {str(centroid.point.coordinates[0] + centroid.point.coordinates[1]): ('#%06X' % randint(0, 0xFFFFFF)) for centroid in X}

    dataSource = ColumnDataSource(data=pd.DataFrame.from_dict(df))

    p.circle(x='x', y='y', size=5, source=dataSource,
             color=factor_cmap('cluster', palette=list(cmap.values()), factors=list(cmap.keys())))

    p.rect(cluster_xs, cluster_ys, 10, 10, width_units="screen", height_units="screen", color="black")
    return p




secim_df = pd.read_csv("Data/secim2015.csv")
print(secim_df)
pointList = [[x, y] for x, y in zip(secim_df["GECERSIZ_OY_ORAN"], secim_df["GECERLI_OY_TOPLAMI"])]

numClusters = 7
kmeans_threshold = 1

start = time.time()
config = Kmeans(numClusters, pointList, kmeans_threshold, 100)
print("Time taken:", time.time() - start)

show(layout(graph_list))

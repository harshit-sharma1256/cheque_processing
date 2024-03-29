from pylab import *
import numpy as np
from os import listdir
from sklearn.svm import LinearSVC
import cv2
from PIL import Image
from sklearn import svm
import imagehash
from scipy.cluster.vq import *
from sklearn.preprocessing import StandardScaler
from sklearn import tree
from sklearn import linear_model
import preproc
import features

genuine_image_filenames = listdir("data/genuine")
forged_image_filenames = listdir("data/forged")
#print(genuine_image_filenames)
#print(forged_image_filenames)
genuine_image_paths = "data/genuine"
forged_image_paths = "data/forged"

genuine_image_features = [[] for x in range(29)]
forged_image_features = [[] for x in range(29)]

for name in genuine_image_filenames:
    signature_id = int(name.split('_')[0][-3:])
    genuine_image_features[signature_id - 1].append({"name": name})

for name in forged_image_filenames:
    signature_id = int(name.split('_')[0][-3:])
    forged_image_features[signature_id - 1].append({"name": name})


# def preprocess_image(path, display=False):
#     raw_image = cv2.imread(path)
#     bw_image = cv2.cvtColor(raw_image, cv2.COLOR_BGR2GRAY)
#     bw_image = 255 - bw_image

#     if display:
#         cv2.imshow("RGB to Gray", bw_image)
#         cv2.waitKey()

#     # _, threshold_image = cv2.threshold(bw_image, 30, 255, 0)
#     _, threshold_image = cv2.threshold(bw_image, 127, 255,cv2.THRESH_BINARY)

#     if display:
#         cv2.imshow("Threshold", threshold_image)
#         cv2.waitKey()

#     return threshold_image

def preprocess_image(path,display=False):
    #return 0,1 image
    return preproc.preproc(path, display=display) 

des_list = []

def sift(im, path, display=False):
    raw_image = cv2.imread(path)
    sift = cv2.xfeatures2d.SIFT_create()
    kp, des = sift.detectAndCompute(im, None)

    if display:
        cv2.drawKeypoints(im, kp, raw_image)
        cv2.imshow('sift_keypoints.jpg', cv2.resize(raw_image, (0, 0), fx=3, fy=3))
        cv2.waitKey()

    return (path, des)


cor = 0
wrong = 0

im_contour_features = []

for i in range(29):
    # print(genuine_image_features[i])
    des_list = []
    for im in genuine_image_features[i]:
        image_path = genuine_image_paths + "/" + im['name']
        preprocessed_image = preprocess_image(image_path)
        hash = imagehash.phash(Image.open(image_path))

        aspect_ratio, bounding_rect_area, convex_hull_area, contours_area = \
            features.get_contour_features(preprocessed_image.copy(), display=False)

        hash = int(str(hash), 16)
        im['hash'] = hash
        im['aspect_ratio'] = aspect_ratio
        im['hull_area/bounding_area'] = convex_hull_area / bounding_rect_area
        im['contour_area/bounding_area'] = contours_area / bounding_rect_area

        im['ratio'] = features.Ratio(preprocessed_image.copy())
        im['centroid_0'],im['centroid_1']=features.Centroid(preprocessed_image.copy())
        
        im['eccentricity'],im['solidity']=features.EccentricitySolidity(preprocessed_image.copy())
        (im['skewness_0'],im['skewness_1']),(im['kurtosis_0'],im['kurtosis_1']) = features.SkewKurtosis(preprocessed_image.copy())
        
        # im_contour_features.append([hash, aspect_ratio, convex_hull_area / bounding_rect_area, contours_area / bounding_rect_area])
        im_contour_features.append([aspect_ratio, convex_hull_area / bounding_rect_area, contours_area / bounding_rect_area, im['ratio'],im['centroid_0'],im['centroid_1'],im['eccentricity'],im['solidity'],im['skewness_0'],im['skewness_1'],im['kurtosis_0'],im['kurtosis_1']])

        des_list.append(sift(preprocessed_image.copy(), image_path))
        # print(len(des_list))


    for im in forged_image_features[i]:
        image_path = forged_image_paths + "/" + im['name']
        preprocessed_image = preprocess_image(image_path)
        hash = imagehash.phash(Image.open(image_path))

        aspect_ratio, bounding_rect_area, convex_hull_area, contours_area = \
            features.get_contour_features(preprocessed_image.copy(), display=False)

        hash = int(str(hash), 16)
        im['hash'] = hash
        im['aspect_ratio'] = aspect_ratio
        im['hull_area/bounding_area'] = convex_hull_area / bounding_rect_area
        im['contour_area/bounding_area'] = contours_area / bounding_rect_area
        
        im['ratio'] = features.Ratio(preprocessed_image.copy())
        im['centroid_0'],im['centroid_1']=features.Centroid(preprocessed_image.copy())
        
        im['eccentricity'],im['solidity']=features.EccentricitySolidity(preprocessed_image.copy())
        (im['skewness_0'],im['skewness_1']),(im['kurtosis_0'],im['kurtosis_1']) = features.SkewKurtosis(preprocessed_image.copy())
        
        # im_contour_features.append([hash, aspect_ratio, convex_hull_area / bounding_rect_area, contours_area / bounding_rect_area])
        im_contour_features.append([aspect_ratio, convex_hull_area / bounding_rect_area, contours_area / bounding_rect_area,im['ratio'],im['centroid_0'],im['centroid_1'],im['eccentricity'],im['solidity'],im['skewness_0'],im['skewness_1'],im['kurtosis_0'],im['kurtosis_1']])

        des_list.append(sift(preprocessed_image.copy(), image_path))

    descriptors = des_list[0][1]
#    print(shape(im_contour_features))
#    print(im_contour_features)
    # print(shape(descriptors))
    # print(descriptors)
    for image_path, descriptor in des_list[1:]:
        descriptors = np.vstack((descriptors, descriptor))
    # print(shape(descriptors))
    # print(descriptors)
    k = 500
    voc, variance = kmeans(descriptors, k, 1)

    # Calculate the histogram of features
    im_features = np.zeros((len(genuine_image_features[i]) + len(forged_image_features[i]), k+12), "float32")
    for ii in range(len(genuine_image_features[i]) + len(forged_image_features[i])):
        words, distance = vq(des_list[ii][1], voc)
        for w in words:
            im_features[ii][w] += 1

        for j in range(12):
            im_features[ii][k+j] = im_contour_features[ii][j]

    #nbr_occurences = np.sum((im_features > 0) * 1, axis=0)
    #idf = np.array(np.log((1.0 * len(image_paths) + 1) / (1.0 * nbr_occurences + 1)), 'float32')

    # Scaling the words
    stdSlr = StandardScaler().fit(im_features)
    im_features = stdSlr.transform(im_features)

    train_genuine_features, test_genuine_features = im_features[0:3], im_features[3:5]

    train_forged_features, test_forged_features = im_features[5:8], im_features[8:10]

    #clf = linear_model.LogisticRegression(C=1e5)

    clf = LinearSVC()
    #clf = tree.DecisionTreeClassifier()
    #clf = tree.DecisionTreeRegressor()
    #clf = svm.SVC()
    clf.fit(np.concatenate((train_forged_features,train_genuine_features)), np.array([1 for x in range(len(train_forged_features))] + [2 for x in range(len(train_genuine_features))]))



    #print("2" + str(clf.predict(test_genuine_features)))
    genuine_res = clf.predict(test_genuine_features)

    for res in genuine_res:
        if int(res) == 2:
            cor += 1
        else:
            wrong += 1

    #print("1" + str(clf.predict(test_forged_features)))
    forged_res = clf.predict(test_forged_features)

    for res in forged_res:
        if int(res) == 1:
            cor += 1
        else:
            wrong += 1

print("Final Accuracy SVM: " + str(float(cor)/(cor+wrong)))